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
        self.button1 = Button(40,40,100,40,(0,255,255))
        self.button2 = Button(40,40 + 40 + 20,100,40,(0,255,255))


    def update(self):
        self.background.update()

    def draw(self, surface):
        self.background.draw(surface)
        self.button1.draw(surface)
        self.button2.draw(surface)

    def handle_click(self,mouse_pos):
            rect1 = pygame.Rect(self.button1.x, self.button1.y, self.button1.width, self.button1.height)
            rect2 = pygame.Rect(self.button2.x, self.button2.y, self.button2.width, self.button2.height)

            if rect1.collidepoint(mouse_pos):
                return 1
            
            elif rect2.collidepoint(mouse_pos):
                return 2 

            else: 
                return 3

