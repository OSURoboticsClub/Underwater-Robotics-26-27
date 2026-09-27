#!/usr/bin/env python
import rospy
from std_msgs.msg import String
import json

old_keystates = []
key_states = []

def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))

def to_pwm(cmd, start=1000, end=2000):
    range = end - start
    return int(((cmd + 1.0) / 2.0) * range + start)

old_values = {
        'camera_x': 0.0,
        'camera_y': 0.0,
        'lfl_offset': 0.0,
        'lfr_offset': -404,
        'lbl_offset': -394,
        'lbr_offset': -394
        }

def process_motor(label, value, old_values, command_parts):
    value = clamp(value, -1.0, 1.0)
    if value != old_values[label]:
        pwm = to_pwm(value, 1000, 2000)
        command_parts.append("{} {}".format(label, pwm))
        old_values[label] = value

def process_command(label, value, old_values, command_parts):
    if value != old_values[label]:
        new_value = round(value)
        command_parts.append("{} {}".format(label, new_value))
        old_values[label] = value

def new_key_press(key):
    global key_states
    global old_key_states
    if (key in key_states) and (key not in old_key_states):
        return True
    else:
        return False

def key_states_callback(msg):
    # Parse the JSON string into a Python list
    global old_key_states
    global key_states
    key_states = json.loads(msg.data)

    global old_values
    command_parts = []

    # Print the key states (list of currently pressed keys)
    # rospy.loginfo("Pressed keys: %s", key_states)

    # Example: Using key states for custom logic
    #if new_key_press("UP"):
    #    rospy.loginfo("W")
    #elif new_key_press("DOWN"):
    #    rospy.loginfo("S")
    move_quantity = 0.02
    if "]" in key_states:
        camera_y = 0
    elif "UP" in key_states:
        camera_y = old_values["camera_y"] + move_quantity
    elif "DOWN" in key_states:
        camera_y = old_values["camera_y"] - move_quantity
    else:
        camera_y = old_values["camera_y"]

    if "[" in key_states:
        camera_x = 0
    elif "RIGHT" in key_states:
        camera_x = old_values["camera_x"] - move_quantity
    elif "LEFT" in key_states:
        camera_x = old_values["camera_x"] + move_quantity
    else:
        camera_x = old_values["camera_x"]

    if "1" in key_states:
        target_offset = 'lfl_offset'
    elif "2" in key_states:
        target_offset = 'lfr_offset'
    elif "3" in key_states:
        target_offset = 'lbl_offset'
    elif "4" in key_states:
        target_offset = 'lbr_offset'
    else:
        target_offset = ''

    if target_offset != '':
        offset_change_quantity = 2.0
        if "W" in key_states:
            offset = 0
        elif "A" in key_states:
            offset = old_values[target_offset] - offset_change_quantity
        elif "D" in key_states:
            offset = old_values[target_offset] + offset_change_quantity
        else:
            offset = old_values[target_offset]

        process_command(target_offset, offset, old_values, command_parts)

#    if "D" in key_states: # temp
#        lights = 1.0 # temp
#        old_values["lights"] = lights # temp
#    elif "A" in key_states: # temp
#        lights = 0.0 # temp
#        old_values["lights"] = lights # temp
#    else: # temp
#        lights = old_values["lights"] # temp

#    command_parts.append("lights {}".format(lights)) # temp
    process_motor('camera_x', camera_x, old_values, command_parts)
    process_motor('camera_y', camera_y, old_values, command_parts)

    if command_parts:
        command = "\n".join(command_parts)
        rospy.loginfo("Publishing: {}".format(command))
        pub.publish(command)

    old_key_states = key_states

rospy.init_node('key_state_listener', anonymous=True)
pub = rospy.Publisher('motor_command', String, queue_size=10)
rospy.Subscriber('key_states', String, key_states_callback)
rospy.spin()
