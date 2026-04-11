import pygame
from objects.solver_button import SolverButton
from objects.x_button import XButton
from Menu.background import Background
from Menu.menu import Button
from objects.file_button import FileButton

NEEDS_HEURISTIC = {"Star", "Greedy", "Weight"}

class SolverMenu:
    def __init__(self, screen_width, screen_height):
        self.background = Background(screen_width, screen_height)
        self.screen = "algorithm"
        self.selected_algorithm = None
        self.font = pygame.font.SysFont(None, 28)

        self.file_button = FileButton(screen_width, screen_height)
        self.x = XButton(screen_width, screen_height)
        

        self.alg_buttons = [
            ("BFS",    SolverButton(screen_width, screen_height, 0)),
            ("DFS",    SolverButton(screen_width, screen_height, 1)),
            ("UCS",    SolverButton(screen_width, screen_height, 2)),
            ("Star",   SolverButton(screen_width, screen_height, 3)),
            ("Greedy", SolverButton(screen_width, screen_height, 4)),
            ("Weight", SolverButton(screen_width, screen_height, 5)),
        ]

        self.h_buttons = [
            ("h1 - Color changes", Button(40, 40,  220, 40, (0, 255, 0))),
            ("h2 - Mixed tubes",   Button(40, 100, 220, 40, (0, 255, 0))),
            ("h3 - h1 + h2",       Button(40, 160, 220, 40, (0, 255, 0))),
        ]

    def update(self):
        self.background.update()

    def draw(self, surface):
        self.background.draw(surface)
        self.x.draw(surface)
        

        if self.screen == "algorithm":
            self.file_button.draw(surface)

            for name, btn in self.alg_buttons:
                btn.draw(surface)

        elif self.screen == "heuristic":
            for name, btn in self.h_buttons:
                btn.draw(surface)
                text = self.font.render(name, True, (0, 0, 0))
                surface.blit(text, (btn.x + 10, btn.y + 12))

    def handle_click(self, mouse_pos):
        if self.x.rect.collidepoint(mouse_pos):
            return "exit"
        
        if self.screen == "algorithm":
            rectFile = self.file_button.rect

            if rectFile.collidepoint(mouse_pos):
                return -1

            for name, btn in self.alg_buttons:
                rect = btn.rect
                if rect.collidepoint(mouse_pos):
                    self.selected_algorithm = name
                    if name not in NEEDS_HEURISTIC:
                        return 1
                    else:
                        self.screen = "heuristic"
                        return 0

        elif self.screen == "heuristic":
            for i, (name, btn) in enumerate(self.h_buttons):
                rect = pygame.Rect(btn.x, btn.y, btn.width, btn.height)
                if rect.collidepoint(mouse_pos):
                    return i + 2

        return 0