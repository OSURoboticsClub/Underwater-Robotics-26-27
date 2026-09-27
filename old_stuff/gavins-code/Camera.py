# -*- coding: utf-8 -*-
import cv2  # type: ignore
import threading
import time
import sys
import imp  # type: ignore

sys.path.append("~/Underwater-Robotics-24-25/gavins-code")

try:
    gamepad_module = imp.load_compiled("Logiteck_Gamepad_F310", "~/Underwater-Robotics-24-25/gavins-code/Logiteck_Gamepad_F310.pyc")
    gamepad = gamepad_module.gamepad
    print("Successfully loaded gamepad from Logiteck_Gamepad_F310.pyc")
except Exception as e:
    print("Error loading Logiteck_Gamepad_F310.pyc:", e)
    gamepad = None

# Global flag for kill switch
kill_signal = False

def list_available_cameras(max_cameras=10):
    """List all available cameras."""
    available_cameras = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def check_kill_switch():
    """Continuously check for the gamepad's kill switch activation."""
    global kill_signal
    if not gamepad or not gamepad.pad:
        print("Gamepad not initialized. Kill switch disabled.")
        return

    while True:
        gamepad.work()  # Process gamepad inputs
        back_pressed = gamepad.pad.get_button(8)
        start_pressed = gamepad.pad.get_button(9)
        x_pressed = gamepad.pad.get_button(0)

        if back_pressed and start_pressed and x_pressed:
            print("Kill switch activated! Closing camera feed...")
            kill_signal = True
            break
        time.sleep(0.1)  # Prevent high CPU usage

def open_camera(camera_index=0, width=1920, height=1080, fps=60):
    """Opens a high-resolution camera feed with gamepad kill switch support."""
    global kill_signal
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Set high resolution and FPS
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    print("Camera {} opened at {}x{} with {} FPS.".format(camera_index, width, height, fps))

    # Start a separate thread to monitor the kill switch
    kill_thread = threading.Thread(target=check_kill_switch)
    kill_thread.setDaemon(True)  # ✅ Fix for Python 2.7
    kill_thread.start()

    # **Make the window full screen**
    cv2.namedWindow("Camera Feed", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Camera Feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # **Resize frame dynamically to fit screen without stretching**
        screen_width = 1920  # Adjust to your screen size
        screen_height = 1080
        frame_resized = cv2.resize(frame, (screen_width, screen_height), interpolation=cv2.INTER_LINEAR)

        cv2.imshow("Camera Feed", frame_resized)

        # Check if the kill switch was activated
        if kill_signal:
            break

        # Press 'q' to exit manually
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera feed closed.")

if __name__ == "__main__":
    cameras = list_available_cameras()
    if cameras:
        print("Available Cameras:", cameras)
        open_camera(cameras[0])  # Open the first detected camera
    else:
        print("No cameras detected.")
