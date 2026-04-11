import pygame 

from Menu.background import Background
from objects.title import TitleScreen
from objects.witch import Witch
from objects.shelf import Shelf
from objects.play_button import PlayButton
from objects.model_button import ModelButton
from objects.exit_button import ExitButton


class Button: 
    def __init__(self, pos_x, pos_y, width, height, color):
        self.x = pos_x
        self.y = pos_y
        self.width = width
        self.height = height
        self.color = color

    # Draw button rectangle
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))


# Main menu screen
class Menu: 
    def __init__(self, screen_width, screen_height):
        # Background and decorative elements
        self.background = Background(screen_width, screen_height)
        self.title_logo = TitleScreen(screen_width, screen_height)
        self.witch = Witch(screen_width, screen_height)
               
        # Shelves displayed in the menu
        self.shelves = [
            Shelf(screen_width // 2 + 17, screen_height // 2 + 20, 38 * 7, 3 * 7),  # Shelf 1
            Shelf(screen_width // 2 + 17, screen_height // 2 + 165 , 38 * 7, 3 * 7),  # Shelf 2
            Shelf(screen_width // 2 + 17, screen_height // 2 + 315, 38 * 7, 3 * 7)  # Shelf 3
        ]
        
        # Menu buttons
        self.play_btn = PlayButton(screen_width, screen_height)
        self.model_btn = ModelButton(screen_width, screen_height)
        self.exit_btn = ExitButton(screen_width, screen_height)

    # Update animated elements
    def update(self):
        self.background.update()

    # Draw all menu components
    def draw(self, surface, show_logo=True):
        # Background and particles
        self.background.draw(surface)
        
        # Draw main menu buttons
        self.play_btn.draw(surface)
        self.model_btn.draw(surface)
        self.exit_btn.draw(surface)
        
        # Optionally draw title screen elements
        if show_logo:
            self.title_logo.draw(surface)
            self.witch.draw(surface)
            for shelf in self.shelves:
                shelf.draw(surface)
        

    # Check user clicks on buttons
    def handle_click(self, mouse_pos):
        if self.play_btn.rect.collidepoint(mouse_pos):
            return "play"
        if self.model_btn.rect.collidepoint(mouse_pos):
            return "model"
        if self.exit_btn.rect.collidepoint(mouse_pos):
            return "exit"
        return None
