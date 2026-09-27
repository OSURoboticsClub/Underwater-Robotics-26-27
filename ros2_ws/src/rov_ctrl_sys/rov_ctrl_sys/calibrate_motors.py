import rclpy
from rov_ctrl_sys.subscriber_publisher_general import SubscriberPublisher
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from rclpy.parameter import Parameter

from std_msgs.msg import String

class CalibrateMotors(SubscriberPublisher):

    def __init__(self):
        sub_qos = QoS.QoSProfile(
            depth=10, 
            reliability=QoS.ReliabilityPolicy.RELIABLE,
            durability=QoS.DurabilityPolicy.VOLATILE
        )
        pub_qos = QoS.QoSProfile(
            depth=10, 
            reliability=QoS.ReliabilityPolicy.RELIABLE,
            durability=QoS.DurabilityPolicy.VOLATILE
        )
        super().__init__('calibrate_motors', String, 'key_states', String, 'motor_command', sub_qos, pub_qos)

        self.declare_parameter('target_motor', 'lfl')
        self.target_motor = self.get_parameter('target_motor').value
        self.add_on_set_parameters_callback(self._on_params_changed)

        self.commands = {}
        self.CPressed = False
        self.DPressed = False
        self.EPressed = False

    def _on_params_changed(self, params):
        allowed_motors = {'lfl','lfr','lbl','lbr','vfl','vfr','vbl','vbr'}
        for p in params:
            if p.name == 'target_motor':
                if p.value not in allowed_motors:
                    return SetParametersResult(
                        successful=False,
                        reason='not an allowed motor'
                    )
        
        for p in params:
            if p.name  == 'target_motor':
                self.target_motor = p.value

        return SetParametersResult(successful=True)

    def generate_pub_msg(self, msg):
        keys = set(msg.data.split(','))

        if not self.CPressed and 'C' in keys:
            self.CPressed = True
            self.commands.clear()
            self.commands[self.target_motor] = 1500
        elif self.CPressed and 'C' not in keys:
            self.CPressed = False

        if not self.DPressed and 'D' in keys:
            self.DPressed = True
            self.commands.clear()
            self.commands[self.target_motor] = 1000
        elif self.DPressed and 'D' not in keys:
            self.DPressed = False

        if not self.EPressed and 'E' in keys:
            self.EPressed = True
            self.commands.clear()
            self.commands[self.target_motor] = 2000
        elif self.EPressed and 'E' not in keys:
            self.EPressed = False

        if self.commands:
            new_msg = String()
            new_msg.data = ','.join(f'{k}={v:0.2f}' for k,v in self.commands.items())
            self.get_logger().info(f"motor_commands: {new_msg.data}")
            self.commands.clear()
            return new_msg
        else:
            return None

def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = CalibrateMotors()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down (SIGINT)")
        pass
    finally:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
