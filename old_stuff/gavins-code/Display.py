# -*- coding: utf-8 -*-
import subprocess
import time
import psutil  # type: ignore
import pygetwindow as gw  # type: ignore
import os
import ctypes  # For hiding taskbar

# Define script paths
scripts = {
    "Camera.py": "~/Underwater-Robotics-24-25/gavins-code/Camera.py",
    "ROV_Controller_Mapping.py": "~/Underwater-Robotics-24-25/gavins-code/ROV_Controller_Mapping.py",
    "Controller_Mapping.py": "~/Underwater-Robotics-24-25/gavins-code/Controller_Mapping.py"
}

def hide_taskbar():
    """Hides the Windows taskbar automatically."""
    hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
    ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = Hide

def show_taskbar():
    """Restores the Windows taskbar when the script exits."""
    hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
    ctypes.windll.user32.ShowWindow(hwnd, 5)  # 5 = Show

def is_script_running(script_name, script_path):
    """Check if a script is already running by full path."""
    for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            if process.info['cmdline'] and script_path in " ".join(process.info['cmdline']):
                return True  # Script is already running
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

# Hide the taskbar before launching applications
hide_taskbar()

try:
    processes = []

    # **STEP 1: Start Camera Feed first**
    camera_script = "Camera.py"
    camera_path = scripts[camera_script]

    if not is_script_running(camera_script, camera_path):
        print ("Starting Camera Feed...")
        try:
            with open(os.devnull, 'w') as FNULL:  # Hide terminal output
                camera_proc = subprocess.Popen(
                    ["C:/Python27/python.exe", camera_path],
                    stdout=FNULL, stderr=FNULL, creationflags=subprocess.SW_HIDE
                )
            processes.append(camera_proc)
            time.sleep(2)  # Give Camera time to initialize
        except Exception as e:
            print ("Error starting {}: {}").format(camera_script, e)
    else:
        print ("Skipping (already running): Camera Feed")

    # **STEP 2: Wait for 7 seconds before launching other scripts**
    print ("Waiting 7 seconds before launching other scripts...")
    time.sleep(7)

    # **STEP 3: Start other scripts (excluding Camera Feed)**
    for script_name, script_path in scripts.iteritems():  # `.iteritems()` for Python 2 dict iteration
        if script_name != "Camera.py":  # Skip Camera since it's already running
            if not is_script_running(script_name, script_path):
                print ("Starting: {}").format(script_name)
                try:
                    with open(os.devnull, 'w') as FNULL:
                        proc = subprocess.Popen(
                            ["C:/Python27/python.exe", script_path],
                            stdout=FNULL, stderr=FNULL, creationflags=subprocess.SW_HIDE
                        )
                    processes.append(proc)
                    time.sleep(2)  # Allow initialization
                except Exception as e:
                    print ("Error starting {}: {}").format(script_name, e)
            else:
                print ("Skipping (already running): {}").format(script_name)

    # Allow time for windows to appear
    time.sleep(5)

    # **STEP 4: Arrange Windows**
    windows = gw.getAllTitles()
    print ("\nAll Open Windows:"), windows

    expected_windows = {
        "Camera Feed": None,
        "ROV Controller Mapping": None,
        "Controller Mapping": None
    }

    for title in windows:
        if "Camera Feed" in title:
            expected_windows["Camera Feed"] = title
        elif "ROV Controller Mapping" in title:
            expected_windows["ROV Controller Mapping"] = title
        elif "Controller Mapping" in title or "Controller" in title:
            expected_windows["Controller Mapping"] = title

    for key, title in expected_windows.iteritems():
        if title:
            try:
                win = gw.getWindowsWithTitle(title)[0]
                win.restore()
                if key == "Camera Feed":
                    win.moveTo(0, 0)
                    win.resizeTo(1920, 1080)
                elif key == "ROV Controller Mapping":
                    win.moveTo(1680, -50)
                    win.resizeTo(375, 275)
                elif key == "Controller Mapping":
                    win.moveTo(1675, 200)
                    win.resizeTo(375, 177.5)
                print ("Arranged:"), key
            except Exception as e:
                print ("Error arranging window '{}': {}").format(title, e)

    print ("\nWindows arranged successfully!")

finally:
    # Restore the taskbar after script execution
    show_taskbar()
