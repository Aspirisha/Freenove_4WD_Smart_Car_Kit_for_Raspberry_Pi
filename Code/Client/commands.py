import logging

from Command import COMMAND as cmd

logger = logging.getLogger(__name__)


def get_motor_command(pressed_keys: set[str]) -> str:
    full_speed = 3000
    part_speed = 0
    if "w" not in pressed_keys and "s" not in pressed_keys:
        logger.info("Stopping motors")
        left_upper_wheel = 0
        left_lower_wheel = 0
        right_upper_wheel = 0
        right_lower_wheel = 0
    elif "w" in pressed_keys:
        if "d" in pressed_keys:
            logger.info("Moving forward right")
            left_upper_wheel = full_speed
            left_lower_wheel = full_speed
            right_upper_wheel = part_speed
            right_lower_wheel = part_speed
        elif "a" in pressed_keys:
            logger.info("Moving forward left")
            left_upper_wheel = part_speed
            left_lower_wheel = part_speed
            right_upper_wheel = full_speed
            right_lower_wheel = full_speed
        else:  # just forward
            logger.info("Moving forward")
            left_upper_wheel = full_speed
            left_lower_wheel = full_speed
            right_upper_wheel = full_speed
            right_lower_wheel = full_speed
    elif "s" in pressed_keys:
        if "a" in pressed_keys:
            logger.info("Moving back left")
            left_upper_wheel = -part_speed
            left_lower_wheel = -part_speed
            right_upper_wheel = -full_speed
            right_lower_wheel = -full_speed
        elif "d" in pressed_keys:
            logger.info("Moving back right")
            left_upper_wheel = -full_speed
            left_lower_wheel = -full_speed
            right_upper_wheel = -part_speed
            right_lower_wheel = -part_speed
        else:
            logger.info("Moving back")
            left_upper_wheel = -full_speed
            left_lower_wheel = -full_speed
            right_upper_wheel = -full_speed
            right_lower_wheel = -full_speed
    return f"{cmd.CMD_MOTOR}#{left_upper_wheel}#{left_lower_wheel}#{right_upper_wheel}#{right_lower_wheel}\n"


def get_motor_precise_command(throttle: float, steering: float) -> str:
    full_speed = 3000
    a = 1 - steering
    b = 1 + steering

    left_upper_wheel = int(full_speed * throttle * b)
    left_lower_wheel = int(full_speed * throttle * b)
    right_upper_wheel = int(full_speed * throttle * a)
    right_lower_wheel = int(full_speed * throttle * a)

    return f"{cmd.CMD_MOTOR}#{left_upper_wheel}#{left_lower_wheel}#{right_upper_wheel}#{right_lower_wheel}\n"
