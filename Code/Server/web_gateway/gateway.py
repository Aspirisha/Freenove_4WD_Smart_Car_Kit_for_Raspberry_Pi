# video_gateway.py
import asyncio
import json
import logging
from pathlib import Path
import struct
import os
import sys

from aiohttp import web, WSMsgType

from async_server import DEFAULT_VIDEO_PORT, DEFAULT_COMMAND_PORT

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from Client.commands import get_motor_command
from Command import COMMAND as cmd


FREENOVE_HOST = "127.0.0.1"
BOUNDARY = "frame"
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

INTERVAL_CHAR = "#"
END_CHAR = "\n"

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s:%(name)s:%(levelname)s - %(message)s", level=logging.INFO
)


class CarConnection:
    def __init__(self):
        self.writer = None
        self.connected = asyncio.Event()
        self._pressed_keys = set()

    async def connect(self):
        while True:
            try:
                logger.info(
                    f"Connecting to car at {FREENOVE_HOST}:{DEFAULT_COMMAND_PORT}..."
                )
                reader, writer = await asyncio.open_connection(
                    FREENOVE_HOST, DEFAULT_COMMAND_PORT
                )
                self.writer = writer
                self.connected.set()
                logger.info("Connected to car!")
                await reader.read()  # wait until disconnect
            except Exception as e:
                logger.error("Car connection failed: %s", e)
                self.connected.clear()
                await asyncio.sleep(3)

    async def send_cmd(self, cmd: str):
        await self.connected.wait()
        msg = (cmd).encode()
        self.writer.write(msg)
        await self.writer.drain()


car = CarConnection()


async def mjpeg_handler(request):
    response = web.StreamResponse(
        status=200,
        reason="OK",
        headers={"Content-Type": f"multipart/x-mixed-replace; boundary={BOUNDARY}"},
    )
    await response.prepare(request)

    reader, writer = await asyncio.open_connection(FREENOVE_HOST, DEFAULT_VIDEO_PORT)

    try:
        while True:
            # Read frame length (4 bytes, little-endian)
            len_bytes = await reader.readexactly(4)
            frame_len = struct.unpack("<L", len_bytes)[0]

            # Read frame data
            frame_data = await reader.readexactly(frame_len)

            # Write MJPEG chunk
            await response.write(
                (
                    f"--{BOUNDARY}\r\n"
                    "Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(frame_data)}\r\n\r\n"
                ).encode("utf-8")
                + frame_data
                + b"\r\n"
            )
            await response.drain()

    except asyncio.IncompleteReadError:
        logger.info("Video stream ended.")
    finally:
        writer.close()
        await writer.wait_closed()
        await response.write_eof()

    return response


def get_camera_command(data: str) -> str:
    if data in ("cam_up", "cam_down"):
        servo = 1
    elif data in ("cam_left", "cam_right"):
        servo = 0
    else:
        logger.error("Unknown camera command: %s", data)
        return ""
    if data in ("cam_up", "cam_right"):
        angle_shift = +5
    else:
        angle_shift = -5
    return (
        f"{cmd.CMD_SERVO}{INTERVAL_CHAR}{servo}{INTERVAL_CHAR}{angle_shift}{END_CHAR}"
    )


async def handle_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async def to_car():
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                logger.warning("Got non-text message %r", msg)
                continue
            logger.info("Handling key event")
            data = msg.json()
            event = data.get("event")
            key = data.get("key")
            logger.info("Got %s key event %s", event, key)
            if event == "down":
                car._pressed_keys.add(key)
                await handle_key_down(key)
            elif event == "up":
                car._pressed_keys.discard(key)
                await handle_key_up(key)
            else:
                logger.warning("Unknown event type: %s", event)

    await asyncio.gather(to_car())
    return ws


async def handle_key_down(key):
    command_str = ""
    if key == "ArrowUp":
        command_str = get_camera_command("cam_up")
    elif key == "ArrowDown":
        command_str = get_camera_command("cam_down")
    elif key == "ArrowLeft":
        command_str = get_camera_command("cam_left")
    elif key == "ArrowRight":
        command_str = get_camera_command("cam_right")
    elif key in ("w", "a", "s", "d"):
        command_str = get_motor_command(car._pressed_keys)
    if command_str:
        await car.send_cmd(command_str)


async def handle_key_up(key):
    command_str = ""
    if key in ("w", "a", "s", "d"):
        command_str = get_motor_command(car._pressed_keys)
    if command_str:
        await car.send_cmd(command_str)


async def index(request):
    return web.FileResponse(STATIC_DIR / "index.html")


async def start_background_tasks(app):
    app["car_task"] = asyncio.create_task(car.connect())


async def cleanup_background_tasks(app):
    app["car_task"].cancel()
    await app["car_task"]


def main():
    app = web.Application()
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    app.router.add_get("/video.mjpg", mjpeg_handler)
    app.router.add_get("/ws", handle_ws)
    app.router.add_get("/", index)
    app.router.add_static(
        "/",
        path=STATIC_DIR,
        name="static",
    )
    web.run_app(app, port=8080)


if __name__ == "__main__":
    main()
