import pygame

class TextPrint:
    def __init__(self):
        self.reset()
        self._font = pygame.font.SysFont('DejaVu Sans Mono', 15)

    def tprintln(self, screen, text):
        self.tprint(screen, text)
        self._y += self._line_height
        self._x_offset = 0
        return self

    def tprint(self, screen, text):
        text_bitmap = self._font.render(text, True, self.color)
        screen.blit(text_bitmap, (self._x + self._x_offset, self._y))
        self._x_offset += text_bitmap.get_width()
        return self

    def reset(self):
        self._x = 5
        self._y = 0
        self._line_height = 17
        self._x_offset = 0
        self.color = (0,0,0)
        return self

    def indent(self):
        self._x += 5
        return self
    
    def unindent(self):
        self._x -= 5
        return self
    
    def get_x(self):
        return self._x
    
    def get_y(self):
        return self._y

    def set_x(self, new_x):
        self._x = new_x
        return self

    def set_y(self, new_y):
        self._y = new_y
        return self

    def set_color(self, new_color):
        self.color = new_color
        return self
