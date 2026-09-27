#!/usr/bin/env python
import rospy
import serial
from std_msgs.msg import String

ser = None

def shutdown_hook():
    global ser
    rospy.loginfo("Shutting down motor_listener")
    if ser and ser.is_open:
        rospy.loginfo("Closing serial port")
        ser.close()

def main():
    global ser

    rospy.init_node('motor_listener', anonymous=True)
    rospy.on_shutdown(shutdown_hook)

    port = rospy.get_param('~port', '/dev/ttyUSB0')
    baud = rospy.get_param('~baud', 115200)


    try:
        ser = serial.Serial(port, baud, timeout=1)
        ser.flushInput()
        ser.flushOutput()
        rospy.loginfo("Opened serial port{} at {} baud.".format(port, baud))
    except serial.SerialException as e:
        rospy.logerr("Failed to open serial port {}: {}".format(port, e))
        return

    def callback(msg):
        command = msg.data.strip()
        if command == "":
            rospy.loginfo("Ignoring empty command")
            return
        else:
            rospy.loginfo("Sending to ESP32: {}".format(command))
            ser.write((command + '\n').encode())

    pub = rospy.Publisher('arduino_data', String, queue_size=10)
    rospy.Subscriber('motor_command', String, callback)

    rate = rospy.Rate(10) # 10hz
    while not rospy.is_shutdown():
        try:
            if ser.in_waiting:
                data = ser.readline().decode('utf-8').strip()
                rospy.loginfo("Received from Arduino: {}".format(data))
                pub.publish(data)
        except serial.SerialException as e:
            rospy.logerr("Serial error: {}".format(e))
            break;
        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
