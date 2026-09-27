# -*- coding: utf-8 -*-
from PyQt4.QtCore import pyqtSignal, QObject, QThread, pyqtSlot  # type: ignore
from PyQt4.QtGui import QApplication  # type: ignore
import pygame  # type: ignore
import sys

# Initialize QApplication only if it hasn't been created
app = QApplication.instance() or QApplication([])

class GamepadThread(QObject):
    """Handles gamepad input with PyQt4 signals and real-time debug printing."""

    # Button Signals (from Logitech F310 Layout)
    XSignal = pyqtSignal()
    ASignal = pyqtSignal()
    BSignal = pyqtSignal()
    YSignal = pyqtSignal()
    LButtonSignal = pyqtSignal()
    RButtonSignal = pyqtSignal()
    StartSignal = pyqtSignal()
    BackSignal = pyqtSignal()
    LStickClickSignal = pyqtSignal()
    RStickClickSignal = pyqtSignal()

    # Trigger Signals
    LTriggerSignal = pyqtSignal()
    RTriggerSignal = pyqtSignal()

    # D-Pad Signals
    UpSignal = pyqtSignal()
    DownSignal = pyqtSignal()
    LeftSignal = pyqtSignal()
    RightSignal = pyqtSignal()
    TopRightSignal = pyqtSignal()
    TopLeftSignal = pyqtSignal()
    BottomRightSignal = pyqtSignal()
    BottomLeftSignal = pyqtSignal()

    # Joystick Movement Signals
    LStickUpSignal = pyqtSignal()
    LStickDownSignal = pyqtSignal()
    LStickLeftSignal = pyqtSignal()
    LStickRightSignal = pyqtSignal()
    LStickTopRightSignal = pyqtSignal()
    LStickTopLeftSignal = pyqtSignal()
    LStickBottomRightSignal = pyqtSignal()
    LStickBottomLeftSignal = pyqtSignal()
    LStickIdleSignal = pyqtSignal()

    RStickUpSignal = pyqtSignal()
    RStickDownSignal = pyqtSignal()
    RStickLeftSignal = pyqtSignal()
    RStickRightSignal = pyqtSignal()
    RStickTopRightSignal = pyqtSignal()
    RStickTopLeftSignal = pyqtSignal()
    RStickBottomRightSignal = pyqtSignal()
    RStickBottomLeftSignal = pyqtSignal()
    RStickIdleSignal = pyqtSignal()

    def __init__(self, parent=None):
        super(GamepadThread, self).__init__(parent)

        # Initialize pygame joystick
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("No gamepad detected!")
            self.pad = None
        else:
            self.pad = pygame.joystick.Joystick(0)
            self.pad.init()
            print("Gamepad detected: {}".format(self.pad.get_name()))

        self.abort = False
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.process)

        # Store previous states to only print on changes
        self.prev_buttons = {btn: False for btn in range(12)}
        self.prev_hat = (0, 0)
        self.prev_lstick = (0, 0)
        self.prev_rstick = (0, 0)

    def start(self):
        """Starts the gamepad thread without blocking execution."""
        if not self.thread.isRunning():
            self.thread.start()

    @pyqtSlot()
    def stop(self):
        """Stops the gamepad thread."""
        self.abort = True
        self.thread.quit()
        self.thread.wait()  # Ensure thread stops before exiting

    def check_exit_combination(self):
        """Checks if Back, Start, and X are all pressed to exit the program."""
        if not self.pad:
            return
        back_pressed = self.pad.get_button(8)
        start_pressed = self.pad.get_button(9)
        x_pressed = self.pad.get_button(0)

        if back_pressed and start_pressed and x_pressed:
            print("[EXIT] Back + Start + X pressed. Exiting program...")
            sys.exit(0)

    def get_joystick_positions(self):
        """
        Returns a tuple (lx, ly, rx, ry) with the current joystick axes values.
        The y-axis values are inverted so that pushing the stick forward yields a positive value.
        """
        if self.pad:
            lx = self.pad.get_axis(0)
            ly = self.pad.get_axis(1)  # Invert y-axis for left stick
            rx = self.pad.get_axis(2)
            ry = self.pad.get_axis(3)  # Invert y-axis for right stick
            return (lx, ly, rx, ry)
        return (0.0, 0.0, 0.0, 0.0)

    def work(self):
        """Reads gamepad input, emits signals, and prints debug output."""
        if self.pad:
            pygame.event.pump()

            # Process button signals
            button_map = {
                0: (self.XSignal, "X button"),
                1: (self.ASignal, "A button"),
                2: (self.BSignal, "B button"),
                3: (self.YSignal, "Y button"),
                4: (self.LButtonSignal, "Left Bumper"),
                5: (self.RButtonSignal, "Right Bumper"),
                6: (self.LTriggerSignal, "Left Trigger"),
                7: (self.RTriggerSignal, "Right Trigger"),
                8: (self.BackSignal, "Back button"),
                9: (self.StartSignal, "Start button"),
                10: (self.LStickClickSignal, "Left Stick Click"),
                11: (self.RStickClickSignal, "Right Stick Click"),
            }
            for btn, (signal, name) in button_map.items():
                pressed = self.pad.get_button(btn)
                if pressed and not self.prev_buttons[btn]:
                    print("[Button Pressed] {}".format(name))
                    signal.emit()
                elif not pressed and self.prev_buttons[btn]:
                    print("[Button Released] {}".format(name))
                self.prev_buttons[btn] = pressed

            self.check_exit_combination()

            # D-Pad Handling
            hat_x, hat_y = self.pad.get_hat(0)
            if (hat_x, hat_y) != self.prev_hat:
                if hat_x == 1 and hat_y == 1:
                    print("[D-Pad] Top Right pressed")
                    self.TopRightSignal.emit()
                elif hat_x == -1 and hat_y == 1:
                    print("[D-Pad] Top Left pressed")
                    self.TopLeftSignal.emit()
                elif hat_x == 1 and hat_y == -1:
                    print("[D-Pad] Bottom Right pressed")
                    self.BottomRightSignal.emit()
                elif hat_x == -1 and hat_y == -1:
                    print("[D-Pad] Bottom Left pressed")
                    self.BottomLeftSignal.emit()
                elif hat_y == 1:
                    print("[D-Pad] Up pressed")
                    self.UpSignal.emit()
                elif hat_y == -1:
                    print("[D-Pad] Down pressed")
                    self.DownSignal.emit()
                elif hat_x == -1:
                    print("[D-Pad] Left pressed")
                    self.LeftSignal.emit()
                elif hat_x == 1:
                    print("[D-Pad] Right pressed")
                    self.RightSignal.emit()
                if hat_x == 0 and hat_y == 0 and self.prev_hat != (0, 0):
                    print("[D-Pad] Released")
                self.prev_hat = (hat_x, hat_y)

            # Joystick Handling with y-axis inversion
            lx = self.pad.get_axis(0)
            ly = self.pad.get_axis(1)  # Invert left stick y-axis
            rx = self.pad.get_axis(2)
            ry = self.pad.get_axis(3)  # Invert right stick y-axis
            dead_zone = 0.2
            lx = 0 if abs(lx) < dead_zone else lx
            ly = 0 if abs(ly) < dead_zone else ly
            rx = 0 if abs(rx) < dead_zone else rx
            ry = 0 if abs(ry) < dead_zone else ry

            if (lx, ly) != self.prev_lstick:
                if lx > 0.5 and ly < -0.5:
                    print("[Left Stick] Top Right")
                    self.LStickTopRightSignal.emit()
                elif lx < -0.5 and ly < -0.5:
                    print("[Left Stick] Top Left")
                    self.LStickTopLeftSignal.emit()
                elif lx > 0.5 and ly > 0.5:
                    print("[Left Stick] Bottom Right")
                    self.LStickBottomRightSignal.emit()
                elif lx < -0.5 and ly > 0.5:
                    print("[Left Stick] Bottom Left")
                    self.LStickBottomLeftSignal.emit()
                elif ly < -0.5:
                    print("[Left Stick] Up")
                    self.LStickUpSignal.emit()
                elif ly > 0.5:
                    print("[Left Stick] Down")
                    self.LStickDownSignal.emit()
                elif lx < -0.5:
                    print("[Left Stick] Left")
                    self.LStickLeftSignal.emit()
                elif lx > 0.5:
                    print("[Left Stick] Right")
                    self.LStickRightSignal.emit()
                elif lx == 0 and ly == 0:
                    print("[Left Stick] Idle")
                    self.LStickIdleSignal.emit()
                self.prev_lstick = (lx, ly)

            if (rx, ry) != self.prev_rstick:
                if rx > 0.5 and ry < -0.5:
                    print("[Right Stick] Top Right")
                    self.RStickTopRightSignal.emit()
                elif rx < -0.5 and ry < -0.5:
                    print("[Right Stick] Top Left")
                    self.RStickTopLeftSignal.emit()
                elif rx > 0.5 and ry > 0.5:
                    print("[Right Stick] Bottom Right")
                    self.RStickBottomRightSignal.emit()
                elif rx < -0.5 and ry > 0.5:
                    print("[Right Stick] Bottom Left")
                    self.RStickBottomLeftSignal.emit()
                elif ry < -0.5:
                    print("[Right Stick] Up")
                    self.RStickUpSignal.emit()
                elif ry > 0.5:
                    print("[Right Stick] Down")
                    self.RStickDownSignal.emit()
                elif rx < -0.5:
                    print("[Right Stick] Left")
                    self.RStickLeftSignal.emit()
                elif rx > 0.5:
                    print("[Right Stick] Right")
                    self.RStickRightSignal.emit()
                elif rx == 0 and ry == 0:
                    print("[Right Stick] Idle")
                    self.RStickIdleSignal.emit()
                self.prev_rstick = (rx, ry)

    @pyqtSlot()
    def process(self):
        while not self.abort:
            try:
                self.work()
            except Exception as e:
                print("Error in gamepad processing:", e)

# Start gamepad thread without blocking
gamepad = GamepadThread()
gamepad.start()

if __name__ == "__main__":
    sys.exit(app.exec_())
