import pygame
from objects.solver_button import SolverButton
from objects.x_button import XButton
from Menu.background import Background
from Menu.menu import Button
from objects.file_button import FileButton

# Algorithms that require a heuristic choice
NEEDS_HEURISTIC = {"Star", "Greedy", "Weight"}

# Menu for selecting a solving algorithm and optional heuristic
class SolverMenu:
    def __init__(self, screen_width, screen_height):
        self.background = Background(screen_width, screen_height)
        # Track which screen is currently shown
        self.screen = "algorithm"
        self.selected_algorithm = None
        self.font = pygame.font.SysFont(None, 28)

        # UI elements
        self.file_button = FileButton(screen_width, screen_height)
        self.x = XButton(screen_width, screen_height)
        
        # Algorithm selection buttons
        self.alg_buttons = [
            ("BFS",    SolverButton(screen_width, screen_height, 0)),
            ("DFS",    SolverButton(screen_width, screen_height, 1)),
            ("UCS",    SolverButton(screen_width, screen_height, 2)),
            ("Star",   SolverButton(screen_width, screen_height, 3)),
            ("Greedy", SolverButton(screen_width, screen_height, 4)),
            ("Weight", SolverButton(screen_width, screen_height, 5)),
        ]

        # Heuristic selection buttons (only used by some algorithms)
        self.h_buttons = [
            ("h1 - Color changes", Button(40, 40,  220, 40, (0, 255, 0))),
            ("h2 - Mixed tubes",   Button(40, 100, 220, 40, (0, 255, 0))),
            ("h3 - h1 + h2",       Button(40, 160, 220, 40, (0, 255, 0))),
        ]

    # Update background animation
    def update(self):
        self.background.update()

    # Draw current menu screen
    def draw(self, surface):
        self.background.draw(surface)
        self.x.draw(surface)
        
        # Draw algorithm selection screen
        if self.screen == "algorithm":
            self.file_button.draw(surface)

            for name, btn in self.alg_buttons:
                btn.draw(surface)

        # Draw heuristic selection screen
        elif self.screen == "heuristic":
            for name, btn in self.h_buttons:
                btn.draw(surface)
                text = self.font.render(name, True, (0, 0, 0))
                surface.blit(text, (btn.x + 10, btn.y + 12))

    # Handle user clicks and navigate screens
    def handle_click(self, mouse_pos):
        # Exit button
        if self.x.rect.collidepoint(mouse_pos):
            return "exit"
        
        # Handle algorithm selection
        if self.screen == "algorithm":
            rectFile = self.file_button.rect

            if rectFile.collidepoint(mouse_pos):
                return -1

            for name, btn in self.alg_buttons:
                rect = btn.rect
                if rect.collidepoint(mouse_pos):
                    self.selected_algorithm = name
                    # If algorithm doesn't need heuristic, continue
                    if name not in NEEDS_HEURISTIC:
                        return 1
                    # Otherwise, switch to heuristic screen
                    else:
                        self.screen = "heuristic"
                        return 0

        # Handle heuristic selection
        elif self.screen == "heuristic":
            for i, (name, btn) in enumerate(self.h_buttons):
                rect = pygame.Rect(btn.x, btn.y, btn.width, btn.height)
                if rect.collidepoint(mouse_pos):
                    return i + 2

        return 0
