import time
import math
import logging
from PCA9685 import PCA9685
from ADC import *

logger = logging.getLogger(__name__)


class Motor:
    MIN_DUTY = -4095
    MAX_DUTY = 4095

    def __init__(self):
        self.pwm = PCA9685(0x40, debug=True)
        self.pwm.setPWMFreq(50)
        self.time_proportion = 3  # Depend on your own car,If you want to get the best out of the rotation mode, change the value by experimenting.
        self.adc = Adc()

    def _duty_range(self, *duties):
        return (max(min(d, self.MAX_DUTY), self.MIN_DUTY) for d in duties)

    def left_Upper_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(0, 0)
            self.pwm.setMotorPwm(1, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(1, 0)
            self.pwm.setMotorPwm(0, abs(duty))
        else:
            self.pwm.setMotorPwm(0, self.MAX_DUTY)
            self.pwm.setMotorPwm(1, self.MAX_DUTY)

    def left_Lower_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(3, 0)
            self.pwm.setMotorPwm(2, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(2, 0)
            self.pwm.setMotorPwm(3, abs(duty))
        else:
            self.pwm.setMotorPwm(2, self.MAX_DUTY)
            self.pwm.setMotorPwm(3, self.MAX_DUTY)

    def right_Upper_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(6, 0)
            self.pwm.setMotorPwm(7, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(7, 0)
            self.pwm.setMotorPwm(6, abs(duty))
        else:
            self.pwm.setMotorPwm(6, self.MAX_DUTY)
            self.pwm.setMotorPwm(7, self.MAX_DUTY)

    def right_Lower_Wheel(self, duty):
        if duty > 0:
            self.pwm.setMotorPwm(4, 0)
            self.pwm.setMotorPwm(5, duty)
        elif duty < 0:
            self.pwm.setMotorPwm(5, 0)
            self.pwm.setMotorPwm(4, abs(duty))
        else:
            self.pwm.setMotorPwm(4, self.MAX_DUTY)
            self.pwm.setMotorPwm(5, self.MAX_DUTY)

    def setMotorModel(self, lu_duty, ll_duty, ru_duty, rl_duty):
        lu_duty, ll_duty, ru_duty, rl_duty = self._duty_range(
            lu_duty, ll_duty, ru_duty, rl_duty
        )
        self.left_Upper_Wheel(lu_duty)
        self.left_Lower_Wheel(ll_duty)
        self.right_Upper_Wheel(ru_duty)
        self.right_Lower_Wheel(rl_duty)
        logger.info(
            "Set motor model with duties: %d, %d, %d, %d",
            lu_duty,
            ll_duty,
            ru_duty,
            rl_duty,
        )

    def Rotate(self, n):
        angle = n
        bat_compensate = 7.5 / (self.adc.recvADC(2) * 3)
        while True:
            W = 2000

            VY = int(2000 * math.cos(math.radians(angle)))
            VX = -int(2000 * math.sin(math.radians(angle)))

            FR = VY - VX + W
            FL = VY + VX - W
            BL = VY - VX - W
            BR = VY + VX + W

            PWM.setMotorModel(FL, BL, FR, BR)
            print("rotating")
            time.sleep(5 * self.time_proportion * bat_compensate / 1000)
            angle -= 5


PWM = Motor()


def loop():
    PWM.setMotorModel(2000, 2000, 2000, 2000)  # Forward
    time.sleep(3)
    PWM.setMotorModel(-2000, -2000, -2000, -2000)  # Back
    time.sleep(3)
    PWM.setMotorModel(-500, -500, 2000, 2000)  # Left
    time.sleep(3)
    PWM.setMotorModel(2000, 2000, -500, -500)  # Right
    time.sleep(3)
    PWM.setMotorModel(0, 0, 0, 0)  # Stop


def destroy():
    PWM.setMotorModel(0, 0, 0, 0)


if __name__ == "__main__":
    try:
        loop()
    except (
        KeyboardInterrupt
    ):  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        destroy()
