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

while True:
    ma = mpu.acceleration
    mg = mpu.gyro
    print(f"Acceleration: X:{ma[0]:.2f}, Y:{ma[1]:.2f}, Z:{ma[2]:.2f} m/s^2")
    print(f"Gyro X:{mg[0]:.2f}, Y:{mg[1]:.2f}, Z:{mg[2]:.2f} degrees/s")
    print(f"Temperature: {mpu.temperature:.2f} C")
    print("")
    time.sleep(1)
