# -*- coding: utf-8 -*-
"""
Optimized code for displaying a controller image with:
 • Sector-based filling for D-Pad and joysticks
 • Button highlights
 • A scaled Pygame window
 • A 3×3 grid at the bottom showing joystick x/y values 
   (from Logiteck_Gamepad_F310)
Compatible with Python 2.7.
"""

import pygame, sys, math
from PIL import Image, ImageDraw  # type: ignore
from Logiteck_Gamepad_F310 import gamepad  # PyQt-based gamepad module

# SECTION: GLOBAL STATE
# Boolean flags for button/trigger/bumper presses
a_pressed = x_pressed = y_pressed = b_pressed = False
left_trigger_active = right_trigger_active = False
left_bumper_active = right_bumper_active = False
start_pressed = back_pressed = False
# For D-Pad and joystick directional fill (sector indices 0-7)
dpad_sector = left_js_sector = right_js_sector = None
# Joystick click states
left_js_click_pressed = right_js_click_pressed = False
# Raw joystick axis positions (as read from gamepad, where up is negative)
left_js_x = left_js_y = 0.0
right_js_x = right_js_y = 0.0

# SECTION: DRAWING HELPERS
def draw_thick_arc(draw_obj, center, radius, start, end, outline="black", thickness=3):
    """Draw multiple arcs to simulate a thick outline."""
    cx, cy = center
    for offset in range(thickness):
        r = radius + offset
        bbox = (cx - r, cy - r, cx + r, cy + r)
        draw_obj.arc(bbox, start=start, end=end, fill=outline)

def draw_8_direction_arcs(draw_obj, bbox, outline="black", thickness=3):
    """Divide the circle (bbox) into 8 equal 45° arcs and draw their outlines."""
    x1, y1, x2, y2 = bbox
    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    r = min((x2 - x1) / 2.0, (y2 - y1) / 2.0)
    for i in range(8):
        draw_thick_arc(draw_obj, (cx, cy), r, i * 45, (i + 1) * 45, outline, thickness)

def draw_thick_ellipse(draw_obj, bbox, outline="black", thickness=3):
    """Draw an ellipse with a thick outline."""
    for offset in range(thickness):
        ex1 = bbox[0] - offset
        ey1 = bbox[1] - offset
        ex2 = bbox[2] + offset
        ey2 = bbox[3] + offset
        draw_obj.ellipse((ex1, ey1, ex2, ey2), outline=outline)

def draw_top_half_rounded_rectangle(draw_obj, xy, radius, outline="black", thickness=3, cutoff_ratio=0.5):
    """Draw only the top half of a rounded rectangle outline."""
    x1, y1, x2, y2 = xy
    cut_y = y1 + int((y2 - y1) * cutoff_ratio)
    for offset in range(thickness):
        ex1, ey1 = x1 - offset, y1 - offset
        ex2, er = x2 + offset, radius + offset
        draw_obj.line((ex1 + er, ey1, ex2 - er, ey1), fill=outline)
        draw_obj.arc((ex1, ey1, ex1 + 2 * er, ey1 + 2 * er), start=180, end=270, fill=outline)
        draw_obj.arc((ex2 - 2 * er, ey1, ex2, ey1 + 2 * er), start=270, end=360, fill=outline)
        draw_obj.line((ex1, ey1 + er, ex1, cut_y), fill=outline)
        draw_obj.line((ex2, ey1 + er, ex2, cut_y), fill=outline)

def draw_thick_rectangle(draw_obj, bbox, outline="black", thickness=3):
    """Draw a rectangle with a thick outline."""
    x1, y1, x2, y2 = bbox
    for offset in range(thickness):
        draw_obj.rectangle((x1 - offset, y1 - offset, x2 + offset, y2 + offset), outline=outline)

def get_sector_from_angle(angle):
    """Map an angle (0–360) to a sector index (0–7)."""
    angle %= 360
    if angle < 22.5 or angle >= 337.5:
        return 0  # Right
    elif angle < 67.5:
        return 1  # Top Right
    elif angle < 112.5:
        return 2  # Top
    elif angle < 157.5:
        return 3  # Top Left
    elif angle < 202.5:
        return 4  # Left
    elif angle < 247.5:
        return 5  # Bottom Left
    elif angle < 292.5:
        return 6  # Bottom
    else:
        return 7  # Bottom Right

def sector_to_angles(sector):
    """Return the (start, end) angles for a given sector (0–7)."""
    mapping = {
        0: (337.5, 22.5),
        1: (22.5, 67.5),
        2: (67.5, 112.5),
        3: (112.5, 157.5),
        4: (157.5, 202.5),
        5: (202.5, 247.5),
        6: (247.5, 292.5),
        7: (292.5, 337.5)
    }
    return mapping.get(sector, (0, 0))

def fill_sector(draw_obj, bbox, sector, fill="#006400"):
    """Fill one 45° sector of an ellipse (bbox) with the specified fill color."""
    start, end = sector_to_angles(sector)
    if end < start:
        end += 360
    draw_obj.pieslice(bbox, start, end, fill=fill)

# SECTION: BASE IMAGE & DRAW UPDATE
image_path = r"~/Underwater-Robotics-24-25/gavins-code/controller.png"
base_image = Image.open(image_path).convert('RGBA')

def update_drawing():
    """Create a new PIL image reflecting current gamepad state."""
    global a_pressed, x_pressed, y_pressed, b_pressed, left_trigger_active, right_trigger_active
    global left_bumper_active, right_bumper_active, start_pressed, back_pressed
    global dpad_sector, left_js_sector, right_js_sector, left_js_click_pressed, right_js_click_pressed

    img = base_image.copy()
    draw_obj = ImageDraw.Draw(img)

    # Fill sectors for directional controls:
    if dpad_sector is not None:
        fill_sector(draw_obj, (80, 65, 175, 155), dpad_sector)
    if left_js_sector is not None:
        fill_sector(draw_obj, (130, 165, 200, 232), left_js_sector)
    if right_js_sector is not None:
        fill_sector(draw_obj, (278, 165, 350, 232), right_js_sector)

    # Fill on/off buttons:
    if left_trigger_active:
        draw_obj.rectangle((92, 6, 116, 35), fill="#006400")
    if right_trigger_active:
        draw_obj.rectangle((365, 6, 389, 35), fill="#006400")
    if left_bumper_active:
        draw_obj.rectangle((116, 1, 177, 35), fill="#006400")
    if right_bumper_active:
        draw_obj.rectangle((304, 1, 365, 35), fill="#006400")
    if y_pressed:
        draw_obj.ellipse((335, 52, 370, 87), fill="#006400")
    if b_pressed:
        draw_obj.ellipse((373, 89, 407, 124), fill="#006400")
    if x_pressed:
        draw_obj.ellipse((298, 89, 330, 124), fill="#006400")
    if a_pressed:
        draw_obj.ellipse((335, 122, 370, 157), fill="#006400")
    if start_pressed:
        draw_obj.ellipse((252, 89, 270, 99), fill="#006400")
    if back_pressed:
        draw_obj.ellipse((208, 89, 226, 99), fill="#006400")

    # Draw joystick dead-center circles:
    left_center = ((130 + 200) / 2.0, (165 + 232) / 2.0); r = 9
    left_bbox = (left_center[0] - r, left_center[1] - r, left_center[0] + r, left_center[1] + r)
    if left_js_click_pressed:
        draw_obj.ellipse(left_bbox, fill="#006400")
    draw_thick_ellipse(draw_obj, left_bbox, outline="black", thickness=2)

    right_center = ((278 + 350) / 2.0, (165 + 232) / 2.0)
    right_bbox = (right_center[0] - r, right_center[1] - r, right_center[0] + r, right_center[1] + r)
    if right_js_click_pressed:
        draw_obj.ellipse(right_bbox, fill="#006400")
    draw_thick_ellipse(draw_obj, right_bbox, outline="black", thickness=2)

    # Redraw outlines for all controls:
    draw_top_half_rounded_rectangle(draw_obj, (92, 6, 116, 35), 10)
    draw_top_half_rounded_rectangle(draw_obj, (365, 6, 389, 35), 10)
    draw_top_half_rounded_rectangle(draw_obj, (116, 1, 177, 35), 8)
    draw_top_half_rounded_rectangle(draw_obj, (304, 1, 365, 35), 8)
    draw_8_direction_arcs(draw_obj, (80, 65, 175, 155))
    draw_8_direction_arcs(draw_obj, (130, 165, 200, 232))
    draw_8_direction_arcs(draw_obj, (278, 165, 350, 232))
    draw_thick_ellipse(draw_obj, (335, 52, 370, 87))
    draw_thick_ellipse(draw_obj, (373, 89, 407, 124))
    draw_thick_ellipse(draw_obj, (298, 89, 330, 124))
    draw_thick_ellipse(draw_obj, (335, 122, 370, 157))
    draw_thick_ellipse(draw_obj, (252, 89, 270, 99))
    draw_thick_ellipse(draw_obj, (208, 89, 226, 99))

    return img

# SECTION: PYGAME SETUP & MAIN LOOP
pygame.init()
SCALE_FACTOR = 0.5
w, h = base_image.size
screen = pygame.display.set_mode((int(w * SCALE_FACTOR), int(h * SCALE_FACTOR)))
pygame.display.set_caption("Controller")
clock = pygame.time.Clock()

def poll_gamepad_state():
    """Read gamepad state and update global variables."""
    global a_pressed, x_pressed, y_pressed, b_pressed
    global left_trigger_active, right_trigger_active, left_bumper_active, right_bumper_active
    global start_pressed, back_pressed, dpad_sector, left_js_sector, right_js_sector
    global left_js_click_pressed, right_js_click_pressed, left_js_x, left_js_y, right_js_x, right_js_y

    if gamepad.pad:
        # Face buttons: X=0, A=1, B=2, Y=3
        a_pressed = bool(gamepad.pad.get_button(1))
        x_pressed = bool(gamepad.pad.get_button(0))
        b_pressed = bool(gamepad.pad.get_button(2))
        y_pressed = bool(gamepad.pad.get_button(3))
        # Triggers and bumpers:
        left_trigger_active  = bool(gamepad.pad.get_button(6))
        right_trigger_active = bool(gamepad.pad.get_button(7))
        left_bumper_active   = bool(gamepad.pad.get_button(4))
        right_bumper_active  = bool(gamepad.pad.get_button(5))
        # Start and Back:
        back_pressed  = bool(gamepad.pad.get_button(8))
        start_pressed = bool(gamepad.pad.get_button(9))
        # D-Pad (invert y-axis for correct orientation):
        hat = gamepad.pad.get_hat(0)
        hat_inverted = (hat[0], -hat[1])
        if hat_inverted != (0, 0):
            mapping = {(0,1):90, (1,1):45, (1,0):0, (1,-1):315,
                       (0,-1):270, (-1,-1):225, (-1,0):180, (-1,1):135}
            ang = mapping.get(hat_inverted, None)
            dpad_sector = get_sector_from_angle(ang) if ang is not None else None
        else:
            dpad_sector = None

        # Joysticks:
        dz = 0.2
        lx, ly = gamepad.pad.get_axis(0), gamepad.pad.get_axis(1)
        # Store raw axes (for grid display, where up is negative)
        left_js_x, left_js_y = lx, ly
        # For sector calculation, use the raw value (without additional inversion)
        if abs(lx) > dz or abs(ly) > dz:
            left_js_sector = get_sector_from_angle(math.degrees(math.atan2(ly, lx)) % 360)
        else:
            left_js_sector = None

        rx, ry = gamepad.pad.get_axis(2), gamepad.pad.get_axis(3)
        right_js_x, right_js_y = rx, ry
        if abs(rx) > dz or abs(ry) > dz:
            right_js_sector = get_sector_from_angle(math.degrees(math.atan2(ry, rx)) % 360)
        else:
            right_js_sector = None

        # Joystick clicks:
        left_js_click_pressed = bool(gamepad.pad.get_button(10))
        right_js_click_pressed = bool(gamepad.pad.get_button(11))

# SECTION: DRAW JOYSTICK GRID (BOTTOM CENTER)
font = pygame.font.SysFont("Arial", 14)
def draw_bottom_grid(surface):
    # 3x3 grid: each cell 60x12.5 px; total 180x37.5, centered at bottom.
    total_w, total_h = 180, 37.5
    cell_w, cell_h = 60, 12.5
    anchor_x = (surface.get_width() - total_w) // 2
    anchor_y = surface.get_height() - total_h
    grid_text = [
        ["", "L-Joystick", "R-Joystick"],
        ["X", "{:.2f}".format(left_js_x), "{:.2f}".format(right_js_x)],
        ["Y", "{:.2f}".format(-left_js_y), "{:.2f}".format(-right_js_y)]
    ]
    # Note: For grid display, we show -y so that pushing up (raw negative) appears positive.
    for row in range(3):
        for col in range(3):
            cell_x = anchor_x + col * cell_w
            cell_y = anchor_y + row * cell_h
            pygame.draw.rect(surface, (180,180,180), (cell_x, cell_y, cell_w, cell_h), 1)
            text_img = font.render(grid_text[row][col], True, (0,0,0))
            tx = cell_x + (cell_w - text_img.get_width()) // 2
            ty = cell_y + (cell_h - text_img.get_height()) // 2
            surface.blit(text_img, (tx, ty))

# SECTION: MAIN LOOP
pygame.init()
sw, sh = int(w * SCALE_FACTOR), int(h * SCALE_FACTOR)
screen = pygame.display.set_mode((int(w * SCALE_FACTOR), int(h * SCALE_FACTOR)))
pygame.display.set_caption("Controller & Joystick Grid")
clock = pygame.time.Clock()

running = True
while running:
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False

    poll_gamepad_state()
    pil_img = update_drawing()
    data = pil_img.tobytes()
    pg_img = pygame.image.fromstring(data, pil_img.size, pil_img.mode)
    scaled_img = pygame.transform.scale(pg_img, (int(w * SCALE_FACTOR), int(h * SCALE_FACTOR)))
    screen.fill((220,220,220))
    screen.blit(scaled_img, (0, 0))
    draw_bottom_grid(screen)
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
