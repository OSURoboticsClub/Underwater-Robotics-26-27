#!/usr/bin/env python
import rospy
from sensor_msgs.msg import Joy
from std_msgs.msg import String

    # msg has an axes array of length 8
    # msg.axes[0] left stick X: 1=left, -1=right
    # msg.axes[1] left stick Y: 1=up, -1=down
    # msg.axes[2] left trigger, 1.0 is unpressed, -1 is fully pressed
    # msg.axes[3] right stick X: 1=left, -1=right
    # msg.axes[4] right stick Y: 1=up, -1=down
    # msg.axes[5] right trigger, 1.0 is unpressed, -1 is fully pressed
    # NOTE: before the triggers have been pressed once, they stay at 0.0
    #       after they've been pressed once they default to 1.0
    # msg.axes[6] left/right on dpad: 1=dpad right, -1=dpad left
    # msg.axes[7] up/down on dpad: 1=dpad up, -1=dpad down
    # 
    # msg also has an buttons array of length 11
    # msg.buttons[0] = A
    # msg.buttons[1] = B
    # msg.buttons[2] = X
    # msg.buttons[3] = Y
    # msg.buttons[4] = left shoulder
    # msg.buttons[5] = right shoulder
    # msg.buttons[6] = back button
    # msg.buttons[7] = start button
    # msg.buttons[8] = dunno, probably mode but it doesn't register
    # msg.buttons[9] = left stick press
    # msg.buttons[10] = right stick press

def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))

def to_pwm(cmd, start=1000, end=2000):
    range = end - start
    return int(((cmd + 1.0) / 2.0) * range + start)

old_values = {
        'main_manip': 1.0,
        'left_manip': 0.0,
        'top_manip': -1.0,
        'main_mover': 0.0,
        'left_mover': 0.0,
        'lights': 0.0
        }

def process_motor(label, value, old_values, command_parts, send_to_pwm):
    value = clamp(value, -1.0, 1.0)
    if value != old_values[label]:
        if send_to_pwm:
            pwm = to_pwm(value, 500, 2500)
        else:
            pwm = value

        command_parts.append("{} {}".format(label, pwm))
        old_values[label] = value


lshoulder_pressed = False
rshoulder_pressed = False
start_pressed = False
back_pressed = False
def joy_callback(msg):
    global lshoulder_pressed
    global rshoulder_pressed
    global start_pressed
    global back_pressed
    global old_values
    command_parts = [];

    if not lshoulder_pressed and msg.buttons[4] == 1:
        lshoulder_pressed = True
        if old_values["main_manip"] == 1.0:
            process_motor('main_manip', 0.0, old_values, command_parts, False)
        else:
            process_motor('main_manip', 1.0, old_values, command_parts, False)
    elif lshoulder_pressed and msg.buttons[4] == 0:
        lshoulder_pressed = False

    if not rshoulder_pressed and msg.buttons[5] == 1:
        rshoulder_pressed = True
        if old_values["left_manip"] == 1.0:
            process_motor('left_manip', 0.0, old_values, command_parts, False)
        else:
            process_motor('left_manip', 1.0, old_values, command_parts, False)
    elif rshoulder_pressed and msg.buttons[5] == 0:
        rshoulder_pressed = False

    if not start_pressed and msg.buttons[7] == 1:
        start_pressed = True
        if old_values["top_manip"] == -1.0:
            process_motor('top_manip', 1.0, old_values, command_parts, True)
        else:
            process_motor('top_manip', -1.0, old_values, command_parts, True)
    elif start_pressed and msg.buttons[7] == 0:
        start_pressed = False

    if msg.buttons[1] == 1:
        main_mover = 1.0
    elif msg.buttons[2] == 1:
        main_mover = -1.0
    else:
        main_mover = 0.0

    if msg.buttons[0] == 1:
        left_mover = 1.0
    elif msg.buttons[3] == 1:
        left_mover = -1.0
    else:
        left_mover = 0.0

    if not back_pressed and msg.buttons[6] == 1:
        back_pressed = True
        if old_values["lights"] == 0.0:
            process_motor('lights', 1.0, old_values, command_parts, False)
        else:
            process_motor('lights', 0.0, old_values, command_parts, False)
    elif back_pressed and msg.buttons[6] == 0:
        back_pressed = False



    process_motor('main_mover', main_mover, old_values, command_parts, True)
    process_motor('left_mover', left_mover, old_values, command_parts, True)

    if command_parts:
        command = "\n".join(command_parts)
        rospy.loginfo("Publishing: {}".format(command))
        pub.publish(command)

rospy.init_node('joy_to_servo', anonymous=True)
pub = rospy.Publisher('motor_command', String, queue_size=10)
rospy.Subscriber('joy', Joy, joy_callback)
rospy.spin()
