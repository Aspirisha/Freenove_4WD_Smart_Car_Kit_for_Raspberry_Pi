#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging

import numpy as np
import os
import time
import sys
from threading import Thread
from queue import Queue

from Command import COMMAND as cmd
from Client_Ui import Ui_Client
from commands import get_motor_command
from Video import VideoStreaming
from PyQt5.QtCore import QThread, QCoreApplication, Qt, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow

logger = logging.getLogger(__name__)


class ProgBar(QObject):
    sigPB = pyqtSignal(int)

    def send(self, text):
        self.sigPB.emit(text)


class SigStr(QObject):
    sigStr = pyqtSignal(str)

    def send(self, text):
        self.sigStr.emit(text)


class FrameGrabber(QObject):
    finished = pyqtSignal()
    frame_signal = pyqtSignal(float, np.ndarray)

    def __init__(self, ready_frames: Queue):
        super().__init__()

        self._ready_frames = ready_frames

    @pyqtSlot()
    def run(self):
        while True:
            stamp, frame = self._ready_frames.get()
            if stamp is None:
                break
            self.frame_signal.emit(stamp, frame)
        self.finished.emit()


class mywindow(QMainWindow, Ui_Client):
    def __init__(self):
        global timer
        super(mywindow, self).__init__()
        self.setupUi(self)
        self.endChar = "\n"
        self.intervalChar = "#"
        file = open("IP.txt", "r")
        self.IP.setText(str(file.readline()))
        file.close()
        self.h = self.IP.text()
        self.TCP = VideoStreaming()
        self.servo1 = 90
        self.servo2 = 90
        self._servo1_diff = 0
        self._servo2_diff = 0
        self.label_FineServo2.setText("0")
        self.label_FineServo1.setText("0")
        self.img = QImage()
        self.img.load("*.png")
        self.img.save("*.png")
        self.img.load("*.jpg")
        self.img.save("*.jpg")
        self.setWindowIcon(QIcon("image/logo_Mini.png"))
        self.label_Video.setPixmap(QPixmap("image/Raspberry_4WD_Car.png"))
        self.W_flag = 0
        self.m_DragPosition = self.pos()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        self._pressed_keys = set()
        self.Key_Q = False
        self.Key_E = False
        self.Key_Z = False
        self.Key_X = False
        self.Key_Space = False
        self.Rotate_Flag = 1
        self.setFocusPolicy(Qt.StrongFocus)
        self.progress_Power.setMinimum(0)
        self.progress_Power.setMaximum(100)

        self.name.setAlignment(Qt.AlignCenter)
        self.label_Servo1.setText("90")
        self.label_Servo2.setText("90")
        self.label_Video.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.label_Servo1.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.label_Servo2.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.label_FineServo1.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.label_FineServo2.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.HSlider_Servo1.setMinimum(0)
        self.HSlider_Servo1.setMaximum(180)
        self.HSlider_Servo1.setSingleStep(1)
        self.HSlider_Servo1.setValue(self.servo1)
        self.HSlider_Servo1.valueChanged.connect(self.Change_Left_Right)

        self.HSlider_FineServo1.setMinimum(-10)
        self.HSlider_FineServo1.setMaximum(10)
        self.HSlider_FineServo1.setSingleStep(1)
        self.HSlider_FineServo1.setValue(0)
        self.HSlider_FineServo1.valueChanged.connect(self.Fine_Tune_Left_Right)

        self.HSlider_FineServo2.setMinimum(-10)
        self.HSlider_FineServo2.setMaximum(10)
        self.HSlider_FineServo2.setSingleStep(1)
        self.HSlider_FineServo2.setValue(0)
        self.HSlider_FineServo2.valueChanged.connect(self.Fine_Tune_Up_Down)

        self.VSlider_Servo2.setMinimum(80)
        self.VSlider_Servo2.setMaximum(180)
        self.VSlider_Servo2.setSingleStep(1)
        self.VSlider_Servo2.setValue(self.servo2)
        self.VSlider_Servo2.valueChanged.connect(self.Change_Up_Down)

        self.checkBox_Led1.setChecked(False)
        self.checkBox_Led1.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led1)
        )
        self.checkBox_Led2.setChecked(False)
        self.checkBox_Led2.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led2)
        )
        self.checkBox_Led3.setChecked(False)
        self.checkBox_Led3.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led3)
        )
        self.checkBox_Led4.setChecked(False)
        self.checkBox_Led4.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led4)
        )
        self.checkBox_Led5.setChecked(False)
        self.checkBox_Led5.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led5)
        )
        self.checkBox_Led6.setChecked(False)
        self.checkBox_Led6.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led6)
        )
        self.checkBox_Led7.setChecked(False)
        self.checkBox_Led7.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led7)
        )
        self.checkBox_Led8.setChecked(False)
        self.checkBox_Led8.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led8)
        )

        self.checkBox_Led_Mode1.setChecked(False)
        self.checkBox_Led_Mode1.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led_Mode1)
        )
        self.checkBox_Led_Mode2.setChecked(False)
        self.checkBox_Led_Mode2.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led_Mode2)
        )
        self.checkBox_Led_Mode3.setChecked(False)
        self.checkBox_Led_Mode3.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led_Mode3)
        )
        self.checkBox_Led_Mode4.setChecked(False)
        self.checkBox_Led_Mode4.stateChanged.connect(
            lambda: self.LedChange(self.checkBox_Led_Mode4)
        )

        self.Btn_Mode1.setChecked(True)
        self.Btn_Mode1.toggled.connect(lambda: self.on_btn_Mode(self.Btn_Mode1))
        self.Btn_Mode2.setChecked(False)
        self.Btn_Mode2.toggled.connect(lambda: self.on_btn_Mode(self.Btn_Mode2))
        self.Btn_Mode3.setChecked(False)
        self.Btn_Mode3.toggled.connect(lambda: self.on_btn_Mode(self.Btn_Mode3))
        self.Btn_Mode4.setChecked(False)
        self.Btn_Mode4.toggled.connect(lambda: self.on_btn_Mode(self.Btn_Mode4))

        self.Ultrasonic.clicked.connect(self.on_btn_Ultrasonic)
        self.Light.clicked.connect(self.on_btn_Light)

        self.Btn_ForWard.pressed.connect(self.on_btn_ForWard)
        self.Btn_ForWard.released.connect(self.on_btn_Stop)

        self.Btn_Turn_Left.pressed.connect(self.on_btn_Turn_Left)
        self.Btn_Turn_Left.released.connect(self.on_btn_Stop)

        self.Btn_BackWard.pressed.connect(self.on_btn_BackWard)
        self.Btn_BackWard.released.connect(self.on_btn_Stop)

        self.Btn_Turn_Right.pressed.connect(self.on_btn_Turn_Right)
        self.Btn_Turn_Right.released.connect(self.on_btn_Stop)

        self.Btn_Up.clicked.connect(self.on_btn_Up)
        self.Btn_Left.clicked.connect(self.on_btn_Left)
        self.Btn_Down.clicked.connect(self.on_btn_Down)
        self.Btn_Home.clicked.connect(self.on_btn_Home)
        self.Btn_Right.clicked.connect(self.on_btn_Right)
        self.Btn_Tracking_Faces.clicked.connect(self.Tracking_Face)
        self.Btn_Buzzer.pressed.connect(self.on_btn_Buzzer)
        self.Btn_Buzzer.released.connect(self.on_btn_Buzzer)

        self.Btn_Connect.clicked.connect(self.on_btn_Connect)

        self.Window_Min.clicked.connect(self.windowMinimumed)
        self.Window_Close.clicked.connect(self.close)

        self.Pb = ProgBar()
        self.Pb.sigPB.connect(self.onPbChanged)

        self.U = SigStr()
        self.U.sigStr.connect(self.onUsonicChanged)

        self.L = SigStr()
        self.L.sigStr.connect(self.onLightChanged)

    def _init_video_receiver_thread(self):
        self.workerThread = QThread()
        self.workerObject = FrameGrabber(self.TCP.ready_frames)
        self.workerThread.started.connect(self.workerObject.run)
        self.workerObject.finished.connect(self.workerThread.quit)
        self.workerObject.finished.connect(self.workerObject.deleteLater)
        self.workerThread.finished.connect(self.workerThread.deleteLater)
        self.workerObject.frame_signal.connect(self.on_frame)

        self.workerObject.moveToThread(self.workerThread)
        self.workerThread.start()

    def _send_motor_command(self):
        command = get_motor_command(self._pressed_keys)
        logger.info(f"Sending motor command: {command.strip()}")
        self.TCP.sendData(cmd.CMD_MOTOR + command)

    def onPbChanged(self, value):
        self.progress_Power.setValue(value)

    def onUsonicChanged(self, value):
        self.Ultrasonic.setText(value)

    def onLightChanged(self, value):
        self.Light.setText(value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_drag = True
            self.m_DragPosition = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, QMouseEvent):
        if QMouseEvent.buttons() and Qt.LeftButton:
            self.move(QMouseEvent.globalPos() - self.m_DragPosition)
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_drag = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.on_btn_Up()
        elif event.key() == Qt.Key_Left:
            self.on_btn_Left()
        elif event.key() == Qt.Key_Down:
            self.on_btn_Down()
        elif event.key() == Qt.Key_Right:
            self.on_btn_Right()
        elif event.key() == Qt.Key_Home:
            self.on_btn_Home()

        if event.key() == Qt.Key_R:
            if self.Btn_Mode1.isChecked() is True:
                self.Btn_Mode2.setChecked(True)
            elif self.Btn_Mode2.isChecked() is True:
                self.Btn_Mode3.setChecked(True)
            elif self.Btn_Mode3.isChecked() is True:
                self.Btn_Mode4.setChecked(True)
            elif self.Btn_Mode4.isChecked() is True:
                self.Btn_Mode1.setChecked(True)

        if event.key() == Qt.Key_L:
            count = 0
            if self.checkBox_Led_Mode1.isChecked() is True:
                self.checkBox_Led_Mode2.setChecked(True)
            elif self.checkBox_Led_Mode2.isChecked() is True:
                self.checkBox_Led_Mode3.setChecked(True)
            elif self.checkBox_Led_Mode3.isChecked() is True:
                self.checkBox_Led_Mode4.setChecked(True)
            elif self.checkBox_Led_Mode4.isChecked() is True:
                self.checkBox_Led_Mode1.setChecked(True)

            for i in range(1, 5):
                checkBox_Led_Mode = getattr(self, "checkBox_Led_Mode%d" % i)
                if checkBox_Led_Mode.isChecked() is False:
                    count += 1
                else:
                    break
            if count == 4:
                self.checkBox_Led_Mode1.setChecked(True)

        if event.key() == Qt.Key_C:
            self.on_btn_Connect()
        if event.key() == Qt.Key_O:
            self.on_btn_rotate()

        if event.key() == Qt.Key_1:
            if self.checkBox_Led1.isChecked() is True:
                self.checkBox_Led1.setChecked(False)
            else:
                self.checkBox_Led1.setChecked(True)
        elif event.key() == Qt.Key_2:
            if self.checkBox_Led2.isChecked() is True:
                self.checkBox_Led2.setChecked(False)
            else:
                self.checkBox_Led2.setChecked(True)
        elif event.key() == Qt.Key_3:
            if self.checkBox_Led3.isChecked() is True:
                self.checkBox_Led3.setChecked(False)
            else:
                self.checkBox_Led3.setChecked(True)
        elif event.key() == Qt.Key_4:
            if self.checkBox_Led4.isChecked() is True:
                self.checkBox_Led4.setChecked(False)
            else:
                self.checkBox_Led4.setChecked(True)
        elif event.key() == Qt.Key_5:
            if self.checkBox_Led5.isChecked() is True:
                self.checkBox_Led5.setChecked(False)
            else:
                self.checkBox_Led5.setChecked(True)
        elif event.key() == Qt.Key_6:
            if self.checkBox_Led6.isChecked() is True:
                self.checkBox_Led6.setChecked(False)
            else:
                self.checkBox_Led6.setChecked(True)
        elif event.key() == Qt.Key_7:
            if self.checkBox_Led7.isChecked() is True:
                self.checkBox_Led7.setChecked(False)
            else:
                self.checkBox_Led7.setChecked(True)
        elif event.key() == Qt.Key_8:
            if self.checkBox_Led8.isChecked() is True:
                self.checkBox_Led8.setChecked(False)
            else:
                self.checkBox_Led8.setChecked(True)

        if event.isAutoRepeat():
            pass
        else:
            if event.key() == Qt.Key_W:
                self._pressed_keys.add("w")
                self._send_motor_command()
            elif event.key() == Qt.Key_S:
                self._pressed_keys.add("s")
                self._send_motor_command()
            elif event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_A:
                self.on_btn_Turn_Left()
                self._pressed_keys.add("a")
            elif event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_D:
                self.on_btn_Turn_Right()
                self._pressed_keys.add("d")
            elif event.key() == Qt.Key_A:
                self._pressed_keys.add("a")
                self._send_motor_command()
            elif event.key() == Qt.Key_D:
                self._pressed_keys.add("d")
                self._send_motor_command()

            elif event.key() == Qt.Key_Q:
                self.on_btn_Dialeft()
                self.Key_Q = True
            elif event.key() == Qt.Key_E:
                self.on_btn_Diaright()
                self.Key_E = True
            elif event.key() == Qt.Key_Z:
                self.on_btn_Diad_left()
                self.Key_Z = True
            elif event.key() == Qt.Key_X:
                self.on_btn_Diad_right()
                self.Key_X = True
            elif event.key() == Qt.Key_Space:
                self.on_btn_Buzzer()
                self.Key_Space = True

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_W:
            time.sleep(0.05)
            if event.key() == Qt.Key_W:
                if not (event.isAutoRepeat()) and "w" in self._pressed_keys:
                    self._pressed_keys.remove("w")
                    self._send_motor_command()
        elif event.key() == Qt.Key_A:
            if not (event.isAutoRepeat()) and "a" in self._pressed_keys:
                self._pressed_keys.remove("a")
                self._send_motor_command()
        elif event.key() == Qt.Key_S:
            if not (event.isAutoRepeat()) and "s" in self._pressed_keys:
                self._pressed_keys.remove("s")
                self._send_motor_command()
        elif event.key() == Qt.Key_D:
            if not (event.isAutoRepeat()) and "d" in self._pressed_keys:
                self._pressed_keys.remove("d")
                self._send_motor_command()
        elif event.key() == Qt.Key_Q:
            if not (event.isAutoRepeat()) and self.Key_Q is True:
                self.on_btn_Stop()
                self.Key_Q = False
        elif event.key() == Qt.Key_E:
            if not (event.isAutoRepeat()) and self.Key_E is True:
                self.on_btn_Stop()
                self.Key_E = False
        elif event.key() == Qt.Key_Z:
            if not (event.isAutoRepeat()) and self.Key_Z is True:
                self.on_btn_Stop()
                self.Key_Z = False
        elif event.key() == Qt.Key_X:
            if not (event.isAutoRepeat()) and self.Key_X is True:
                self.on_btn_Stop()
                self.Key_X = False

        if event.key() == Qt.Key_Space:
            if not (event.isAutoRepeat()) and self.Key_Space is True:
                self.on_btn_Buzzer()
                self.Key_Space = False

    def on_btn_ForWard(self):
        print("forward")

    def on_btn_Turn_Left(self):
        Turn_Left = (
            self.intervalChar
            + str(-1500)
            + self.intervalChar
            + str(-1500)
            + self.intervalChar
            + str(1500)
            + self.intervalChar
            + str(1500)
            + self.endChar
        )
        self.TCP.sendData(cmd.CMD_MOTOR + Turn_Left)

    def on_btn_BackWard(self):
        BackWard = (
            self.intervalChar
            + str(-1500)
            + self.intervalChar
            + str(-1500)
            + self.intervalChar
            + str(-1500)
            + self.intervalChar
            + str(-1500)
            + self.endChar
        )
        self.TCP.sendData(cmd.CMD_MOTOR + BackWard)

    def on_btn_Turn_Right(self):
        Turn_Right = (
            self.intervalChar
            + str(1500)
            + self.intervalChar
            + str(1500)
            + self.intervalChar
            + str(-1500)
            + self.intervalChar
            + str(-1500)
            + self.endChar
        )
        self.TCP.sendData(cmd.CMD_MOTOR + Turn_Right)

    def on_btn_Stop(self):
        Stop = (
            self.intervalChar
            + str(0)
            + self.intervalChar
            + str(0)
            + self.intervalChar
            + str(0)
            + self.intervalChar
            + str(0)
            + self.endChar
        )
        self.TCP.sendData(cmd.CMD_MOTOR + Stop)

    def on_btn_rotate(self):
        if self.Rotate_Flag:
            self.Btn_Rotate.setText("Rotate-Off")
            self.Rotate_Flag = 0
        else:
            self.Btn_Rotate.setText("Rotate-On")
            self.Rotate_Flag = 1

    def on_btn_Up(self):
        prev_servo = self.servo2
        self.servo2 = self.servo2 + 10
        if self.servo2 >= 180:
            self.servo2 = 180
        self._servo2_diff = self.servo2 - prev_servo
        self.VSlider_Servo2.setValue(self.servo2)

    def on_btn_Down(self):
        prev_servo = self.servo2
        self.servo2 = self.servo2 - 10
        if self.servo2 <= 80:
            self.servo2 = 80
        self._servo2_diff = self.servo2 - prev_servo
        self.VSlider_Servo2.setValue(self.servo2)

    def on_btn_Left(self):
        prev_servo = self.servo1
        self.servo1 = self.servo1 - 10
        if self.servo1 <= 0:
            self.servo1 = 0
        self._servo1_diff = self.servo1 - prev_servo
        self.HSlider_Servo1.setValue(self.servo1)

    def on_btn_Right(self):
        prev_servo = self.servo1
        self.servo1 = self.servo1 + 10
        if self.servo1 >= 180:
            self.servo1 = 180
        self._servo1_diff = self.servo1 - prev_servo
        self.HSlider_Servo1.setValue(self.servo1)

    def on_btn_Home(self):
        self.servo1 = 90
        self.servo2 = 90
        self.HSlider_Servo1.setValue(self.servo1)
        self.VSlider_Servo2.setValue(self.servo2)

    def on_btn_Buzzer(self):
        if self.Btn_Buzzer.text() == "Buzzer":
            self.TCP.sendData(cmd.CMD_BUZZER + self.intervalChar + "1" + self.endChar)
            self.Btn_Buzzer.setText("Noise")
        else:
            self.TCP.sendData(cmd.CMD_BUZZER + self.intervalChar + "0" + self.endChar)
            self.Btn_Buzzer.setText("Buzzer")

    def on_btn_Ultrasonic(self):
        if self.Ultrasonic.text() == "Ultrasonic":
            self.TCP.sendData(cmd.CMD_SONIC + self.intervalChar + "1" + self.endChar)
        else:
            self.TCP.sendData(cmd.CMD_SONIC + self.intervalChar + "0" + self.endChar)
            self.Ultrasonic.setText("Ultrasonic")

    def on_btn_Light(self):
        if self.Light.text() == "Light":
            self.TCP.sendData(cmd.CMD_LIGHT + self.intervalChar + "1" + self.endChar)
        else:
            self.TCP.sendData(cmd.CMD_LIGHT + self.intervalChar + "0" + self.endChar)
            self.Light.setText("Light")

    def Change_Left_Right(self):  # Left or Right
        self.TCP.sendData(
            cmd.CMD_SERVO
            + self.intervalChar
            + "0"
            + self.intervalChar
            + str(self._servo1_diff)
            + self.endChar
        )
        self.label_Servo1.setText("%d" % self.servo1)

    def Change_Up_Down(self):  # Up or Down
        self.TCP.sendData(
            cmd.CMD_SERVO
            + self.intervalChar
            + "1"
            + self.intervalChar
            + str(self._servo2_diff)
            + self.endChar
        )
        self.label_Servo2.setText("%d" % self.servo2)

    def Fine_Tune_Left_Right(self):  # fine tune Left or Right
        self.label_FineServo1.setText(str(self.HSlider_FineServo1.value()))
        data = self.servo1 + self.HSlider_FineServo1.value()
        self.TCP.sendData(
            cmd.CMD_SERVO
            + self.intervalChar
            + "0"
            + self.intervalChar
            + str(data)
            + self.endChar
        )

    def Fine_Tune_Up_Down(self):  # fine tune Up or Down
        self.label_FineServo2.setText(str(self.HSlider_FineServo2.value()))
        data = self.servo2 + self.HSlider_FineServo2.value()
        self.TCP.sendData(
            cmd.CMD_SERVO
            + self.intervalChar
            + "1"
            + self.intervalChar
            + str(data)
            + self.endChar
        )

    def windowMinimumed(self):
        self.showMinimized()

    def LedChange(self, b):
        R = self.Color_R.text()
        G = self.Color_G.text()
        B = self.Color_B.text()
        led_Off = (
            self.intervalChar
            + str(0)
            + self.intervalChar
            + str(0)
            + self.intervalChar
            + str(0)
            + self.endChar
        )
        color = (
            self.intervalChar
            + str(R)
            + self.intervalChar
            + str(G)
            + self.intervalChar
            + str(B)
            + self.endChar
        )
        if b.text() == "Led1":
            self.led_Index = str(0x01)
            if b.isChecked() is True:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + color
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + led_Off
                )
        if b.text() == "Led2":
            self.led_Index = str(0x02)
            if b.isChecked() is True:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + color
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + led_Off
                )
        if b.text() == "Led3":
            self.led_Index = str(0x04)
            if b.isChecked() is True:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + color
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + led_Off
                )
        if b.text() == "Led4":
            self.led_Index = str(0x08)
            if b.isChecked() is True:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + color
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + led_Off
                )
        if b.text() == "Led5":
            self.led_Index = str(0x10)
            if b.isChecked() is True:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + color
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + led_Off
                )
        if b.text() == "Led6":
            self.led_Index = str(0x20)
            if b.isChecked() is True:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + color
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + led_Off
                )
        if b.text() == "Led7":
            self.led_Index = str(0x40)
            if b.isChecked() is True:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + color
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + led_Off
                )
        if b.text() == "Led8":
            self.led_Index = str(0x80)
            if b.isChecked() is True:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + color
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED + self.intervalChar + self.led_Index + led_Off
                )
        if b.text() == "Led_Mode1":
            if b.isChecked() is True:
                self.checkBox_Led_Mode2.setChecked(False)
                self.checkBox_Led_Mode3.setChecked(False)
                self.checkBox_Led_Mode4.setChecked(False)
                self.TCP.sendData(
                    cmd.CMD_LED_MOD + self.intervalChar + "1" + self.endChar
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED_MOD + self.intervalChar + "0" + self.endChar
                )
        if b.text() == "Led_Mode2":
            if b.isChecked() is True:

                self.checkBox_Led_Mode1.setChecked(False)
                self.checkBox_Led_Mode3.setChecked(False)
                self.checkBox_Led_Mode4.setChecked(False)
                self.TCP.sendData(
                    cmd.CMD_LED_MOD + self.intervalChar + "2" + self.endChar
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED_MOD + self.intervalChar + "0" + self.endChar
                )
        if b.text() == "Led_Mode3":
            if b.isChecked() is True:
                self.checkBox_Led_Mode2.setChecked(False)
                self.checkBox_Led_Mode1.setChecked(False)
                self.checkBox_Led_Mode4.setChecked(False)
                self.TCP.sendData(
                    cmd.CMD_LED_MOD + self.intervalChar + "3" + self.endChar
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED_MOD + self.intervalChar + "0" + self.endChar
                )
        if b.text() == "Led_Mode4":
            if b.isChecked() is True:
                self.checkBox_Led_Mode2.setChecked(False)
                self.checkBox_Led_Mode3.setChecked(False)
                self.checkBox_Led_Mode1.setChecked(False)
                self.TCP.sendData(
                    cmd.CMD_LED_MOD + self.intervalChar + "4" + self.endChar
                )
            else:
                self.TCP.sendData(
                    cmd.CMD_LED_MOD + self.intervalChar + "0" + self.endChar
                )

    def on_btn_Mode(self, Mode):
        if Mode.text() == "M-Free":
            if Mode.isChecked() is True:
                # self.timer.start(34)
                self.TCP.sendData(
                    cmd.CMD_MODE + self.intervalChar + "one" + self.endChar
                )
        if Mode.text() == "M-Light":
            if Mode.isChecked() is True:
                # self.timer.stop()
                self.TCP.sendData(
                    cmd.CMD_MODE + self.intervalChar + "two" + self.endChar
                )
        if Mode.text() == "M-Sonic":
            if Mode.isChecked() is True:
                # self.timer.stop()
                self.TCP.sendData(
                    cmd.CMD_MODE + self.intervalChar + "three" + self.endChar
                )
        if Mode.text() == "M-Line":
            if Mode.isChecked() is True:
                # self.timer.stop()
                self.TCP.sendData(
                    cmd.CMD_MODE + self.intervalChar + "four" + self.endChar
                )

    def on_btn_Connect(self):
        if self.Btn_Connect.text() == "Connect":
            self.h = self.IP.text()
            self.TCP.StartTcpClient(
                self.h,
            )
            file = open("IP.txt", "w")
            file.write(self.IP.text())
            file.close()
            try:
                self.streaming = Thread(target=self.TCP.streaming, args=(self.h,))
                self.streaming.start()
            except:
                print("video error")
            try:
                self.recv = Thread(target=self.recvmassage)
                self.recv.start()
            except:
                print("recv error")
            self._init_video_receiver_thread()
            self.Btn_Connect.setText("Disconnect")
            print("Server address:" + str(self.h) + "\n")
        elif self.Btn_Connect.text() == "Disconnect":
            self.Btn_Connect.setText("Connect")
            self.TCP.StopTcpcClient()
            self.recv.join()
            self.power.join()
            self.streaming.join()
            self.label_Video.setPixmap(QPixmap("image/Raspberry_4WD_Car.png"))

    def close(self):
        self.TCP.StopTcpcClient()
        self.recv.join()
        self.power.join()
        self.streaming.join()
        QCoreApplication.instance().quit()
        sys.exit(0)

    def Power(self):
        while not self.TCP._stop_event.wait(1):
            try:
                self.TCP.sendData(cmd.CMD_POWER + self.endChar)
            except:
                break

    def recvmassage(self):
        self.TCP.socket1_connect(self.h)
        self.power = Thread(target=self.Power)
        self.power.start()
        restCmd = ""

        while not self.TCP._stop_event.is_set():
            Alldata = restCmd + str(self.TCP.recvData())
            restCmd = ""
            print(Alldata)
            if Alldata == "":
                break
            else:
                cmdArray = Alldata.split("\n")
                if cmdArray[-1] != "":
                    restCmd = cmdArray[-1]
                    cmdArray = cmdArray[:-1]
            for oneCmd in cmdArray:
                Massage = oneCmd.split("#")
                if cmd.CMD_SONIC in Massage:
                    # self.Ultrasonic.setText('Obstruction:%s cm' % Massage[1])
                    u = "Obstruction:%s cm" % Massage[1]
                    self.U.send(u)
                elif cmd.CMD_LIGHT in Massage:
                    # self.Light.setText("Left:" + Massage[1] + 'V' + ' ' + "Right:" + Massage[2] + 'V')
                    l = "Left:" + Massage[1] + "V" + " " + "Right:" + Massage[2] + "V"
                    self.L.send(l)
                elif cmd.CMD_POWER in Massage:
                    MAX_VOLATGE = 8.4
                    percent_power = int(float(Massage[1]) / MAX_VOLATGE * 100)
                    # self.progress_Power.setValue(percent_power)
                    self.Pb.send(percent_power)

    def Tracking_Face(self):
        if self.Btn_Tracking_Faces.text() == "Tracing-On":
            self.Btn_Tracking_Faces.setText("Tracing-Off")
        else:
            self.Btn_Tracking_Faces.setText("Tracing-On")

    def find_Face(self, face_x, face_y):
        if face_x != 0 and face_y != 0:
            offset_x = float(face_x / 400 - 0.5) * 2
            offset_y = float(face_y / 300 - 0.5) * 2
            delta_degree_x = int(4 * offset_x)
            delta_degree_y = int(-4 * offset_y)
            self.servo1 = self.servo1 + delta_degree_x
            self.servo2 = self.servo2 + delta_degree_y
            if (
                offset_x > -0.15
                and offset_y > -0.15
                and offset_x < 0.15
                and offset_y < 0.15
            ):
                pass
            else:
                self.HSlider_Servo1.setValue(self.servo1)
                self.VSlider_Servo2.setValue(self.servo2)

    @pyqtSlot(float, np.ndarray)
    def on_frame(self, stamp, frame):
        assert frame is not None
        height, width, channel = frame.shape
        bytesPerLine = channel * width
        qImg = QImage(
            frame.data, width, height, bytesPerLine, QImage.Format_RGB888
        ).rgbSwapped()
        # now = time.monotonic()
        # print('delay:', now - stamp)
        self.label_Video.setPixmap(QPixmap(qImg))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%d/%b/%Y %H:%M:%S",
        stream=sys.stdout,
    )

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myshow = mywindow()
    myshow.show()
    sys.exit(app.exec_())
