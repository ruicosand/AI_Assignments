import pygame 

from Menu.background import Background
from Menu.menu import Button


class SolverMenu: 
    def __init__(self, screen_width, scree_height):
        self.background = Background(screen_width, scree_height)
        self.button1 = Button(40,40,100,40,(0,255,0))
        self.button2 = Button(40,40 + 40 + 20,100,40,(0,255,0))
        self.button3 = Button(40,40 + 80 + 40,100,40,(0,255,0))


    def update(self):
        self.background.update()

    def draw(self, surface):
        self.background.draw(surface)
        self.button1.draw(surface)
        self.button2.draw(surface)
        self.button3.draw(surface)

    def handle_click(self,mouse_pos):
            rect1 = pygame.Rect(self.button1.x, self.button1.y, self.button1.width, self.button1.height)
            rect2 = pygame.Rect(self.button2.x, self.button2.y, self.button2.width, self.button2.height)
            rect3 = pygame.Rect(self.button3.x, self.button3.y, self.button3.width, self.button3.height)

            if rect1.collidepoint(mouse_pos):
                return 1
            
            elif rect2.collidepoint(mouse_pos):
                return 2 

            elif rect3.collidepoint(mouse_pos): 
                return 3

            else: return 0

