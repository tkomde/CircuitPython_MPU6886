# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Taiki Komoda for JINS Inc.
#
# SPDX-License-Identifier: MIT
"""
`mpu6886`
================================================================================

CircuitPython helper library for the MPU6886 6-DoF Accelerometer and Gyroscope


* Author(s): Taiki Komoda

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

# imports

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jins-tkomoda/CircuitPython_MPU6886.git"

from math import radians
from time import sleep

from adafruit_bus_device import i2c_device
from adafruit_register.i2c_bit import RWBit
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_struct import ROUnaryStruct, Struct, UnaryStruct
from micropython import const

try:
    from typing import Tuple

    from busio import I2C
except ImportError:
    pass

_MPU6886_DEFAULT_ADDRESS = const(0x68)  # MPU6886 default i2c address w/ AD0 low
_MPU6886_DEVICE_ID = const(0x19)  # The correct MPU6886_WHO_AM_I value

_MPU6886_SELF_TEST_X = const(0x0D)  # Self test factory calibrated values register
_MPU6886_SELF_TEST_Y = const(0x0E)  # Self test factory calibrated values register
_MPU6886_SELF_TEST_Z = const(0x0F)  # Self test factory calibrated values register
_MPU6886_SELF_TEST_A = const(0x10)  # Self test factory calibrated values register
_MPU6886_SMPLRT_DIV = const(0x19)  # sample rate divisor register
_MPU6886_CONFIG = const(0x1A)  # General configuration register @OK
_MPU6886_GYRO_CONFIG = const(0x1B)  # Gyro specfic configuration register @OK
_MPU6886_ACCEL_CONFIG = const(0x1C)  # Accelerometer specific configration register @OK
_MPU6886_INT_PIN_CONFIG = const(0x37)  # Interrupt pin configuration register
_MPU6886_ACCEL_OUT = const(0x3B)  # base address for sensor data reads
_MPU6886_TEMP_OUT = const(0x41)  # Temperature data high byte register
_MPU6886_GYRO_OUT = const(0x43)  # base address for sensor data reads
_MPU6886_SIG_PATH_RESET = const(0x68)  # register to reset sensor signal paths
_MPU6886_USER_CTRL = const(0x6A)  # FIFO and I2C Master control register
_MPU6886_PWR_MGMT_1 = const(0x6B)  # Primary power/sleep control register @OK
_MPU6886_PWR_MGMT_2 = const(0x6C)  # Secondary power/sleep control register
_MPU6886_WHO_AM_I = const(0x75)  # Divice ID register

STANDARD_GRAVITY = 9.80665


class ClockSource:  # pylint: disable=too-few-public-methods
    """Allowed values for :py:attr:`clock_source`.

    * :py:attr:`ClockSource.CLKSEL_INTERNAL_8MHz`
    * :py:attr:`ClockSource.CLKSEL_INTERNAL_X`
    * :py:attr:`ClockSource.CLKSEL_INTERNAL_Y`
    * :py:attr:`ClockSource.CLKSEL_INTERNAL_Z`
    * :py:attr:`ClockSource.CLKSEL_EXTERNAL_32`
    * :py:attr:`ClockSource.CLKSEL_EXTERNAL_19`
    * :py:attr:`ClockSource.CLKSEL_RESERVED`
    * :py:attr:`ClockSource.CLKSEL_STOP`
    """

    CLKSEL_INTERNAL_8MHz = const(0)  # Internal 8MHz oscillator
    CLKSEL_INTERNAL_X = const(1)  # PLL with X Axis gyroscope reference
    CLKSEL_INTERNAL_Y = const(2)  # PLL with Y Axis gyroscope reference
    CLKSEL_INTERNAL_Z = const(3)  # PLL with Z Axis gyroscope reference
    CLKSEL_EXTERNAL_32 = const(4)  # External 32.768 kHz reference
    CLKSEL_EXTERNAL_19 = const(5)  # External 19.2 MHz reference
    CLKSEL_RESERVED = const(6)  # Reserved
    CLKSEL_STOP = const(7)  # Stops the clock, constant reset mode


class Range:  # pylint: disable=too-few-public-methods
    """Allowed values for :py:attr:`accelerometer_range`.

    * :py:attr:`Range.RANGE_2_G`
    * :py:attr:`Range.RANGE_4_G`
    * :py:attr:`Range.RANGE_8_G`
    * :py:attr:`Range.RANGE_16_G`

    """

    RANGE_2_G = const(0)  # +/- 2g (default value)
    RANGE_4_G = const(1)  # +/- 4g
    RANGE_8_G = const(2)  # +/- 8g
    RANGE_16_G = const(3)  # +/- 16g


class GyroRange:  # pylint: disable=too-few-public-methods
    """Allowed values for :py:attr:`gyro_range`.

    * :py:attr:`GyroRange.RANGE_250_DPS`
    * :py:attr:`GyroRange.RANGE_500_DPS`
    * :py:attr:`GyroRange.RANGE_1000_DPS`
    * :py:attr:`GyroRange.RANGE_2000_DPS`

    """

    RANGE_250_DPS = const(0)  # +/- 250 deg/s (default value)
    RANGE_500_DPS = const(1)  # +/- 500 deg/s
    RANGE_1000_DPS = const(2)  # +/- 1000 deg/s
    RANGE_2000_DPS = const(3)  # +/- 2000 deg/s


class Rate:  # pylint: disable=too-few-public-methods
    """Allowed values for :py:attr:`cycle_rate`.

    * :py:attr:`Rate.CYCLE_1_25_HZ`
    * :py:attr:`Rate.CYCLE_5_HZ`
    * :py:attr:`Rate.CYCLE_20_HZ`
    * :py:attr:`Rate.CYCLE_40_HZ`

    """

    CYCLE_1_25_HZ = const(0)  # 1.25 Hz
    CYCLE_5_HZ = const(1)  # 5 Hz
    CYCLE_20_HZ = const(2)  # 20 Hz
    CYCLE_40_HZ = const(3)  # 40 Hz


class MPU6886:
    """Driver for the MPU6886 6-DoF accelerometer and gyroscope.

    :param ~busio.I2C i2c_bus: The I2C bus the device is connected to
    :param int address: The I2C device address. Defaults to :const:`0x68`

    **Quickstart: Importing and using the device**

        Here is an example of using the :class:`MPU6886` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            import mpu6886

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = board.I2C()  # uses board.SCL and board.SDA
            sensor = mpu6886.MPU6886(i2c)

        Now you have access to the :attr:`acceleration`, :attr:`gyro`
        and :attr:`temperature` attributes

        .. code-block:: python

            acc_x, acc_y, acc_z = sensor.acceleration
            gyro_x, gyro_y, gyro_z = sensor.gyro
            temperature = sensor.temperature
    """

    def __init__(self, i2c_bus: I2C, address: int = _MPU6886_DEFAULT_ADDRESS) -> None:
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)

        if self._device_id != _MPU6886_DEVICE_ID:
            raise RuntimeError("Failed to find MPU6886 - check your wiring!")

        self.reset()

        self._sample_rate_divisor = 0
        self._gyro_range = GyroRange.RANGE_500_DPS
        self._accel_range = Range.RANGE_2_G
        sleep(0.100)
        self.clock_source = ClockSource.CLKSEL_INTERNAL_X  # set to use gyro x-axis as reference
        sleep(0.100)
        self.sleep = False
        sleep(0.010)

    @classmethod
    def reset(cls) -> None:
        """Reinitialize the sensor"""
        # Touble...
        # self._reset = True
        # while self._reset is True:
        # sleep(0.1)

        sleep(0.1)

        _signal_path_reset = 0b111  # reset all sensors
        sleep(0.1)

    _clksel = RWBits(3, _MPU6886_PWR_MGMT_1, 0)
    _device_id = ROUnaryStruct(_MPU6886_WHO_AM_I, ">B")

    _reset = RWBit(_MPU6886_PWR_MGMT_1, 7, 1)
    _signal_path_reset = RWBits(3, _MPU6886_SIG_PATH_RESET, 3)

    _gyro_range = RWBits(2, _MPU6886_GYRO_CONFIG, 3)
    _accel_range = RWBits(2, _MPU6886_ACCEL_CONFIG, 3)

    _filter_bandwidth = RWBits(2, _MPU6886_CONFIG, 3)

    _raw_accel_data = Struct(_MPU6886_ACCEL_OUT, ">hhh")
    _raw_gyro_data = Struct(_MPU6886_GYRO_OUT, ">hhh")
    _raw_temp_data = ROUnaryStruct(_MPU6886_TEMP_OUT, ">h")

    _cycle = RWBit(_MPU6886_PWR_MGMT_1, 5)
    _cycle_rate = RWBits(2, _MPU6886_PWR_MGMT_2, 6, 1)

    sleep = RWBit(_MPU6886_PWR_MGMT_1, 6, 1)
    """Shuts down the accelerometers and gyroscopes, saving power. No new data will
    be recorded until the sensor is taken out of sleep by setting to `False`"""
    sample_rate_divisor = UnaryStruct(_MPU6886_SMPLRT_DIV, ">B")
    """The sample rate divisor. See the datasheet for additional detail"""

    @property
    def temperature(self) -> float:
        """The current temperature in  º Celsius"""
        raw_temperature = self._raw_temp_data
        temp = (raw_temperature / 340.0) + 36.53
        return temp

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """Acceleration X, Y, and Z axis data in :math:`m/s^2`"""
        raw_data = self._raw_accel_data
        raw_x = raw_data[0]
        raw_y = raw_data[1]
        raw_z = raw_data[2]

        accel_range = self._accel_range
        accel_scale = 1
        if accel_range == Range.RANGE_16_G:
            accel_scale = 2048
        if accel_range == Range.RANGE_8_G:
            accel_scale = 4096
        if accel_range == Range.RANGE_4_G:
            accel_scale = 8192
        if accel_range == Range.RANGE_2_G:
            accel_scale = 16384

        # setup range dependant scaling
        accel_x = (raw_x / accel_scale) * STANDARD_GRAVITY
        accel_y = (raw_y / accel_scale) * STANDARD_GRAVITY
        accel_z = (raw_z / accel_scale) * STANDARD_GRAVITY

        return (accel_x, accel_y, accel_z)

    @property
    def gyro(self) -> Tuple[float, float, float]:
        """Gyroscope X, Y, and Z axis data in :math:`rad/s`"""
        raw_data = self._raw_gyro_data
        raw_x = raw_data[0]
        raw_y = raw_data[1]
        raw_z = raw_data[2]

        gyro_scale = 1
        gyro_range = self._gyro_range
        if gyro_range == GyroRange.RANGE_250_DPS:
            gyro_scale = 131
        if gyro_range == GyroRange.RANGE_500_DPS:
            gyro_scale = 65.5
        if gyro_range == GyroRange.RANGE_1000_DPS:
            gyro_scale = 32.8
        if gyro_range == GyroRange.RANGE_2000_DPS:
            gyro_scale = 16.4

        # setup range dependant scaling
        gyro_x = radians(raw_x / gyro_scale)
        gyro_y = radians(raw_y / gyro_scale)
        gyro_z = radians(raw_z / gyro_scale)

        return (gyro_x, gyro_y, gyro_z)

    @property
    def cycle(self) -> bool:
        """Enable or disable periodic measurement at a rate set by :meth:`cycle_rate`.
        If the sensor was in sleep mode, it will be waken up to cycle"""
        return self._cycle

    @cycle.setter
    def cycle(self, value: bool) -> None:
        self.sleep = not value
        self._cycle = value

    @property
    def gyro_range(self) -> int:
        """The measurement range of all gyroscope axes. Must be a `GyroRange`"""
        return self._gyro_range

    @gyro_range.setter
    def gyro_range(self, value: int) -> None:
        if (value < 0) or (value > 3):
            raise ValueError("gyro_range must be a GyroRange")
        self._gyro_range = value
        sleep(0.01)

    @property
    def accelerometer_range(self) -> int:
        """The measurement range of all accelerometer axes. Must be a `Range`"""
        return self._accel_range

    @accelerometer_range.setter
    def accelerometer_range(self, value: int) -> None:
        if (value < 0) or (value > 3):
            raise ValueError("accelerometer_range must be a Range")
        self._accel_range = value
        sleep(0.01)

    @property
    def cycle_rate(self) -> int:
        """The rate that measurements are taken while in `cycle` mode. Must be a `Rate`"""
        return self._cycle_rate

    @cycle_rate.setter
    def cycle_rate(self, value: int) -> None:
        if (value < 0) or (value > 3):
            raise ValueError("cycle_rate must be a Rate")
        self._cycle_rate = value
        sleep(0.01)

    @property
    def clock_source(self) -> int:
        """The clock source for the sensor"""
        return self._clksel

    @clock_source.setter
    def clock_source(self, value: int) -> None:
        """Select between Internal/External clock sources"""
        if value not in range(8):
            raise ValueError("clock_source must be ClockSource value, integer from 0 - 7.")
        self._clksel = value
