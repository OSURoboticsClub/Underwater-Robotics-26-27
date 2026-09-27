import serial
from inputs import get_gamepad

# Connect to Arduino (update COM port accordingly)
arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

def scale_value(input_val, in_min, in_max, out_min, out_max):
    """Scales input values from one range to another."""
    return int((input_val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def read_controller():
    """Reads input from the gamepad and sends PWM values to Arduino."""
    while True:
        events = get_gamepad()
        for event in events:
            if event.code == "ABS_Y":  # Change based on throttle stick
                joystick_value = event.state
                esc_value = scale_value(joystick_value, -32768, 32767, 1000, 2000)  # Scale to ESC PWM range
                print "Sending PWM: " + str(esc_value)
                arduino.write("{}\n".format(esc_value))  # Send value to Arduino

if __name__ == "__main__":
    read_controller()
