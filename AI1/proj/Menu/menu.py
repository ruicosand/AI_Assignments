import pygame 
from Menu.background import Background

class Button: 
    def __init__(self, pos_x, pos_y, width, height, color):
        self.x = pos_x
        self.y = pos_y
        self.width = width
        self.height = height
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))




class Menu: 
    def __init__(self, screen_width, scree_height):
        self.background = Background(screen_width, scree_height)
        self.button = Button(40,40,100,40,(0,255,255))

    def update(self):
        self.background.update()

    def draw(self, surface):
        self.background.draw(surface)
        self.button.draw(surface)

    def handle_click(self,mouse_pos):
            rect = pygame.Rect(self.button.x, self.button.y, self.button.width, self.button.height)
            return rect.collidepoint(mouse_pos)
        

