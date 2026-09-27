#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rospy
from std_msgs.msg import String
import pygame
import json
import threading

class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.SysFont('DejaVu Sans Mono', 20)

    def tprintln(self, screen, text):
        self.tprint(screen, text)
        self.y += self.line_height
        self.x_offset = 0;

    def tprint(self, screen, text):
        text_bitmap = self.font.render(text, True, self.color)
        screen.blit(text_bitmap, (self.x + self.x_offset, self.y))
        self.x_offset += text_bitmap.get_width()

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 22
        self.x_offset = 0
        self.color = (0,0,0)

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def set_x(self, new_x):
        self.x = new_x

    def set_y(self, new_y):
        self.y = new_y

    def set_color(self, new_color):
        self.color = new_color

debug = False
data = {
        'lfl': "0.0",
        'lfr': "0.0",
        'lbl': "0.0",
        'lbr': "0.0",
        'vfl': "0.0",
        'vfr': "0.0",
        'vbl': "0.0",
        'vbr': "0.0",
        'main_manip': "1.0",
        'left_manip': "0.0",
        'top_manip': "-1.0",
        'main_mover': "0.0",
        'left_mover': "0.0",
        'lights': "0.0",
        'camera_x': "0.0",
        'camera_y': "0.0"
        }

data_lock = threading.Lock()

def ros_spin():
    rospy.spin()

def callback(msg):
    global data
    commands = msg.data.strip()

    command_list = commands.split("\n")
    with data_lock:
        for command in command_list:
            command = command.strip().split(" ")
            data[command[0]] = command[1]

def rov_color(speed):
    speed = float(speed)
    if (speed == 1500) or (speed == 0):
        return (0,0,0)
    elif speed > 1500:
        return (0,255,0)
    else:
        return (255,0,0)


def print_ROV(text_print, screen):
    global data
    old_x = text_print.get_x()
    old_y = text_print.get_y()
    text_print.set_x(1575)
    text_print.set_y(600)

    bar = u"\u203E" * 4
    wireFrame = [u"  /{}/".format(bar),u"   FRONT   ",u"\\{}\\".format(bar),
            u" / 13 /",u"             ",u"\\ 12 \\",
            u"/____/",u"               ",u"\\____\\",
            u"",u"",u"",
            u"|{}|".format(bar),u"               ",u"|{}|".format(bar),
            u"| ## |",u"               ",u"| ## |",
            u"|____|",u"               ",u"|____|",
            u"",u"",u"",
            u"|{}|".format(bar),u"               ",u"|{}|".format(bar),
            u"| ## |",u"               ",u"| ## |",
            u"|____|",u"               ",u"|____|",
            u"",u"",u"",
            u"\\{}\\".format(bar),u"               ",u"/{}/".format(bar),
            u" \\ 09 \\",u"             ",u"/ 08 /",
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
    for index, item in enumerate(wireFrame):
        if wireFrameColor[index] != "":
            text_print.set_color(rov_color(data[wireFrameColor[index]]))
        else:
            text_print.set_color((0,0,0))

        if (index + 1) % 3 == 0:
            text_print.tprintln(screen, item)
        else:
            text_print.tprint(screen, item)

    text_print.set_y(old_y)
    text_print.set_x(old_x)
    text_print.set_color((0,0,0))

def main():
    heartbeat = 0;
    global debug
    rospy.init_node('pygame_key_publisher')
    pub = rospy.Publisher('key_states', String, queue_size=10)
    rospy.Subscriber('motor_command', String, callback)

    spin_thread = threading.Thread(target=ros_spin)
    spin_thread.daemon = True
    spin_thread.start()

    pygame.init()
    fullscreen = rospy.get_param('~fullscreen', False)
    if fullscreen:
        screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((200,200))
    pygame.display.set_caption("Keyboard Listener")
    pygame.mouse.set_visible(True)

    clock = pygame.time.Clock()
    held_keys = set()

    keymap = {
            pygame.K_UP: 'UP',
            pygame.K_DOWN: 'DOWN',
            pygame.K_LEFT: 'LEFT',
            pygame.K_RIGHT: 'RIGHT',
            pygame.K_LEFTBRACKET: "[",
            pygame.K_RIGHTBRACKET: "]",
            pygame.K_w: 'W',
            pygame.K_a: 'A',
            pygame.K_s: 'S',
            pygame.K_d: 'D',
            pygame.K_SPACE: 'SPACE',
            pygame.K_RETURN: 'ENTER',
            pygame.K_1: '1',
            pygame.K_2: '2',
            pygame.K_3: '3',
            pygame.K_4: '4'
            }

    text_print = TextPrint()

    running = True
    while (not rospy.is_shutdown()) and running:
        pygame.event.pump()
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                rospy.signal_shutdown('Window closed')
            elif event.type == pygame.KEYDOWN:
                if event.key in keymap:
                    held_keys.add(keymap[event.key])
                elif event.key == pygame.K_LSHIFT:
                    debug = not debug
            elif event.type == pygame.KEYUP:
                if event.key in keymap and keymap[event.key] in held_keys:
                    held_keys.remove(keymap[event.key])
            pass
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE] and keys[pygame.K_DELETE]:
            running = False

        # Publish as JSON string
        pub.publish(json.dumps(sorted(list(held_keys))))

        screen.fill(pygame.Color(255, 255, 255))
        text_print.reset()


        text_print.indent()
        text_print.set_color((255,0,0))
        text_print.tprintln(screen, "Press both ESC and delete to exit")

        text_print.set_color((0,0,0))
        global data;
        if debug:
            with data_lock:
                for key, value in data.items():
                    text_print.tprint(screen, "{}: ".format(key))
                    text_print.tprintln(screen, value)
        print_ROV(text_print, screen)
        text_print.set_y(600);
        text_print.unindent();
        text_print.tprint(screen, str(heartbeat % 10));

        pygame.display.flip()

        heartbeat += 1
        clock.tick(30)  # Limit to 30 FPS

    pygame.quit()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
