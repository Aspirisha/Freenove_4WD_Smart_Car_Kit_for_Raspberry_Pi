import asyncio
from functools import partial
import logging
import io
import struct
import sys

from typing import List

import cv2

from gpiozero import Buzzer
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from picamera2.encoders import Quality

from ADC import Adc
from Command import COMMAND as cmd
from Motor import Motor
from servo import Servo


logger = logging.getLogger(__name__)

DEFAULT_VIDEO_PORT = 8000
DEFAULT_COMMAND_PORT = 5000


class CarModel:
    BATTERY_VOLTAGE_DIVIDER = 3
    BUZZER_PIN = 17

    def __init__(self):
        self.adc = Adc()
        self.servo = Servo()
        self.buzzer = Buzzer(pin=self.BUZZER_PIN)
        self.PWM = Motor()
        self.cam_angles = {"x": 90, "y": 90}

    def process_servo_command(self, data: List):
        logger.info("Processing servo command")
        try:
            servo_channel = data[1]
            angle = int(data[2])
            if servo_channel is None or angle is None:
                return
            if servo_channel == "0":
                self.cam_angles["x"] = max(0, min(180, self.cam_angles["x"] + angle))
                angle = self.cam_angles["x"]
            elif servo_channel == "1":
                self.cam_angles["y"] = max(80, min(180, self.cam_angles["y"] + angle))
                angle = self.cam_angles["y"]
            logger.info("Setting servo %s to angle %d", servo_channel, angle)
            self.servo.setServoPwm(servo_channel, angle)
        except:
            pass

    def process_motor_command(self, data: List):
        logger.info("Processing motor command")
        try:
            data1 = int(data[1])
            data2 = int(data[2])
            data3 = int(data[3])
            data4 = int(data[4])
            if data1 == None or data2 == None or data2 == None or data3 == None:
                return
            self.PWM.setMotorModel(data1, data2, data3, data4)
        except:
            pass

    def get_power(self) -> float:
        return self.adc.recvADC(2) * self.BATTERY_VOLTAGE_DIVIDER


async def frame_producer(queue: asyncio.Queue, picam2: Picamera2):
    def new_frame(request):
        frame = request.make_array("main")
        try:
            queue.put_nowait(frame)
        except asyncio.QueueFull:
            logger.info("Dropping stale frames")
            pass  # drop old frame if backlog

    picam2.post_callback = new_frame
    picam2.start()

    while True:
        await asyncio.sleep(1)


class AsyncStreamingOutput(io.BufferedIOBase):
    def __init__(self, loop: asyncio.EventLoop = None):
        self.frame = None
        self.condition = asyncio.Condition()
        self._loop = loop or asyncio.get_event_loop()

    def write(self, buf):
        # Called by Picamera2 in sync context
        # Use asyncio thread-safe call to wake waiting coroutines
        self.frame = buf
        self._loop.call_soon_threadsafe(self._notify)

    def _notify(self):
        # Wakes up one or more coroutines waiting on the condition
        async def notify():
            async with self.condition:
                self.condition.notify_all()

        asyncio.create_task(notify())


class VideoStreamer:
    def __init__(self, frames_producer: AsyncStreamingOutput):
        self._client_connected = False
        self._frames_producer = frames_producer

    async def stream(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        logger.info("Started handling client video stream")
        if self._client_connected:
            writer.write(struct.pack("<L", 0))
            await writer.drain()
            return
        self._client_connected = True
        while True:
            async with self._frames_producer.condition:
                await self._frames_producer.condition.wait()
                frame = self._frames_producer.frame
            try:
                writer.write(struct.pack("<L", len(frame)) + frame)
                await writer.drain()
            except (
                ConnectionResetError,
                ConnectionResetError,
                BrokenPipeError,
                asyncio.CancelledError,
            ):
                self._client_connected = False
                break


async def video_streamer(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, queue: asyncio.Queue
):
    peer = writer.get_extra_info("peername")
    logger.info("[Video] Connection from %s", peer)
    try:
        while True:
            frame = await queue.get()

            # JPEG encode
            ret, jpeg = cv2.imencode(".jpg", frame)
            data = jpeg.tobytes()

            # send: [4-byte length][JPEG data]
            writer.write(struct.pack("<L", len(data)) + data)
            await writer.drain()

            queue.task_done()
    except (asyncio.IncompleteReadError, ConnectionResetError):
        logger.error("[Video] Disconnected: %s", peer)
    finally:
        writer.close()
        await writer.wait_closed()


async def power_checker(car_model: CarModel):
    try:
        while True:
            await asyncio.sleep(10)
            adc_power = car_model.get_power()
            if adc_power < 6.5:
                logger.info("Very low power detected: %s", adc_power)
                for _ in range(4):
                    car_model.buzzer.on()
                    await asyncio.sleep(0.1)
                    car_model.buzzer.off()
                    await asyncio.sleep(0.1)
            elif adc_power < 7:
                logger.info("Low power detected: %s", adc_power)
                for _ in range(2):
                    car_model.buzzer.on()
                    await asyncio.sleep(0.1)
                    car_model.buzzer.off()
                    await asyncio.sleep(0.1)
            else:
                car_model.buzzer.off()
    except (ConnectionResetError, asyncio.CancelledError):
        logger.error("[Power Checker] canceled")


async def command_handler(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, car_model: CarModel
):
    peer = writer.get_extra_info("peername")
    logger.info("[Cmd] Connection from %s", peer)
    power_checker_task = asyncio.create_task(power_checker(car_model))
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            command_data = line.decode().strip()
            logger.info("Received command(s) from client: %s", command_data)
            if len(command_data) < 5:
                continue
            commands = command_data.split("\n")
            logger.info("Split into %d command(s): %r", len(commands), commands)

            for command in commands:
                data = command.split("#")
                logger.info("Processing command: %r", data)
                if cmd.CMD_SERVO in data:
                    car_model.process_servo_command(data)
                elif cmd.CMD_MOTOR in data:
                    car_model.process_motor_command(data)
                elif cmd.CMD_POWER in data:
                    logger.info("Processing power command: %r", data)
                    power = car_model.get_power()
                    msg = f"{cmd.CMD_POWER}#{round(power, 2)}\n"
                    writer.write(msg.encode())
                    await writer.drain()

    except (asyncio.IncompleteReadError, ConnectionResetError):
        logger.error("[Cmd] Disconnected: %s", peer)
    finally:
        writer.close()
        power_checker_task.cancel()
        await writer.wait_closed()


async def create_video_server(use_video_config: bool):
    picam2 = Picamera2()

    if not use_video_config:
        config = picam2.create_preview_configuration(main={"size": (400, 300)})
        picam2.configure(config)
        queue = asyncio.Queue(maxsize=2)
        asyncio.create_task(frame_producer(queue, picam2))
        video_server = await asyncio.start_server(
            lambda r, w: video_streamer(r, w, queue), "0.0.0.0", DEFAULT_VIDEO_PORT
        )
    else:
        picam2.configure(picam2.create_video_configuration(main={"size": (400, 300)}))
        output = AsyncStreamingOutput()
        encoder = JpegEncoder(q=90)
        streamer = VideoStreamer(output)
        picam2.start_recording(encoder, FileOutput(output), quality=Quality.VERY_HIGH)
        video_server = await asyncio.start_server(
            streamer.stream,
            "0.0.0.0",
            DEFAULT_VIDEO_PORT,
        )
    return video_server


async def main():
    video_server = await create_video_server(use_video_config=True)
    car_model = CarModel()

    cmd_server = await asyncio.start_server(
        partial(command_handler, car_model=car_model), "0.0.0.0", DEFAULT_COMMAND_PORT
    )

    logger.info(
        "Servers running on ports %d (video), %d (commands)",
        DEFAULT_VIDEO_PORT,
        DEFAULT_COMMAND_PORT,
    )
    await asyncio.gather(
        video_server.serve_forever(),
        cmd_server.serve_forever(),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%d/%b/%Y %H:%M:%S",
        stream=sys.stdout,
    )
    asyncio.run(main())
