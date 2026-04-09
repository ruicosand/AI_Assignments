import pygame 
import ast
from game_logic import GameController
from waterSort import WaterSort
from Menu.background import Background
from solver import Solver
from Menu.menu import Button


class levelMenu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.background = Background(width, height)
        self.easy = Button(width / 2, 100, 180, 40, (255,0,255))
        self.medium = Button(width / 2, 300 , 180, 40, (255,0,255))
        self.hard = Button(width / 2, height - 200, 180, 40, (255,0,255))
        self.font = pygame.font.SysFont(None, 30)


    def draw(self,surface):
        self.background.draw(surface)
        self.easy.draw(surface)
        self.medium.draw(surface)
        self.hard.draw(surface)

        easy_text = self.font.render("Easy", True, (0, 0, 0))
        medium_text = self.font.render("Medium", True, (0, 0, 0))
        hard_text = self.font.render("Hard", True, (0, 0, 0))

        surface.blit(easy_text, (self.width / 2 + 60, 112))
        surface.blit(medium_text, (self.width / 2 + 45, 312))
        surface.blit(hard_text, (self.width / 2 + 60, self.height - 188))

    def update(self):
        self.background.update()    

    def handle_click(self, mouse_pos):
        easyRect = pygame.Rect(self.width / 2, 100, 180, 40)
        mediumRect = pygame.Rect(self.width / 2, 300 , 180, 40)
        hardRect = pygame.Rect(self.width / 2,self.height - 200, 180, 40)

        if easyRect.collidepoint(mouse_pos):
            return "easy"
        
        if mediumRect.collidepoint(mouse_pos):
            return "medium"
        
        if hardRect.collidepoint(mouse_pos):
            return "hard"




    

            


