from smbus import SMBus

I2C_BUS = 3  # software I2C bus
INA_ADDR = 0x40  # default INA219 address
SHUNT_OHMS = 0.1  # most INA219 boards use a 0.1 ohm shunt

# INA219 register addresses
REG_CONFIG = 0x00
REG_SHUNT_VOLT = 0x01
REG_BUS_VOLT = 0x02
REG_POWER = 0x03
REG_CURRENT = 0x04
REG_CALIBRATION = 0x05

# Calibration value—this sets scaling for current/power
# Works for 0.1 Ω shunt, max ~3.2A
CALIB_VALUE = 4096


class INA219:
    def __init__(self, i2c_bus=I2C_BUS, address=INA_ADDR, shunt_ohms=SHUNT_OHMS):
        self._bus = SMBus(i2c_bus)
        self._address = address
        self._shunt_ohms = shunt_ohms
        self._calibration_value = CALIB_VALUE
        self._write_reg(REG_CALIBRATION, self._calibration_value)

    def _read_reg(self, reg):
        raw = self._bus.read_word_data(self._address, reg)
        # INA219 uses swapped byte order
        val = ((raw & 0xFF) << 8) | (raw >> 8)
        # convert to signed 16-bit
        if val & 0x8000:
            val -= 1 << 16
        return val

    def _write_reg(self, reg, value):
        self._bus.write_word_data(
            self._address, reg, ((value & 0xFF) << 8) | (value >> 8)
        )

    def read_shunt_voltage(self):
        raw = self._read_reg(REG_SHUNT_VOLT)
        return raw * 0.01  # mV

    def read_bus_voltage(self):
        raw = self._read_reg(REG_BUS_VOLT)
        return (raw >> 3) * 0.004  # V

    def read_current(self):
        raw = self._read_reg(REG_CURRENT)
        return raw * 0.1  # mA

    def close(self):
        self._bus.close()
