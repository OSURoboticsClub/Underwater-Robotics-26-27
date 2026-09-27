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

ltrigger_been_pressed = False;
rtrigger_been_pressed = False;

old_values = {
        'lfl': 0.0,
        'lfr': 0.0,
        'lbl': 0.0,
        'lbr': 0.0,
        'vfl': 0.0,
        'vfr': 0.0,
        'vbl': 0.0,
        'vbr': 0.0
        }

def process_motor(label, value, old_values, command_parts):
    value = clamp(value, -1.0, 1.0)
    if value != old_values[label]:
            pwm = to_pwm(value)
            command_parts.append("{} {}".format(label, pwm))
            old_values[label] = value

def joy_callback(msg):
    global ltrigger_been_pressed
    global rtrigger_been_pressed

    if ((not rtrigger_been_pressed) and msg.axes[5] != 0.0): 
        rtrigger_been_pressed = True

    if ((not ltrigger_been_pressed) and msg.axes[2] != 0.0): 
        ltrigger_been_pressed = True


    forward = msg.axes[1]
    strafe = msg.axes[0]
    turn = msg.axes[3]
    roll = msg.axes[6]
    pitch = msg.axes[7]
    if not ltrigger_been_pressed and not rtrigger_been_pressed:
        lift = 0.0
    elif not ltrigger_been_pressed and rtrigger_been_pressed:
        lift = -1 * ((msg.axes[5] - 1.0) / 2.0)
    elif ltrigger_been_pressed and not rtrigger_been_pressed:
        lift = (msg.axes[2] - 1.0) / 2.0
    else:
        lift = ((msg.axes[2] - 1.0) / 2.0) - ((msg.axes[5] - 1.0) / 2.0)
    lift = clamp(lift, -1.0, 1.0)

    command_parts = [];

    lateral_mod = rospy.get_param('~lateral', 1)
    vertical_mod = rospy.get_param('~vertical', 1)
    pitch_roll_mod = rospy.get_param('~pitch_roll', 1)

    lfl = (forward - strafe - turn) * lateral_mod # Lateral Front Left
    lfr = (forward + strafe - turn) * lateral_mod # Lateral Front Right
    lbl = (forward + strafe + turn) * lateral_mod # Lateral Back Left
    lbr = (forward - strafe + turn) * lateral_mod # Lateral Back Right

    vfl = vertical_mod * lift + ( roll - pitch) * pitch_roll_mod # Vertical Front Left
    vfr = vertical_mod * lift + ( roll + pitch) * pitch_roll_mod # Vertical Front Left
    vbl = vertical_mod * lift + (-roll - pitch) * pitch_roll_mod # Vertical Front Left
    vbr = vertical_mod * lift + (-roll + pitch) * pitch_roll_mod # Vertical Front Left


    process_motor('lfl', lfl, old_values, command_parts)
    process_motor('lfr', lfr, old_values, command_parts)
    process_motor('lbl', lbl, old_values, command_parts)
    process_motor('lbr', lbr, old_values, command_parts)

    process_motor('vfl', vfl, old_values, command_parts)
    process_motor('vfr', vfr, old_values, command_parts)
    process_motor('vbl', vbl, old_values, command_parts)
    process_motor('vbr', vbr, old_values, command_parts)

    if command_parts:
        command = "\n".join(command_parts)
        rospy.loginfo("Publishing: {}".format(command))
        pub.publish(command)

rospy.init_node('joy_to_motor', anonymous=True)
pub = rospy.Publisher('motor_command', String, queue_size=10)
rospy.Subscriber('joy', Joy, joy_callback)
rospy.spin()
