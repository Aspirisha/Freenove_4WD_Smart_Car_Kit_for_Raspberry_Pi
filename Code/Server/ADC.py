import logging

import smbus
import time

logger = logging.getLogger(__name__)


class Adc:
    REFERENCE_VOLTAGE = 3.3
    # I2C address of the device
    ADDRESS = 0x48
    # ADS7830 Command
    # 0x84 = 10000100:
    #  Bit 7: always 1 for single-ended mode, here 1
    #  Bits 6–4: channel selection (CH0–CH7), here 0 channel
    #  Bits 3–0: power-down / mode control (here 0100 for "power-down between conversions" mode)
    ADS7830_CMD = 0x84

    def __init__(self):
        # Get I2C bus
        self._bus = smbus.SMBus(1)

        aa = self._bus.read_byte_data(self.ADDRESS, 0xF4)
        if aa < 150:
            self._model = "PCF8591"
            raise ValueError("PCF8591 not supported")
        self._model = "ADS7830"
        logger.info("Detected ADC type: %s", self._model)

    def _recvADS7830(self, channel):
        # Select correct channel setting bits
        COMMAND_SET = self.ADS7830_CMD | (
            (((channel << 2) | (channel >> 1)) & 0x07) << 4
        )
        self._bus.write_byte(self.ADDRESS, COMMAND_SET)
        while 1:
            value1 = self._bus.read_byte(self.ADDRESS)
            value2 = self._bus.read_byte(self.ADDRESS)
            if value1 == value2:
                break
        voltage = value1 / 255.0 * self.REFERENCE_VOLTAGE  # calculate the voltage value
        voltage = round(voltage, 2)
        return voltage

    def recvADC(self, channel):
        return self._recvADS7830(channel)

    def i2cClose(self):
        self._bus.close()


def loop():
    adc = Adc()
    while True:
        Left_IDR = adc.recvADC(0)
        logger.info("The photoresistor voltage on the left is %.2fV", Left_IDR)
        Right_IDR = adc.recvADC(1)
        logger.info("The photoresistor voltage on the right is %.2fV", Right_IDR)
        voltage = adc.recvADC(2)
        logger.info("Battery voltage is %.2fV", voltage)
        time.sleep(1)


def destroy():
    pass


# Main program logic follows:
if __name__ == "__main__":
    print("Program is starting ... ")
    try:
        loop()
    except (
        KeyboardInterrupt
    ):  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        destroy()
