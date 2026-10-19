import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rcl_interfaces.msg import SetParametersResult
from rclpy.parameter import Parameter

from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped


def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))


class JoyToMotor(Node):
    """Translate joystick input into a TwistStamped velocity command.

    Subscribes to ``joy`` (sensor_msgs/Joy) and publishes a
    geometry_msgs/TwistStamped on ``cmd_vel``.

    The six degrees of freedom are mapped as follows (body frame):
        linear.x  – forward / back   (left-stick Y)
        linear.y  – left / right     (left-stick X)
        linear.z  – up / down        (triggers)
        angular.x – roll             (d-pad left / right, if enabled)
        angular.y – pitch            (d-pad up / down, if enabled)
        angular.z – yaw              (right-stick X)
    """

    def __init__(self):
        super().__init__('joy_to_motor')

        # ---- QoS profiles ----
        sub_qos = QoS.QoSProfile(
            depth=10,
            reliability=QoS.ReliabilityPolicy.BEST_EFFORT,
            durability=QoS.DurabilityPolicy.VOLATILE
        )
        pub_qos = QoS.QoSProfile(
            depth=10,
            reliability=QoS.ReliabilityPolicy.RELIABLE,
            durability=QoS.DurabilityPolicy.VOLATILE
        )

        # ---- Subscriber & Publisher ----
        self.subscription = self.create_subscription(
            Joy, 'joy', self._joy_callback, sub_qos)
        self.publisher_ = self.create_publisher(
            TwistStamped, 'cmd_vel', pub_qos)

        # ---- Trigger latch state ----
        self.ltrigger_been_pressed = False
        self.rtrigger_been_pressed = False

        # ---- Parameters ----
        self.declare_parameter('allow_rolling', True)
        self.allow_rolling = self.get_parameter('allow_rolling').value

        self.declare_parameter('frame_id', 'base_link')
        self.frame_id = self.get_parameter('frame_id').value

        self._params = {}

        # Speed caps (applied as final clamp on each axis, range 0‒1)
        self._params['lateral_cap'] = 0.75
        self._params['vertical_cap'] = 0.75

        # Per-axis scaling multipliers
        self._params['x_mod'] = 1.0     # left / right
        self._params['y_mod'] = 1.0     # up / down
        self._params['z_mod'] = 1.0     # forward / back
        self._params['yaw_mod'] = 1.0
        self._params['pitch_mod'] = 1.0
        self._params['roll_mod'] = 1.0

        for key, val in self._params.items():
            self.declare_parameter(key, val)
            self._params[key] = self.get_parameter(key).value

        self.add_on_set_parameters_callback(self._on_params_changed)

        # ---- Startup logging ----
        self.get_logger().info('Parameters:')
        self.get_logger().info(f'  frame_id:      {self.frame_id}')
        self.get_logger().info(f'  lateral_cap:   {self._params["lateral_cap"]}')
        self.get_logger().info(f'  vertical_cap:  {self._params["vertical_cap"]}')
        self.get_logger().info(f'  x_mod:         {self._params["x_mod"]}')
        self.get_logger().info(f'  y_mod:         {self._params["y_mod"]}')
        self.get_logger().info(f'  z_mod:         {self._params["z_mod"]}')
        self.get_logger().info(f'  pitch_mod:     {self._params["pitch_mod"]}')
        self.get_logger().info(f'  yaw_mod:       {self._params["yaw_mod"]}')
        self.get_logger().info(f'  roll_mod:      {self._params["roll_mod"]}')
        self.get_logger().info(f'  allow_rolling: {self.allow_rolling}')

    # ------------------------------------------------------------------
    # Parameter validation
    # ------------------------------------------------------------------
    def _on_params_changed(self, params):
        for p in params:
            if p.name in self._params:
                if p.type_ not in (Parameter.Type.DOUBLE, Parameter.Type.INTEGER):
                    return SetParametersResult(
                        successful=False,
                        reason='scalars must be numeric')
                if p.value < 0:
                    return SetParametersResult(
                        successful=False,
                        reason='scalars must be nonnegative')

        for p in params:
            if p.name in self._params:
                self._params[p.name] = float(p.value)
                self.get_logger().info(f'Set {p.name} to: {float(p.value)}')

        return SetParametersResult(successful=True)

    # ------------------------------------------------------------------
    # Joy callback — maps axes to a TwistStamped
    # ------------------------------------------------------------------
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
    def _joy_callback(self, msg):
        # --- Trigger latching (triggers report 0.0 until first press) ---
        if (not self.rtrigger_been_pressed) and msg.axes[5] != 0.0:
            self.rtrigger_been_pressed = True
        if (not self.ltrigger_been_pressed) and msg.axes[2] != 0.0:
            self.ltrigger_been_pressed = True

        # --- Raw axis extraction ---
        # forward / back  (left stick Y)
        z = msg.axes[1]
        # left / right    (left stick X)
        x = msg.axes[0]
        # yaw             (right stick X)
        yaw = msg.axes[3]

        # Roll / pitch from d-pad (if enabled)
        if self.allow_rolling:
            roll = msg.axes[6]
            pitch = msg.axes[7]
        else:
            roll = 0.0
            pitch = 0.0

        # Vertical from triggers
        if not self.ltrigger_been_pressed and not self.rtrigger_been_pressed:
            y = 0.0
        elif not self.ltrigger_been_pressed and self.rtrigger_been_pressed:
            y = -1 * ((msg.axes[5] - 1.0) / 2.0)
        elif self.ltrigger_been_pressed and not self.rtrigger_been_pressed:
            y = (msg.axes[2] - 1.0) / 2.0
        else:
            y = ((msg.axes[2] - 1.0) / 2.0) - ((msg.axes[5] - 1.0) / 2.0)
        y = clamp(y, -1.0, 1.0)

        # --- Apply per-axis scaling ---
        z *= self._params['z_mod']
        x *= self._params['x_mod']
        y *= self._params['y_mod']
        yaw *= self._params['yaw_mod']
        pitch *= self._params['pitch_mod']
        roll *= self._params['roll_mod']

        # --- Clamp to caps ---
        lat_cap = self._params['lateral_cap']
        vert_cap = self._params['vertical_cap']

        x = clamp(x, -lat_cap, lat_cap)
        z = clamp(z, -lat_cap, lat_cap)
        yaw = clamp(yaw, -lat_cap, lat_cap)
        y = clamp(y, -vert_cap, vert_cap)
        pitch = clamp(pitch, -vert_cap, vert_cap)
        roll = clamp(roll, -vert_cap, vert_cap)

        # --- Build and publish TwistStamped ---
        twist_msg = TwistStamped()
        twist_msg.header.stamp = self.get_clock().now().to_msg()
        twist_msg.header.frame_id = self.frame_id

        twist_msg.twist.linear.x = z      # forward / back
        twist_msg.twist.linear.y = x      # left / right (strafe)
        twist_msg.twist.linear.z = y      # up / down
        twist_msg.twist.angular.x = roll
        twist_msg.twist.angular.y = pitch
        twist_msg.twist.angular.z = yaw

        self.publisher_.publish(twist_msg)

        self.get_logger().debug(
            f'cmd_vel  lin=({z:.2f}, {x:.2f}, {y:.2f})  '
            f'ang=({roll:.2f}, {pitch:.2f}, {yaw:.2f})')


def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = JoyToMotor()

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
