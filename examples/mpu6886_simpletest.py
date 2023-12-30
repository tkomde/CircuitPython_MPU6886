# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Taiki Komoda for JINS Inc.
#
# SPDX-License-Identifier: Unlicense
"""
Sample script for MPU6886
"""

import time
import board
from busio import I2C
import mpu6886

i2c = I2C(board.IMU_SCL, board.IMU_SDA)
mpu = mpu6886.MPU6886(i2c)

mpu.gyro_range = 1
time.sleep(0.05)
mpu.accelerometer_range = 1
time.sleep(0.05)

while True:
    ac = mpu.acceleration
    gy = mpu.gyro
    print(f"Acceleration: X:{ac[0]:.2f}, Y:{ac[1]:.2f}, Z:{ac[2]:.2f} m/s^2")
    print(f"Gyro X:{gy[0]:.2f}, Y:{gy[1]:.2f}, Z:{gy[2]:.2f} rad/s")
    print(f"Temperature: {mpu.temperature:.2f} C")
    print("")
    time.sleep(1)
