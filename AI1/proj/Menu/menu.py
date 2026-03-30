import pygame 
from Menu.background import Background
from objects.title import TitleScreen
from objects.witch import Witch
from objects.shelf import Shelf
from objects.play_button import PlayButton
from objects.model_button import ModelButton
from objects.exit_button import ExitButton


class Menu: 
    def __init__(self, screen_width, screen_height):
        self.background = Background(screen_width, screen_height)
        self.title_logo = TitleScreen(screen_width, screen_height)
        self.witch = Witch(screen_width, screen_height)
               
        self.shelves = [
            Shelf(250, 250, 400, 400),  # Shelf 1
            Shelf(250, 400, 400, 400),  # Shelf 2
            Shelf(250, 550, 400, 400)  # Shelf 3
        ]
        
        self.play_btn = PlayButton(screen_width, screen_height)
        self.model_btn = ModelButton(screen_width, screen_height)
        self.exit_btn = ExitButton(screen_width, screen_height)
        
        # Position button relative to screen center

    def update(self):
        self.background.update()

    def draw(self, surface, show_logo=True):
        # 1. Draw beige background and particles
        self.background.draw(surface)
        
        self.play_btn.draw(surface)
        self.model_btn.draw(surface)
        self.exit_btn.draw(surface)
        
        # 2. Draw the Logo if we are on the Title/Menu screen
        if show_logo:
            self.title_logo.draw(surface)
            self.witch.draw(surface)
            for shelf in self.shelves:
                shelf.draw(surface)
        

    def handle_click(self, mouse_pos):
        # Check collision for each button using their internal .rect
        if self.play_btn.rect.collidepoint(mouse_pos):
            return "play"
        if self.model_btn.rect.collidepoint(mouse_pos):
            return "model"
        if self.exit_btn.rect.collidepoint(mouse_pos):
            return "exit"
        return None