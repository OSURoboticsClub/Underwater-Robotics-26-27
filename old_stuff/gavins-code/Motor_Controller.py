#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial # type: ignore
import threading
import time

# Optional: If you have serial.tools.list_ports installed, you can uncomment:
# (Make sure to pip install pyserial in Python 2.7 environment)
try:
    import serial.tools.list_ports # type: ignore
    HAS_LIST_PORTS = True
except ImportError:
    HAS_LIST_PORTS = False

def read_from_port(ser):
    """
    Continuously read lines from the serial port and print them.
    """
    while True:
        try:
            if ser.inWaiting() > 0:
                line = ser.readline().strip()
                if line:
                    print("[From Arduino] " + line)
            time.sleep(0.05)
        except Exception as e:
            print("Error reading from port:", e)
            break

def get_serial_port():
    """
    Prompt the user to choose a serial port, optionally listing available ports.
    Returns the user-entered port string.
    """
    while True:
        # Optionally list available ports if the user wants to see them
        if HAS_LIST_PORTS:
            print("Available ports:")
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                print("  (No ports found)")
            else:
                for p in ports:
                    # p is a tuple like (device, description, hwid)
                    print("  {}".format(p.device))

        user_port = raw_input("Enter the Arduino's serial port (e.g. COM3, COM11, /dev/ttyUSB0) or 'q' to quit: ") # type: ignore

        if user_port.lower() in ('q', 'quit'):
            return None  # Signal to exit the script

        if user_port.strip():
            # If they typed something non-empty, use it
            return user_port.strip()
        else:
            print("No port entered. Please try again or type 'q' to quit.\n")

def main():
    baud = 115200  # Match your Arduino sketch
    timeout = 1

    # Prompt for which port to connect
    port = get_serial_port()
    if port is None:
        print("No port selected. Exiting.")
        return

    # Attempt to open the port
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        print("\nOpened serial port:", ser.name)
    except serial.SerialException as e:
        print("Could not open serial port {}: {}".format(port, e))
        return

    # Start a background thread to read from the port
    reader_thread = threading.Thread(target=read_from_port, args=(ser,))
    reader_thread.daemon = True
    reader_thread.start()

    print("\nType a pulse width (1000-2000) in microseconds.")
    print("Type 'q' or 'quit' to exit.\n")

    try:
        while True:
            user_input = raw_input("Enter pulse width> ")  # raw_input in Python 2 # type: ignore

            if user_input.lower() in ('q', 'quit'):
                print("Quitting...")
                break

            # Validate it's an integer
            try:
                pulse_width = int(user_input)
            except ValueError:
                print("Not a valid integer. Try again.")
                continue

            # Range check
            if pulse_width < 1000 or pulse_width > 2000:
                print("Must be between 1000 and 2000 microseconds. Try again.")
                continue

            # Send the integer followed by newline
            ser.write(str(pulse_width) + "\n")

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        if ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
