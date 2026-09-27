# -*- coding: utf-8 -*-
import pygame  # type: ignore
import sys
import os
from PyQt4.QtCore import QCoreApplication  # type: ignore

# Place the Pygame window in the center of the screen
os.environ["SDL_VIDEO_CENTERED"] = "1"

# Attempt to initialize Pygame
try:
    pygame.init()
    pygame.event.get() 
except Exception as e:
    print("Pygame Initialization Failed:", e)
    sys.exit(1)

# Screen dimensions
WIDTH, HEIGHT = 500, 500

# Set up the Pygame display and allow resizing
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)  # Allow resizing
    pygame.display.set_caption("ROV Controller Mapping")
except Exception as e:
    print("Failed to initialize display:", e)
    sys.exit(1)

# Load the watermark image and scale it to fit the screen
# Using escaped backslashes:
watermark_path = "~/Underwater-Robotics-24-25/gavins-code/watermark.png"
try:
    background = pygame.image.load(watermark_path)
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))  # Scale to fit the screen
    print("Watermark loaded successfully!")
    expand_x = 400 
    expand_y = 0   
    bg_width = WIDTH + expand_x
    bg_height = HEIGHT + expand_y
    background = pygame.transform.scale(background, (bg_width, bg_height))
    print("Background re-scaled to:", bg_width, "x", bg_height)
    
except Exception as e:
    print("Failed to load background image:", e)
    background = None  # Prevent crashes if the image fails to load
    
# Basic colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Main box properties
box_x, box_y = 200, 200
box_width, box_height = 100, 100

# Set up dimensions for the outer and side boxes
outer_box_width = 40
outer_box_height = 60

# Define the positions and angles for rotated and side boxes
rotated_boxes = [
    (box_x + 90, box_y + 110, outer_box_height, outer_box_width, -45),   # Top Right
    (box_x + 90, box_y - 50, outer_box_height, outer_box_width, 45),    # Bottom Right
    (box_x - 50, box_y + 110, outer_box_height, outer_box_width, 45),   # Top Left
    (box_x - 50, box_y - 50, outer_box_height, outer_box_width, -45),   # Bottom Left
    (box_x - 80, box_y + 10, 60, 30, 0),                                # Left Upper Box
    (box_x - 80, box_y + 50, 60, 30, 0),                                # Left Lower Box
    (box_x + 120, box_y + 10, 60, 30, 0),                               # Right Upper Box
    (box_x + 120, box_y + 50, 60, 30, 0),                               # Right Lower Box
]

# Initialize box colors
box_colors = [BLUE] * len(rotated_boxes)

# Function to draw a rotated rectangle onto the Pygame surface
def draw_rotated_rect(surface, color, rect, angle):
    rect_surface = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    rect_surface.fill(color)
    rotated_surface = pygame.transform.rotate(rect_surface, angle)
    new_rect = rotated_surface.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2))
    surface.blit(rotated_surface, new_rect.topleft)

# Import the gamepad module if available
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from Logiteck_Gamepad_F310 import gamepad  # type: ignore
except Exception as e:
    print("Gamepad Initialization Failed:", e)
    gamepad = None  

# Handlers for gamepad signals
def handle_right_stick_up():
    global box_colors
    print("[Right Stick] Moving Forwards")
    box_colors = [GREEN, GREEN, GREEN, GREEN, BLUE, BLUE, BLUE, BLUE]
    if gamepad and gamepad.pad and gamepad.pad.get_button(8):  
        print("[Back Button] Going Up")
        box_colors[4] = GREEN  
        box_colors[5] = GREEN  
        box_colors[6] = GREEN  
        box_colors[7] = GREEN  
        box_colors[0] = BLUE  
        box_colors[1] = BLUE  
        box_colors[2] = BLUE  
        box_colors[3] = BLUE
        if gamepad.pad.get_button(11):
            print("[Back + Right Stick Click] Pitching Forwards")
            box_colors[4] = RED   # Left Upper Box (Front)
            box_colors[6] = RED   # Right Upper Box (Front)
            box_colors[5] = GREEN # Left Lower Box (Back)
            box_colors[7] = GREEN # Right Lower Box (Back)
        
def handle_right_stick_down():
    global box_colors
    print("[Right Stick] Moving Backwards")
    box_colors = [RED, RED, RED, RED, BLUE, BLUE, BLUE, BLUE]
    if gamepad and gamepad.pad and gamepad.pad.get_button(8):  # Button 8 is Back
        print("[Back Button] Going Down")
        box_colors[4] = RED  
        box_colors[5] = RED  
        box_colors[6] = RED  
        box_colors[7] = RED  
        box_colors[0] = BLUE  
        box_colors[1] = BLUE  
        box_colors[2] = BLUE  
        box_colors[3] = BLUE
        if gamepad.pad.get_button(11):
            print("[Back + Right Stick Click] Pitching Backwards")
            box_colors[4] = GREEN   # Left Upper Box (Front)
            box_colors[6] = GREEN   # Right Upper Box (Front)
            box_colors[5] = RED     # Left Lower Box (Back)
            box_colors[7] = RED     # Right Lower Box (Back)

def handle_right_stick_down_right():
    global box_colors
    print("[Right Stick] Moving Backwards")
    box_colors = [RED, RED, RED, RED, BLUE, BLUE, BLUE, BLUE]  # Keep middle side boxes blue
    if gamepad.pad.get_button(11):
        print("[Right Stick Click] Moving Down Right")
        box_colors[3] = BLUE  
        box_colors[0] = BLUE  
    if gamepad and gamepad.pad and gamepad.pad.get_button(8):  
        print("[Back Button] Pressed - Going Down")
        box_colors[4] = RED  
        box_colors[5] = RED  
        box_colors[6] = RED  
        box_colors[7] = RED  
        box_colors[0] = BLUE  
        box_colors[1] = BLUE  
        box_colors[2] = BLUE  
        box_colors[3] = BLUE
        
def handle_right_stick_down_left():
    global box_colors
    print("[Right Stick] Moving Backwards")
    box_colors = [RED, RED, RED, RED, BLUE, BLUE, BLUE, BLUE]  
    if gamepad.pad.get_button(11):
        print("[Right Stick Click] Moving Down Left")
        box_colors[2] = BLUE  
        box_colors[1] = BLUE  
    elif gamepad and gamepad.pad and gamepad.pad.get_button(8):
        print("[Back Button] Going Down")
        box_colors[4] = RED  
        box_colors[5] = RED  
        box_colors[6] = RED  
        box_colors[7] = RED  
        box_colors[0] = BLUE  
        box_colors[1] = BLUE  
        box_colors[2] = BLUE  
        box_colors[3] = BLUE

def handle_right_stick_left():
    global box_colors
    print("[Right Stick] Rotating Left")
    box_colors = [GREEN, GREEN, RED, RED, BLUE, BLUE, BLUE, BLUE]  
    if gamepad.pad.get_button(11):
        print("[Right Stick Click] Drift Left")
        box_colors[0] = RED  
        box_colors[2] = GREEN
    if gamepad and gamepad.pad and gamepad.pad.get_button(8):
        print("[Back Button] Pitching Leftwards")
        box_colors[4] = RED  
        box_colors[5] = RED  
        box_colors[6] = GREEN  
        box_colors[7] = GREEN  
        box_colors[0] = BLUE  
        box_colors[1] = BLUE  
        box_colors[2] = BLUE  
        box_colors[3] = BLUE 
        
def handle_right_stick_top_left():
    global box_colors
    print("[Right Stick] Rotating Left")
    box_colors = [GREEN, GREEN, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE]  
    if gamepad.pad.get_button(11):
        print("[Right Stick Click] Moving Top Left")
        box_colors[0] = BLUE  
        box_colors[2] = GREEN  
    if gamepad and gamepad.pad and gamepad.pad.get_button(8):
        print("[Back Button] Goining Up")
        box_colors[4] = GREEN  
        box_colors[5] = GREEN  
        box_colors[6] = GREEN  
        box_colors[7] = GREEN  
        box_colors[0] = BLUE  
        box_colors[1] = BLUE  
        box_colors[2] = BLUE  
        box_colors[3] = BLUE
            
def handle_right_stick_right():
    global box_colors
    print("[Right Stick] Rotating Right")
    box_colors = [RED, RED, GREEN, GREEN, BLUE, BLUE, BLUE, BLUE]  
    if gamepad.pad.get_button(11):
        print("[Right Stick Click] Drift Right")
        box_colors[2] = RED  
        box_colors[0] = GREEN
    if gamepad and gamepad.pad and gamepad.pad.get_button(8):
        print("[Back Button] Pitching Rightwards")
        box_colors[4] = GREEN  
        box_colors[5] = GREEN  
        box_colors[6] = RED  
        box_colors[7] = RED  
        box_colors[0] = BLUE  
        box_colors[1] = BLUE  
        box_colors[2] = BLUE  
        box_colors[3] = BLUE  
        
def handle_right_stick_top_right():
    global box_colors
    print("[Right Stick] Rotating Right")
    box_colors = [BLUE, BLUE, GREEN, GREEN, BLUE, BLUE, BLUE, BLUE]  
    if gamepad.pad.get_button(11):
        print("[Right Stick Click] Moving Top Right")
        box_colors[2] = BLUE  
        box_colors[0] = GREEN  
    if gamepad and gamepad.pad and gamepad.pad.get_button(8):
        print("[Back Button] Going Up")
        box_colors[4] = GREEN  
        box_colors[5] = GREEN  
        box_colors[6] = GREEN  
        box_colors[7] = GREEN  
        box_colors[0] = BLUE  
        box_colors[1] = BLUE  
        box_colors[2] = BLUE  
        box_colors[3] = BLUE
        
def handle_right_stick_idle():
    """Reset colors to default if the joystick is neutral."""
    global box_colors
    if box_colors != [BLUE] * len(rotated_boxes):
        print("[Right Stick] Idle")
        box_colors = [BLUE] * len(rotated_boxes)

# Connect Gamepad Signals (Only if a gamepad is detected)
if gamepad:
    gamepad.RStickUpSignal.connect(handle_right_stick_up)
    gamepad.RStickDownSignal.connect(handle_right_stick_down)
    gamepad.RStickBottomRightSignal.connect(handle_right_stick_down_right)
    gamepad.RStickBottomLeftSignal.connect(handle_right_stick_down_left)
    gamepad.RStickLeftSignal.connect(handle_right_stick_left)
    gamepad.RStickTopLeftSignal.connect(handle_right_stick_top_left)
    gamepad.RStickRightSignal.connect(handle_right_stick_right)
    gamepad.RStickTopRightSignal.connect(handle_right_stick_top_right)
    gamepad.RStickIdleSignal.connect(handle_right_stick_idle)

print("Game loop started. Waiting for events...")

# Draw a test circle on the screen before entering the main loop
screen.fill(BLACK)
# Updated Pygame Setup & Main Loop with scaling
SCALE_FACTOR = 0.45
# Create a drawing surface at the original resolution
draw_surface = pygame.Surface((WIDTH, HEIGHT))
# Set the display window size to the scaled dimensions
screen = pygame.display.set_mode((int(WIDTH * SCALE_FACTOR), int(HEIGHT * SCALE_FACTOR)), pygame.RESIZABLE)
pygame.display.set_caption("ROV Controller Mapping (Scaled)")
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Draw everything on the offscreen draw_surface
    if background:
        draw_surface.blit(background, (-97.5, 25))  # Use original coordinates
    else:
        draw_surface.fill(BLACK)
    # Draw rotated boxes and central box onto draw_surface
    for i, (bx, by, bw, bh, angle) in enumerate(rotated_boxes):
        draw_rotated_rect(draw_surface, box_colors[i], (bx, by, bw, bh), angle)
    pygame.draw.rect(draw_surface, BLUE, (box_x, box_y, box_width, box_height))

    # Scale the entire draw_surface to the display size
    scaled_surface = pygame.transform.scale(draw_surface, (int(WIDTH * SCALE_FACTOR), int(HEIGHT * SCALE_FACTOR)))
    screen.fill((0, 0, 0))
    screen.blit(scaled_surface, (0, 0))
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
