import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rov_ctrl_sys.subscriber_general import Subscriber
from rov_ctrl_sys.text_print import TextPrint
from sensor_msgs.msg import Image
from std_msgs.msg import String

import pygame
import threading
import json
import pathlib
import math

def rov_color(speed):
    speed = float(speed)
    if (speed == 1500) or (speed == 0):
        return (0,0,0)
    elif speed > 1500:
        return (  0,175,  0)
    else:
        return (255,0,0)

class Window(Node):

    def __init__(self):
        super().__init__('window')

        self.declare_parameter('fullscreen', True)
        self.fullscreen = self.get_parameter('fullscreen').value
        self.declare_parameter('image_width', 640)
        self.image_width = self.get_parameter('image_width').value
        self.declare_parameter('image_height', 480)
        self.image_height = self.get_parameter('image_height').value


        self.img_size = (self.image_width, self.image_height)
        img_ratio = self.image_width / self.image_height

        self.max_img_box = (960,720)
        box_ratio = self.max_img_box[0] / self.max_img_box[1]
        
        if img_ratio >= box_ratio:
            self.img_box_size = (self.max_img_box[0], self.max_img_box[0] * (1/img_ratio))
        else:
            self.img_box_size = (self.max_img_box[1] * img_ratio, self.max_img_box[1])

        self.screen_updates = []

        pygame.init()
        self.running = True
        self.screen = pygame.display.set_mode((1280,720), flags=pygame.SCALED)
#         self.screen = pygame.display.set_mode((640,360), flags=pygame.SCALED)
        if self.fullscreen:
            pygame.display.toggle_fullscreen()

        pygame.display.set_caption("ROV Control Window")
        pygame.mouse.set_visible(True)
        self.text = TextPrint()

#        self.clock = pygame.time.Clock()


        self.buffer_size = self.img_size[0] * self.img_size[1] * 3
        self.buffers = [bytearray(self.buffer_size),bytearray(self.buffer_size)]
        self.img_surfaces = [pygame.image.frombuffer(self.buffers[0], self.img_size, 'RGB'), pygame.image.frombuffer(self.buffers[1], self.img_size, 'RGB')]
        self.front_idx = 0
        self.new_frame = False
        self.img_lock = threading.Lock()
        self.img_dir = str(pathlib.Path.home()) + '/Underwater-Robotics-Current/crab_detect/rov_photos/'
        self.img_num = 1

        self.held_keys = set()
        self.keymap = {
                pygame.K_UP: 'UP',          # change controls
                pygame.K_DOWN: 'DOWN',      # ^^
                pygame.K_LEFT: 'LEFT',      # ^^
                pygame.K_RIGHT: 'RIGHT',    # ^^
                pygame.K_BACKSPACE: "BACKSPACE", # reset
                pygame.K_c: 'C', # camera
                pygame.K_d: 'D', # dome lights
                pygame.K_e: 'E', # external lights
                pygame.K_x: 'X',
                pygame.K_y: 'Y',
                pygame.K_p: 'P', # crab processing
                pygame.K_f: 'F', # fullscreen
#                 pygame.K_w: 'W',
#                 pygame.K_a: 'A',
#                 pygame.K_s: 'S',
#                 pygame.K_d: 'D',
#                 pygame.K_SPACE: 'SPACE',
#                 pygame.K_RETURN: 'ENTER',
#                 pygame.K_1: '1',
#                 pygame.K_2: '2',
#                 pygame.K_3: '3',
#                 pygame.K_4: '4',
                pygame.K_ESCAPE: "ESC", # used to close window
                pygame.K_DELETE: "DEL"  # ^^
                }
        self.last_msg = None

        self.f_pressed = False
        self.debug = False
        self.new_data = True
        self.data = {
            'lfl': 1500,
            'lfr': 1500,
            'lbl': 1500,
            'lbr': 1500,
            'vfl': 1500,
            'vfr': 1500,
            'vbl': 1500,
            'vbr': 1500,
            'manip': 0.0,
            'manip_rotate': 1500,
            'dome_lights': 0.0,
            'ext_lights': 0.0,
            'camera_x': 1500,
            'camera_y': 1500,
            'pressure_sensor': 1500,
            'esp2_sensor': 1500
        }
        self.data_lock = threading.Lock()


        self.pub = self.create_publisher(String, 'key_states', 10)
        timer_delay = 1.0/30.0 # seconds
        self.timer = self.create_timer(timer_delay, self.timer_callback)
        self.sub_img = self.create_subscription(Image,
                'image_raw',
                self.image_callback,
                1)

        consistent_QoS = QoS.QoSProfile(
                depth=10, 
                reliability=QoS.ReliabilityPolicy.RELIABLE,
                durability=QoS.DurabilityPolicy.VOLATILE
            )
        self.sub_motors = self.create_subscription(
            String, 
            'motor_command', 
            self.motor_callback,
            consistent_QoS
        )
        self.sub_servos = self.create_subscription(
            String, 
            'servo_command', 
            self.servo_callback,
            consistent_QoS
        )
        self.sub_esp1 = self.create_subscription(
            String,
            '/rov/motor_feedback',
            self.sensor_callback,
            consistent_QoS
        )
        self.sub_esp2 = self.create_subscription(
            String,
            '/rov/servo_feedback',
            self.sensor_callback,
            consistent_QoS
        )
        self.sub_img, self.pub, self.sub_img, self.sub_motors, self.sub_servos, self.sub_esp1, self.sub_esp2 # prevent unused variable warnings
        self.reset_screen()
    
    def reset_screen(self):
        self.screen.fill(pygame.Color(255, 255, 255))
        pygame.display.flip()

        instructions = pygame.Surface((self.screen.get_width()-self.max_img_box[0], 20))
#         instructions.fill((200,225,200))
        instructions.fill((255,255,255))
        self.text.reset()
        self.text.indent().set_color((255,0,0))
        self.text.tprintln(instructions, "Press both ESC and delete to exit")
        self.text.set_color((0,0,0)).reset()
        self.screen_updates.append((instructions, (0,0)))
        self.print_ROV()
        with self.data_lock:
            self.new_data = True

    def print_ROV(self):
        wireframe_surface = pygame.Surface((320,275))
#         wireframe_surface.fill((200,200,225))
        wireframe_surface.fill((255,255,255))

        old_x = self.text.get_x()
        old_y = self.text.get_y()
        self.text.set_x(5)
        self.text.set_y(5)

        bar = u"\u203E" * 4
        wireFrame = [u"  /{}/".format(bar),u"   FRONT   ",u"\\{}\\".format(bar),
                u" / 19 /",u"             ",u"\\ 18 \\",
                u"/____/",u"               ",u"\\____\\",
                u"",u"",u"",
                u"|{}|".format(bar),u"               ",u"|{}|".format(bar),
                u"| 17 |",u"               ",u"| 16 |",
                u"|____|",u"               ",u"|____|",
                u"",u"",u"",
                u"|{}|".format(bar),u"               ",u"|{}|".format(bar),
                u"| 04 |",u"               ",u"| 13 |",
                u"|____|",u"               ",u"|____|",
                u"",u"",u"",
                u"\\{}\\".format(bar),u"               ",u"/{}/".format(bar),
                u" \\ 14 \\",u"             ",u"/ 27 /",
                u"  \\____\\",u"    Back   ",u"/____/"
                ]
        wireFrameColor = ["lfl","","lfr",
                "lfl","","lfr",
                "lfl","","lfr",
                "","","",
                "vfl","","vfr",
                "vfl","","vfr",
                "vfl","","vfr",
                "","","",
                "vbl","","vbr",
                "vbl","","vbr",
                "vbl","","vbr",
                "","","",
                "lbl","","lbr",
                "lbl","","lbr",
                "lbl","","lbr",
                ]
        motors = {
            'lfl': 1500,
            'lfr': 1500,
            'lbl': 1500,
            'lbr': 1500,
            'vfl': 1500,
            'vfr': 1500,
            'vbl': 1500,
            'vbr': 1500,
        }
        with self.data_lock:
            for key in self.data:
                if key in motors:
                    motors[key] = self.data[key]

        for index, item in enumerate(wireFrame):
            if wireFrameColor[index] != "":
                self.text.set_color(rov_color(motors[wireFrameColor[index]]))
            else:
                self.text.set_color((0,0,0))

            if (index + 1) % 3 == 0:
                self.text.tprintln(wireframe_surface, item)
            else:
                self.text.tprint(wireframe_surface, item)

        self.text.set_y(old_y)
        self.text.set_x(old_x)
        self.text.set_color((0,0,0))
        self.screen_updates.append((wireframe_surface,(0,self.screen.get_height() - wireframe_surface.get_height())))

    def motor_callback(self, msg):
        new_values = {}
        for pair in msg.data.split(','):
            (motor, value) = pair.split('=')
            new_values[motor] = int(value)
        with self.data_lock:
            self.data.update(new_values)
            self.new_data = True
        self.print_ROV()

    def servo_callback(self, msg):
        new_values = {}
        for pair in msg.data.split(','):
            (servo, value) = pair.split('=')
            new_values[servo] = float(value)
        with self.data_lock:
            self.data.update(new_values)
            self.new_data = True

    def sensor_callback(self, msg):
        new_values = {}
        for pair in msg.data.split(','):
            data = pair.split('=')
            if len(data) == 2:
                (servo, value) = data;
                try:
                    new_values[servo] = float(value)
                except ValueError as e:
                    self.get_logger().error(f"{e}");
                    return
        with self.data_lock:
            self.data.update((k,v) for k,v in new_values.items() if k in self.data)
            self.new_data = True

    def image_callback(self, msg):
        if (msg.encoding == "rgb8") and (self.img_size == (msg.width,msg.height)) and (len(msg.data) == msg.step * msg.height):
            with self.img_lock:
                back_idx = self.front_idx ^ 1

            row_out = msg.width * 3
            if row_out > msg.step:
                return

            if msg.step == row_out:
                self.buffers[back_idx][:msg.height * row_out] = msg.data
            else:
                for y in range(msg.height):
                    self.buffers[back_idx][y*row_out:(y+1)*row_out] = msg.data[y*msg.step:y*msg.step + row_out]

            with self.img_lock:
                self.front_idx = back_idx
                self.new_frame = True

    def timer_callback(self):
        key_changed = False
        capture_frame = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.get_logger().info("Window closed, shutting down")
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    self.debug = not self.debug
                    continue
                elif event.key == pygame.K_RETURN:
                    capture_frame = True
                    continue

                name = self.keymap.get(event.key)
                if (name is not None) and (name not in self.held_keys):
                        self.held_keys.add(name)
                        key_changed = True
            elif event.type == pygame.KEYUP:
                name = self.keymap.get(event.key)
                if name is not None and name in self.held_keys:
                    self.held_keys.remove(name)
                    key_changed = True
            pass

        if "ESC" in self.held_keys and "DEL" in self.held_keys:
            self.running = False
            return

        if key_changed:
            msg = String()
            msg.data = ",".join(self.held_keys) # join(sorted(self.held_keys))
            self.pub.publish(msg)
            self.last_msg = msg
        elif self.last_msg:
            self.pub.publish(self.last_msg)

        with self.data_lock:
            new_data = self.new_data
        if new_data:
            console = pygame.Surface((320,720 - 20 - 275))
#             console.fill((225,200,200))
            console.fill((255,255,255))
            self.text.reset().set_color((0,0,0))
            self.text.set_y(10)
            with self.data_lock:
                for key, value in self.data.items():
                    self.text.tprint(console, f"{key}: ")
                    self.text.tprintln(console, str(value))
                self.new_data = False

            self.screen_updates.append((console, (0,20)))


        with self.img_lock:
            new_frame = self.new_frame
            if new_frame:
                img_surface = self.img_surfaces[self.front_idx]
                self.new_frame = False
            if capture_frame:
                filename = self.img_dir + 'crab' + str(self.img_num) + '.jpeg'
                pygame.image.save(self.img_surfaces[self.front_idx], filename)
                self.img_num += 1
                self.get_logger().info(f'Saving image to: {filename}')

        if new_frame:
            scaled = pygame.transform.scale(img_surface, self.img_box_size)

            img_box = pygame.Surface(self.max_img_box)
            img_box.fill((150,150,150))
            self.screen_updates.append((img_box, (self.screen.get_width()-img_box.get_width(),0)))

            self.screen_updates.append((scaled, (  self.screen.get_width()-scaled.get_width(),  0)))
#             self.screen_updates.append(self.screen.blit(img_surface, (100,100)))

        if not self.f_pressed and 'F' in self.held_keys:
            self.fullscreen = not self.fullscreen
            if not self.fullscreen:
                self.screen = pygame.display.set_mode((1280,720), flags=pygame.SCALED)
#                 self.screen = pygame.display.set_mode((640,360), flags=pygame.SCALED)
            else:
                pygame.display.toggle_fullscreen()
            self.reset_screen()
            self.f_pressed = True
        elif self.f_pressed and 'F' not in self.held_keys:
            self.f_pressed = False

        updated_rects = self.screen.blits(blit_sequence=self.screen_updates, doreturn=True)
        pygame.display.update(updated_rects)
        self.screen_updates = []

    def destroy_node(self):
        pygame.quit()
        super().destroy_node()


def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = Window()

    try:
        while rclpy.ok() and node.running:
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
