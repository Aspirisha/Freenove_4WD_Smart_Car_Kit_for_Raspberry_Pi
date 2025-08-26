import io
import os
import logging
import socket
import struct
import time
import picamera2
import sys, getopt
from Thread import *
from threading import Thread
from server import Server

logger = logging.getLogger(__name__)


class mywindow:

    def __init__(self):
        self.user_ui = False
        self.start_tcp = True
        self.TCP_Server = Server()
        self.TCP_Server.StartTcpServer()
        self.ReadData = Thread(target=self.TCP_Server.readdata)
        self.SendVideo = Thread(target=self.TCP_Server.sendvideo)
        self.power = Thread(target=self.TCP_Server.Power)
        self.SendVideo.start()
        self.ReadData.start()
        self.power.start()
        if self.user_ui:
            self.label.setText("Server On")
            self.Button_Server.setText("Off")

    def close(self):
        try:
            stop_thread(self.SendVideo)
            stop_thread(self.ReadData)
            stop_thread(self.power)
        except:
            pass
        try:
            self.TCP_Server.server_socket.shutdown(2)
            self.TCP_Server.server_socket1.shutdown(2)
            self.TCP_Server.StopTcpServer()
        except:
            pass
        print("Close TCP")
        os._exit(0)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%d/%b/%Y %H:%M:%S",
        stream=sys.stdout,
    )
    try:
        myshow = mywindow()
        if myshow.user_ui == True:
            myshow.show()
            sys.exit(myshow.app.exec_())
        else:
            try:
                pass
            except KeyboardInterrupt:
                myshow.close()
        while True:
            pass
    except KeyboardInterrupt:
        myshow.close()


if __name__ == "__main__":
    main()
