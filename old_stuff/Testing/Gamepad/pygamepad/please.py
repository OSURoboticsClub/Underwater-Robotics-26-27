from __future__ import print_function
import serial
import time
from inputs import get_gamepad 

arduino = serial.Serial(port='COM5', baudrate=115200, timeout=.1)

def write_read(x):
    arduino.write(bytes(x))
    time.sleep(0.05)
    data = arduino.readline()
    return data

while True:

    events = get_gamepad()
    for event in events:
        if event.code == "ABS_X":
            print("Left stick X-axis:", event.state)
        elif event.code == "BTN_WEST":
            print("X button pressed")
            value = write_read(0)
            print(value)
        elif event.code == "BTN_EAST":
            print("B button pressed")
            value = write_read(180)
            print(value)

