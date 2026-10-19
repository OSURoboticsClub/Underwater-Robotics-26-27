import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rcl_interfaces.msg import SetParametersResult
from rclpy.parameter import Parameter

from geometry_msgs.msg import TwistStamped
from std_msgs.msg import String


def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))


def to_pwm(cmd, start=1000, end=2000):
    """Map a value in [-1, 1] to a PWM value in [start, end]."""
    pwm_range = end - start
    return int(((cmd + 1.0) / 2.0) * pwm_range + start)


class ThrusterAllocator(Node):
    """Convert a 6-DOF TwistStamped into 8 individual motor PWM commands.

    Subscribes to ``cmd_vel`` (geometry_msgs/TwistStamped) and publishes
    motor commands as a CSV string on ``motor_command`` (std_msgs/String)
    for the motor_controller serial bridge.

    Thruster layout (body frame, looking from above):
        Lateral (horizontal plane):
            lfl – lateral front-left
            lfr – lateral front-right
            lbl – lateral back-left
            lbr – lateral back-right
        Vertical:
            vfl – vertical front-left
            vfr – vertical front-right
            vbl – vertical back-left
            vbr – vertical back-right

    Twist mapping:
        linear.x  → forward / back   (z axis in old code)
        linear.y  → left / right     (x axis in old code)
        linear.z  → up / down        (y axis in old code)
        angular.x → roll
        angular.y → pitch
        angular.z → yaw
    """

    def __init__(self):
        super().__init__('thruster_allocator')

        # ---- QoS profiles ----
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

        # ---- Subscriber & Publisher ----
        self.subscription = self.create_subscription(
            TwistStamped, 'cmd_vel', self._twist_callback, sub_qos)
        self.publisher_ = self.create_publisher(
            String, 'motor_command', pub_qos)

        # ---- Track previous PWM values (only publish on change) ----
        self.old_values = {
            'lfl': 0.0, 'lfr': 0.0, 'lbl': 0.0, 'lbr': 0.0,
            'vfl': 0.0, 'vfr': 0.0, 'vbl': 0.0, 'vbr': 0.0
        }

        # ---- Idle timers (re-send stop commands after sticks released) ----
        self.lateral_names = {'lfl', 'lfr', 'lbl', 'lbr'}
        self.vertical_names = {'vfl', 'vfr', 'vbl', 'vbr'}
        self.lateral_timer = None
        self.vertical_timer = None
        self.timer_delay = 1.0

        # ---- Parameters ----
        self._params = {}

        # Speed caps
        self._params['lateral_cap'] = 0.75
        self._params['vertical_cap'] = 0.75

        # Global negative-direction modifier
        self._params['neg_mod'] = 1.0

        # ---- Per-motor positive / negative modifiers ----
        for motor in ('lfl', 'lfr', 'lbl', 'lbr', 'vfl', 'vfr', 'vbl', 'vbr'):
            self._params[f'{motor}_mod_pos'] = 1.0
            self._params[f'{motor}_mod_neg'] = 1.0

        # ---- Mixing matrix weights ----
        # Lateral motors: how much each DOF contributes to each motor.
        # Signs encode the default thruster geometry.
        #
        #   lfl =  fwd * z_lfl  -  strafe * x_lfl  -  yaw * yaw_lfl
        #   lfr =  fwd * z_lfr  +  strafe * x_lfr  +  yaw * yaw_lfr
        #   lbl =  fwd * z_lbl  -  strafe * x_lbl  +  yaw * yaw_lbl
        #   lbr =  fwd * z_lbr  +  strafe * x_lbr  -  yaw * yaw_lbr
        for motor in ('lfl', 'lfr', 'lbl', 'lbr'):
            self._params[f'x_{motor}'] = 1.0
            self._params[f'z_{motor}'] = 1.0
            self._params[f'yaw_{motor}'] = 1.0

        # Vertical motors:
        #   vfl =  heave * y_vfl  -  roll * roll_vfl  -  pitch * pitch_vfl
        #   vfr =  heave * y_vfr  +  roll * roll_vfr  -  pitch * pitch_vfr
        #   vbl =  heave * y_vbl  -  roll * roll_vbl  +  pitch * pitch_vbl
        #   vbr =  heave * y_vbr  +  roll * roll_vbr  +  pitch * pitch_vbr
        for motor in ('vfl', 'vfr', 'vbl', 'vbr'):
            self._params[f'y_{motor}'] = 1.0
            self._params[f'pitch_{motor}'] = 1.0
            self._params[f'roll_{motor}'] = 1.0

        # Declare all as ROS parameters
        for key, val in self._params.items():
            self.declare_parameter(key, val)
            self._params[key] = self.get_parameter(key).value

        self.add_on_set_parameters_callback(self._on_params_changed)

        self.get_logger().info('Thruster allocator started')
        self.get_logger().info(f'  lateral_cap:  {self._params["lateral_cap"]}')
        self.get_logger().info(f'  vertical_cap: {self._params["vertical_cap"]}')
        self.get_logger().info(f'  neg_mod:      {self._params["neg_mod"]}')
        for key, val in self._params.items():
            if val != 1.0 and key not in ('lateral_cap', 'vertical_cap', 'neg_mod'):
                self.get_logger().info(f'  {key}: {val}')

    # ------------------------------------------------------------------
    # Parameter validation
    # ------------------------------------------------------------------
    def _on_params_changed(self, params):
        for p in params:
            if p.name in self._params:
                if p.type_ not in (Parameter.Type.DOUBLE, Parameter.Type.INTEGER):
                    return SetParametersResult(
                        successful=False,
                        reason='motor scalars must be numeric')
                if p.value < 0:
                    return SetParametersResult(
                        successful=False,
                        reason='motor scalars must be nonnegative')

        for p in params:
            if p.name in self._params:
                self._params[p.name] = float(p.value)
                self.get_logger().info(f'Set {p.name} to: {float(p.value)}')

        return SetParametersResult(successful=True)

    # ------------------------------------------------------------------
    # Mixing
    # ------------------------------------------------------------------
    def _twist_callback(self, msg):
        fwd    = msg.twist.linear.x   # forward / back
        strafe = msg.twist.linear.y   # left / right
        heave  = msg.twist.linear.z   # up / down
        roll   = msg.twist.angular.x
        pitch  = msg.twist.angular.y
        yaw    = msg.twist.angular.z

        p = self._params  # shorthand

        # ---- Lateral mixing ----
        lfl = ( fwd * p['z_lfl'] - strafe * p['x_lfl'] - yaw * p['yaw_lfl'])
        lfr = ( fwd * p['z_lfr'] + strafe * p['x_lfr'] + yaw * p['yaw_lfr'])
        lbl = ( fwd * p['z_lbl'] - strafe * p['x_lbl'] + yaw * p['yaw_lbl'])
        lbr = ( fwd * p['z_lbr'] + strafe * p['x_lbr'] - yaw * p['yaw_lbr'])

        # ---- Vertical mixing ----
        vfl = ( heave * p['y_vfl'] - roll * p['roll_vfl'] - pitch * p['pitch_vfl'])
        vfr = ( heave * p['y_vfr'] + roll * p['roll_vfr'] - pitch * p['pitch_vfr'])
        vbl = ( heave * p['y_vbl'] - roll * p['roll_vbl'] + pitch * p['pitch_vbl'])
        vbr = ( heave * p['y_vbr'] + roll * p['roll_vbr'] + pitch * p['pitch_vbr'])

        # ---- Clamp to [-1, 1] ----
        motors = {
            'lfl': clamp(lfl, -1.0, 1.0),
            'lfr': clamp(lfr, -1.0, 1.0),
            'lbl': clamp(lbl, -1.0, 1.0),
            'lbr': clamp(lbr, -1.0, 1.0),
            'vfl': clamp(vfl, -1.0, 1.0),
            'vfr': clamp(vfr, -1.0, 1.0),
            'vbl': clamp(vbl, -1.0, 1.0),
            'vbr': clamp(vbr, -1.0, 1.0),
        }

        # ---- Apply per-motor directional modifiers ----
        for key in motors:
            if motors[key] < 0:
                motors[key] *= p[f'{key}_mod_neg'] * p['neg_mod']
            else:
                motors[key] *= p[f'{key}_mod_pos']

        # ---- Apply speed caps ----
        lat_cap = p['lateral_cap']
        vert_cap = p['vertical_cap']
        for key in self.lateral_names:
            motors[key] = clamp(motors[key], -lat_cap, lat_cap)
        for key in self.vertical_names:
            motors[key] = clamp(motors[key], -vert_cap, vert_cap)

        # ---- Convert to PWM, build command dict (only changed values) ----
        commands = {}
        for key, value in motors.items():
            if value != self.old_values[key]:
                commands[key] = to_pwm(value)
                self.old_values[key] = value

        if not commands:
            return

        # ---- Publish ----
        cmd_str = ','.join(f'{k}={v}' for k, v in commands.items())
        self.get_logger().info(f'motor_commands: {cmd_str}')

        # ---- Idle timers: re-send neutral after sticks released ----
        lateral_cmds = {k: commands[k] for k in commands if k in self.lateral_names}
        if lateral_cmds and self.lateral_timer:
            self.lateral_timer.cancel()
            self.lateral_timer = None
            self.get_logger().info('Cancelled lateral timer')

        neutral_laterals = {k: v for k, v in lateral_cmds.items() if v == 1500}
        if len(neutral_laterals) == 4:
            self.lateral_timer = self.create_timer(
                self.timer_delay, self._gen_timer_cb(neutral_laterals))
            self.get_logger().info('Scheduled lateral timer')

        vertical_cmds = {k: commands[k] for k in commands if k in self.vertical_names}
        if vertical_cmds and self.vertical_timer:
            self.vertical_timer.cancel()
            self.vertical_timer = None
            self.get_logger().info('Cancelled vertical timer')

        neutral_verticals = {k: v for k, v in vertical_cmds.items() if v == 1500}
        if len(neutral_verticals) == 4:
            self.vertical_timer = self.create_timer(
                self.timer_delay, self._gen_timer_cb(neutral_verticals))
            self.get_logger().info('Scheduled vertical timer')

        out_msg = String()
        out_msg.data = cmd_str
        self.publisher_.publish(out_msg)

    def _gen_timer_cb(self, cmds):
        """Create a one-shot timer callback that re-publishes neutral commands."""
        msg = String()
        msg.data = ','.join(f'{k}={v}' for k, v in cmds.items())
        def _cb():
            self.publisher_.publish(msg)
            self.get_logger().info('Executing idle timer')
        return _cb


def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = ThrusterAllocator()

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
