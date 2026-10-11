import rclpy
from rov_ctrl_sys.subscriber_publisher_general import SubscriberPublisher
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from rclpy.parameter import Parameter

from sensor_msgs.msg import Joy
from std_msgs.msg import String

def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))

def to_pwm(cmd, start=1000, end=2000):
    range = end - start
    return int(((cmd + 1.0) / 2.0) * range + start)


class JoyToMotor(SubscriberPublisher):

    def __init__(self):
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
        super().__init__('joy_to_motor', Joy, 'joy', String, 'motor_command', sub_qos, pub_qos)
        self.ltrigger_been_pressed = False
        self.rtrigger_been_pressed = False
        self.old_values = {
            'lfl': 0.0,
            'lfr': 0.0,
            'lbl': 0.0,
            'lbr': 0.0,
            'vfl': 0.0,
            'vfr': 0.0,
            'vbl': 0.0,
            'vbr': 0.0
        }
        self.commands = dict()

        self.lateral = {'lfl', 'lfr', 'lbl', 'lbr'}
        self.vertical = {'vfl', 'vfr', 'vbl', 'vbr'}

        self.lateral_timer = None
        self.vertical_timer = None
        self.timer_delay = 1.0

        self.declare_parameter('allow_rolling', True)
        self.allow_rolling = self.get_parameter('allow_rolling').value

        self._params = {}
        self._params['lateral_cap'] = 0.75
        self._params['vertical_cap'] = 0.75
        self._params['neg_mod'] = 1.0

        self._params['lfl_mod_pos'] = 1.0
        self._params['lfr_mod_pos'] = 1.0
        self._params['lbl_mod_pos'] = 1.0
        self._params['lbr_mod_pos'] = 1.0
        self._params['vfl_mod_pos'] = 1.0
        self._params['vfr_mod_pos'] = 1.0
        self._params['vbl_mod_pos'] = 1.0
        self._params['vbr_mod_pos'] = 1.0

        self._params['lfl_mod_neg'] = 1.0
        self._params['lfr_mod_neg'] = 1.0
        self._params['lbl_mod_neg'] = 1.0
        self._params['lbr_mod_neg'] = 1.0
        self._params['vfl_mod_neg'] = 1.0
        self._params['vfr_mod_neg'] = 1.0
        self._params['vbl_mod_neg'] = 1.0
        self._params['vbr_mod_neg'] = 1.0

#         x: left-right
#         y: up-down
#         z: forward-back

        self._params['x_mod'] = 1.0
        self._params['x_lfl'] = 1.0
        self._params['x_lfr'] = 1.0
        self._params['x_lbl'] = 1.0
        self._params['x_lbr'] = 1.0

        self._params['z_mod'] = 1.0
        self._params['z_lfl'] = 1.0
        self._params['z_lfr'] = 1.0
        self._params['z_lbl'] = 1.0
        self._params['z_lbr'] = 1.0

        self._params['yaw_mod'] = 1.0
        self._params['yaw_lfl'] = 1.0
        self._params['yaw_lfr'] = 1.0
        self._params['yaw_lbl'] = 1.0
        self._params['yaw_lbr'] = 1.0

        self._params['y_mod'] = 1.0
        self._params['y_vfl'] = 1.0
        self._params['y_vfr'] = 1.0
        self._params['y_vbl'] = 1.0
        self._params['y_vbr'] = 1.0

        self._params['pitch_mod'] = 1.0
        self._params['pitch_vfl'] = 1.0
        self._params['pitch_vfr'] = 1.0
        self._params['pitch_vbl'] = 1.0
        self._params['pitch_vbr'] = 1.0

        self._params['roll_mod'] = 1.0
        self._params['roll_vfl'] = 1.0
        self._params['roll_vfr'] = 1.0
        self._params['roll_vbl'] = 1.0
        self._params['roll_vbr'] = 1.0

        for key, val in self._params.items():
            self.declare_parameter(key, val)
            self._params[key] = self.get_parameter(key).value

        self.add_on_set_parameters_callback(self._on_params_changed)

        self.get_logger().info(f"Parameters:")
        self.get_logger().info(f"  lateral_cap: {self._params['lateral_cap']}")
        self.get_logger().info(f"  vertical_cap: {self._params['vertical_cap']}")
        self.get_logger().info(f"  x_mod: {self._params['x_mod']}")
        self.get_logger().info(f"  y_mod: {self._params['y_mod']}")
        self.get_logger().info(f"  z_mod: {self._params['z_mod']}")
        self.get_logger().info(f"  pitch_mod: {self._params['pitch_mod']}")
        self.get_logger().info(f"  yaw_mod: {self._params['yaw_mod']}")
        self.get_logger().info(f"  roll_mod: {self._params['roll_mod']}")
        self.get_logger().info(f"  allow_rolling: {self.allow_rolling}")

        for key, val in self._params.items():
            if val != 1.0:
                self.get_logger().info(f'  {key}: {val}')

    def process_motor(self, key, value):
        value = clamp(value, -1.0, 1.0)
        if value != self.old_values[key]:
            pwm = to_pwm(value)
            self.commands[key] = pwm
            self.old_values[key] = value
        else:
            self.commands.pop(key, None)
    
    def _on_params_changed(self, params):
        for p in params:
            if p.name in self._params:
                if p.type_ not in (Parameter.Type.DOUBLE, Parameter.Type.INTEGER):
                    return SetParametersResult(
                        successful=False,
                        reason='motor scalars must be numeric'
                    )

                if p.value < 0:
                    return SetParametersResult(
                        successful=False,
                        reason='motor scalars must be nonnegative'
                    )
        
        for p in params:
            if p.name in self._params:
                self._params[p.name] = float(p.value)
                self.get_logger().info(f'Set {p.name} to: {float(p.value)}')

        return SetParametersResult(successful=True)

    def gen_lateral_timer(self, cmds):
        msg = String()
        msg.data = ','.join(f'{k}={v}' for k,v in cmds.items())
        def temp():
            self.publisher_.publish(msg)
            self.get_logger().info('Executing lateral timer')
#             self.lateral_timer.cancel()
#             self.lateral_timer = None
        return temp

    def gen_vertical_timer(self, cmds):
        msg = String()
        msg.data = ','.join(f'{k}={v}' for k,v in cmds.items())
        def temp():
            self.publisher_.publish(msg)
            self.get_logger().info('Executing vertical timer')
#             self.vertical_timer.cancel()
#             self.vertical_timer = None
        return temp

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
    def generate_pub_msg(self, msg):
        if ((not self.rtrigger_been_pressed) and msg.axes[5] != 0.0): 
            self.rtrigger_been_pressed = True

        if ((not self.ltrigger_been_pressed) and msg.axes[2] != 0.0): 
            self.ltrigger_been_pressed = True

        z = msg.axes[1]
        x = msg.axes[0]
        yaw = msg.axes[3]

        if self.allow_rolling:
            roll = msg.axes[6]
            pitch = msg.axes[7]
        else:
            roll = 0.0
            pitch = 0.0

        if not self.ltrigger_been_pressed and not self.rtrigger_been_pressed:
            y = 0.0
        elif not self.ltrigger_been_pressed and self.rtrigger_been_pressed:
            y = -1 * ((msg.axes[5] - 1.0) / 2.0)
        elif self.ltrigger_been_pressed and not self.rtrigger_been_pressed:
            y = (msg.axes[2] - 1.0) / 2.0
        else:
            y = ((msg.axes[2] - 1.0) / 2.0) - ((msg.axes[5] - 1.0) / 2.0)
        y = clamp(y, -1.0, 1.0)

        z *= self._params['z_mod']
        x *= self._params['x_mod']
        y *= self._params['y_mod']
        yaw *= self._params['yaw_mod']
        pitch *= self._params['pitch_mod']
        roll *= self._params['roll_mod']

        lfl = z*self._params['z_lfl'] - x*self._params['x_lfl'] - yaw*self._params['yaw_lfl']
        lfr = z*self._params['z_lfr'] + x*self._params['x_lfr'] + yaw*self._params['yaw_lfr']
        lbl = z*self._params['z_lbl'] - x*self._params['x_lbl'] + yaw*self._params['yaw_lbl']
        lbr = z*self._params['z_lbr'] + x*self._params['x_lbr'] - yaw*self._params['yaw_lbr']
        vfl = y*self._params['y_vfl'] - roll*self._params['roll_vfl'] - pitch*self._params['pitch_vfl']
        vfr = y*self._params['y_vfr'] + roll*self._params['roll_vfr'] - pitch*self._params['pitch_vfr']
        vbl = y*self._params['y_vbl'] - roll*self._params['roll_vbl'] + pitch*self._params['pitch_vbl']
        vbr = y*self._params['y_vbr'] + roll*self._params['roll_vbr'] + pitch*self._params['pitch_vbr']

        lfl = clamp(lfl, -1.0, 1.0)
        lfr = clamp(lfr, -1.0, 1.0)
        lbl = clamp(lbl, -1.0, 1.0)
        lbr = clamp(lbr, -1.0, 1.0)
        vfl = clamp(vfl, -1.0, 1.0)
        vfr = clamp(vfr, -1.0, 1.0)
        vbl = clamp(vbl, -1.0, 1.0)
        vbr = clamp(vbr, -1.0, 1.0)

        if lfl < 0:
          lfl *= self._params['lfl_mod_neg'] * self._params['neg_mod']
        else:
          lfl *= self._params['lfl_mod_pos']

        if lfr < 0:
          lfr *= self._params['lfr_mod_neg'] * self._params['neg_mod']
        else:
          lfr *= self._params['lfr_mod_pos']

        if lbl < 0:
          lbl *= self._params['lbl_mod_neg'] * self._params['neg_mod']
        else:
          lbl *= self._params['lbl_mod_pos']

        if lbr < 0:
          lbr *= self._params['lbr_mod_neg'] * self._params['neg_mod']
        else:
          lbr *= self._params['lbr_mod_pos']

        if vfl < 0:
          vfl *= self._params['vfl_mod_neg'] * self._params['neg_mod']
        else:
          vfl *= self._params['vfl_mod_pos']

        if vfr < 0:
          vfr *= self._params['vfr_mod_neg'] * self._params['neg_mod']
        else:
          vfr *= self._params['vfr_mod_pos']

        if vbl < 0:
          vbl *= self._params['vbl_mod_neg'] * self._params['neg_mod']
        else:
          vbl *= self._params['vbl_mod_pos']

        if vbr < 0:
          vbr *= self._params['vbr_mod_neg'] * self._params['neg_mod']
        else:
          vbr *= self._params['vbr_mod_pos']

        lfl = clamp(lfl, -self._params['lateral_cap'], self._params['lateral_cap'])
        lfr = clamp(lfr, -self._params['lateral_cap'], self._params['lateral_cap'])
        lbl = clamp(lbl, -self._params['lateral_cap'], self._params['lateral_cap'])
        lbr = clamp(lbr, -self._params['lateral_cap'], self._params['lateral_cap'])
        vfl = clamp(vfl, -self._params['vertical_cap'], self._params['vertical_cap'])
        vfr = clamp(vfr, -self._params['vertical_cap'], self._params['vertical_cap'])
        vbl = clamp(vbl, -self._params['vertical_cap'], self._params['vertical_cap'])
        vbr = clamp(vbr, -self._params['vertical_cap'], self._params['vertical_cap'])

        self.process_motor('lfl', lfl)
        self.process_motor('lfr', lfr)
        self.process_motor('lbl', lbl)
        self.process_motor('lbr', lbr)
        self.process_motor('vfl', vfl)
        self.process_motor('vfr', vfr)
        self.process_motor('vbl', vbl)
        self.process_motor('vbr', vbr)

        if self.commands:
            new_msg = String()
            new_msg.data = ','.join(f'{k}={v}' for k,v in self.commands.items())
            self.get_logger().info(f"motor_commands: {new_msg.data}")

            lateral_commands = {k: self.commands[k] for k in self.commands if k in self.lateral}
            if len(lateral_commands) > 0 and self.lateral_timer:
                self.lateral_timer.cancel()
                self.lateral_timer = None
                self.get_logger().info('Cancelled lateral timer')
                pass
            lateral_commands = {k: v for k,v in lateral_commands.items() if v == 1500}
            if len(lateral_commands) == 4:
                self.lateral_timer = self.create_timer(self.timer_delay, 
                        self.gen_lateral_timer(lateral_commands))
                self.get_logger().info('Scheduled lateral timer')
                pass

            vertical_commands = {k: self.commands[k] for k in self.commands if k in self.vertical}
            if len(vertical_commands) > 0 and self.vertical_timer:
                self.vertical_timer.cancel()
                self.vertical_timer = None
                self.get_logger().info('Cancelled vertical timer')
                pass
            vertical_commands = {k: v for k,v in vertical_commands.items() if v == 1500}
            if len(vertical_commands) == 4:
                self.vertical_timer = self.create_timer(self.timer_delay, 
                        self.gen_vertical_timer(vertical_commands))
                self.get_logger().info('Scheduled vertical timer')
                pass

            return new_msg
        else:
            return None

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
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
