import rclpy
from std_msgs.msg import String
from rov_ctrl_sys.subscriber_general import Subscriber
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rcl_interfaces.msg import ParameterDescriptor

import threading
import queue
import serial

class MotorController(Subscriber):

    def __init__(self):
        qos = QoS.QoSProfile(
            depth=10,
            reliability=QoS.ReliabilityPolicy.RELIABLE,
            durability=QoS.DurabilityPolicy.VOLATILE
        )

        super().__init__('motor_controller', String, 'motor_command', qos)
        port_descriptor = ParameterDescriptor(description='Serial port the motors are connected to')
        baud_descriptor = ParameterDescriptor(description='The rate used to communicate on the serial port')

        self.declare_parameter('port', '/dev/ttyUSB0', port_descriptor)
        self.declare_parameter('baud', 115200, baud_descriptor)

        self.port = self.get_parameter('port').value
        self.baud = self.get_parameter('baud').value

        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0)
            self.ser.flushInput()
            self.ser.flushOutput()
            self.get_logger().info(f'Opened serial port {self.port} at {self.baud} baud.')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port {self.port}: {e}')
            self.ser = None

        self.pub = self.create_publisher(String, 'motor_feedback', qos)
        self.timer = self.create_timer(0.02, self.timer_callback)

        self.write_queue = queue.Queue()
        self.writer_thread = threading.Thread(target=self.serial_writer, daemon=True)
        self.writer_thread.start()
        self.rx_buffer = bytearray()

    def destroy_node(self):
        self.get_logger().info(f'Shutting down {self.get_name()}')
        self.write_queue.put(None)
        self.writer_thread.join(timeout=1.0)
        if self.ser and self.ser.is_open:
            self.get_logger().info('Closing serial port')
            self.ser.close()
        super().destroy_node()
    
    def listener_callback(self, msg):
        if msg.data == "":
            self.get_logger().warn('Ignoring empty command')
        elif (not self.ser) or (not self.ser.is_open):
            self.get_logger().warn(f'Serial port is closed, rejecting command: {msg.data}')
        else:
            self.get_logger().info(f'Queuing to ESP32: "{msg.data}"')
            self.write_queue.put(msg.data + '\n')

    def serial_writer(self):
        while True:
            msg = self.write_queue.get()
            if msg is None:
                break
            try: 
                self.ser.write(msg.encode('utf-8'))
            except Exception as e:
                self.get_logger().warn(f'Serial write error: {e}')

    def timer_callback(self):
        try:
            while self.ser and self.ser.in_waiting:
                c = self.ser.read(1)
                if c == b'\n':
                    line = self.rx_buffer.decode('utf-8', errors='ignore').strip()
                    self.rx_buffer.clear()
                    if line:
                        self.pub.publish(String(data=line))
                        self.get_logger().debug(f'Received from Esp32: {line}')
                else:
                    self.rx_buffer += c
        except Exception as e:
            self.get_logger().warn(f'Serial read error: {e}')


def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = MotorController()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down (SIGINT)")
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
