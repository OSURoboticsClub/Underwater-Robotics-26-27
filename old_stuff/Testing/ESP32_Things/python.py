import serial
import time

arduino = serial.Serial(port='COM5', baudrate=115200, timeout=.1)


def write_read(x):
    arduino.write(bytes(x))
    time.sleep(0.05)
    data = arduino.readline()
    return data


while True:
    num = input("Enter an angle (0-180): ")
    value = write_read(num)
    print(value)
