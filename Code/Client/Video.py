#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import cv2
import socket
import logging
import io
import sys
import struct
import time
import threading
import traceback
from PIL import Image
from multiprocessing import Process, Queue
from Command import COMMAND as cmd

logger = logging.getLogger(__name__)


class ImageProcessor:
    def __init__(self, raw_image_queue: Queue, ready_frames_queue: Queue):
        self._face_cascade = None
        self.face_x = 0
        self.face_y = 0
        self._raw_image_queue = raw_image_queue
        self._ready_frames_queue = ready_frames_queue
        self.prev_gray = None
        self.prev_pts = None
        self.last_transforms = []

    def run(self):
        self._face_cascade = cv2.CascadeClassifier(
            r"haarcascade_frontalface_default.xml"
        )
        stamp = 0
        while True:
            stamp, jpg = self._raw_image_queue.get()
            if stamp is None:
                break
            if not self.IsValidImage4Bytes(jpg):
                print("Got invalid image")
                continue
            image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            # image = self.stabilize(image)
            self._ready_frames_queue.put((stamp, image))

    def IsValidImage4Bytes(self, buf):
        bValid = True
        if buf[6:10] in (b"JFIF", b"Exif"):
            if not buf.rstrip(b"\0\r\n").endswith(b"\xff\xd9"):
                bValid = False
        else:
            try:
                Image.open(io.BytesIO(buf)).verify()
            except:
                bValid = False
        return bValid

        # self.face_detect(image)

    def face_detect(self, img):
        if (
            sys.platform.startswith("win")
            or sys.platform.startswith("darwin")
            or sys.platform.startswith("linux")
        ):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                for x, y, w, h in faces:
                    self.face_x = float(x + w / 2.0)
                    self.face_y = float(y + h / 2.0)
                    img = cv2.circle(
                        img,
                        (int(self.face_x), int(self.face_y)),
                        int((w + h) / 4),
                        (0, 255, 0),
                        2,
                    )
            else:
                self.face_x = 0
                self.face_y = 0

    def stabilize(self, frame):
        curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.prev_gray is None:
            self.reset_stabilizer(curr_gray)
            return frame

        curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(
            self.prev_gray, curr_gray, self.prev_pts, None
        )
        valid_prev_pts = self.prev_pts[status == 1]
        valid_curr_pts = curr_pts[status == 1]
        if len(valid_curr_pts) < 2:
            print("Too little valid points")
            self.reset_stabilizer(curr_gray)
            return frame
        matrix, inliers = cv2.estimateAffinePartial2D(valid_prev_pts, valid_curr_pts)
        if matrix is None:
            self.reset_stabilizer(curr_gray)
            return frame

        # print('inliers: ', inliers)
        dx = matrix[0, 2]
        dy = matrix[1, 2]
        da = np.arctan2(matrix[1, 0], matrix[0, 0])
        # print('stabilizing', dx, dy, da)
        transform = np.array([dx, dy, da], np.float32)
        self.last_transforms.append(transform)
        if len(self.last_transforms) > 50:
            self.last_transforms = self.last_transforms[1:]
        smoothed_transform = np.sum(self.last_transforms, axis=0) / len(
            self.last_transforms
        )

        self.prev_gray = curr_gray.copy()
        self.prev_pts = valid_curr_pts.reshape(-1, 1, 2)

        dx, dy, da = smoothed_transform
        # print('stabilized', dx, dy, da)

        # Create transformation matrix
        transform_matrix = np.array(
            [[np.cos(da), -np.sin(da), dx], [np.sin(da), np.cos(da), dy]]
        )
        frame_height, frame_width = frame.shape[:2]
        stabilized_frame = cv2.warpAffine(
            frame, transform_matrix, (frame_width, frame_height)
        )
        return stabilized_frame

    def reset_stabilizer(self, curr_gray):
        self.prev_gray = curr_gray
        self.prev_pts = cv2.goodFeaturesToTrack(
            self.prev_gray,
            maxCorners=200,
            qualityLevel=0.01,
            minDistance=30,
            blockSize=3,
        )


class VideoStreaming:
    def __init__(self):
        self.connect_Flag = False
        self._raw_image_queue = Queue()
        self._ready_frames_queue = Queue()
        self._image_processor = None
        self._stop_event = threading.Event()

    @property
    def ready_frames(self) -> Queue:
        return self._ready_frames_queue

    def StartTcpClient(self, IP):
        print("Starting TCP video receiving...")
        self._stop_event.clear()
        self.client_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        image_processor = ImageProcessor(
            self._raw_image_queue, self._ready_frames_queue
        )
        self._image_processor = Process(target=image_processor.run)
        self._image_processor.start()

    def StopTcpcClient(self):
        try:
            logger.info("Stopping TCP client...")
            self._stop_event.set()
            self.connect_Flag = False
            self.client_socket1.shutdown(socket.SHUT_RDWR)
            self.client_socket1.close()
            self._raw_image_queue.put((None, None))  # means stop
            self._ready_frames_queue.put((None, None))  # means stop
            self._image_processor.join()
        except:
            pass

    def streaming(self, ip):
        stream_bytes = b" "
        try:
            self.client_socket.connect((ip, 8000))
            self.connection = self.client_socket.makefile("rb")
        except Exception as e:
            print("Failed to create connection:", str(e))
            pass
        try:
            while not self._stop_event.is_set():
                stream_bytes = self.connection.read(4)
                leng = struct.unpack("<L", stream_bytes[:4])[0]
                payload = bytearray(leng)
                read = self.connection.readinto(payload)
                while read < leng:
                    read += self.connection.readinto(payload[read:])
                now = time.monotonic()
                self._raw_image_queue.put((now, payload))
        except Exception as e:
            logger.error("Failed to receive image: %s", str(e))
            logger.error(traceback.format_exc())
        finally:
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()

    def sendData(self, s):
        if self._stop_event.is_set():
            logger.info("Connection to server stopped")
            return

        if self.connect_Flag:
            logger.info("Sending data %s to server", s)
            self.client_socket1.send(s.encode("utf-8"))
        else:
            logger.info("Not connected to server to send data")

    def recvData(self):
        data = ""
        try:
            data = self.client_socket1.recv(1024).decode("utf-8")
        except:
            pass
        return data

    def socket1_connect(self, ip):
        try:
            self.client_socket1.connect((ip, 5000))
            self.connect_Flag = True
            print("Connection Successful !")
        except Exception as e:
            print("Connect to server Failed!: Server IP is right? Server is opened?")
            self.connect_Flag = False


if __name__ == "__main__":
    pass
