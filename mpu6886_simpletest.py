#Sample script for MPU6886

import time
import board
from busio import I2C
import mpu6886

i2c = I2C(board.IMU_SCL, board.IMU_SDA)
mpu = mpu6886.MPU6886(i2c)

while True:
    print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2"%(mpu.acceleration))
    print("Gyro X:%.2f, Y: %.2f, Z: %.2f degrees/s"%(mpu.gyro))
    print("Temperature: %.2f C"%mpu.temperature)
    print("")
    time.sleep(1)
