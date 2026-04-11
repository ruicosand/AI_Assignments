import pygame 
import ast
from game_logic import GameController
from waterSort import WaterSort
from Menu.background import Background
from solver import Solver
from Menu.menu import Button
from objects.difficulty_button import DiffButton
from objects.shelf import Shelf
from objects.x_button import XButton

# Menu screen for choosing game difficulty/levels
class levelMenu:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # UI components
        self.background = Background(width, height)
        self.easy = DiffButton(width, height, 0)
        self.medium = DiffButton(width, height, 1)
        self.hard = DiffButton(width, height, 2)
        self.font = pygame.font.SysFont(None, 30)
        self.x = XButton(width,height)

        # Decorative shelves shown in the menu
        self.shelves = [
            Shelf(self.width // 3 - 30, self.height // 3 - 20, 38 * 7, 3 * 7),  # Shelf 1
            Shelf(self.width // 3 - 30, self.height // 3 + 180, 38 * 7, 3 * 7),  # Shelf 2
            Shelf(self.width // 3 - 30, self.height // 3 + 380, 38 * 7, 3 * 7)   # Shelf 3
        ]

    # Draw all UI elements on the screen
    def draw(self,surface):
        self.background.draw(surface)
        self.easy.draw(surface)
        self.medium.draw(surface)
        self.hard.draw(surface)
        self.x.draw(surface)
        
        for shelf in self.shelves:
            shelf.draw(surface)

    # Update background animation
    def update(self):
        self.background.update()    

    # Handle user clicks and return selected option
    def handle_click(self, mouse_pos):
        easyRect = self.easy.rect
        mediumRect = self.medium.rect
        hardRect = self.hard.rect

        if easyRect.collidepoint(mouse_pos):
            return "easy"
        
        if mediumRect.collidepoint(mouse_pos):
            return "medium"
        
        if hardRect.collidepoint(mouse_pos):
            return "hard"

        if self.x.rect.collidepoint(mouse_pos):
            return "exit"
