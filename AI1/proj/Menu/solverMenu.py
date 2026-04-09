import pygame
from Menu.background import Background
from Menu.menu import Button

NEEDS_HEURISTIC = {"Star", "Greedy", "Weight"}

class SolverMenu:
    def __init__(self, screen_width, screen_height):
        self.background = Background(screen_width, screen_height)
        self.screen = "algorithm"
        self.selected_algorithm = None
        self.font = pygame.font.SysFont(None, 28)

        self.file_button = Button(40, 550, 180, 40, (255,0,255))

        self.alg_buttons = [
            ("BFS",    Button(40, 40,  180, 40, (0, 255, 0))),
            ("DFS",    Button(40, 100, 180, 40, (0, 255, 0))),
            ("UCS",    Button(40, 160, 180, 40, (0, 255, 0))),
            ("Star",   Button(40, 220, 180, 40, (0, 255, 0))),
            ("Greedy", Button(40, 280, 180, 40, (0, 255, 0))),
            ("Weight", Button(40, 340, 180, 40, (0, 255, 0))),
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

        if self.screen == "algorithm":
            self.file_button.draw(surface)
            file_text = self.font.render("Load file", True, (0, 0, 0))
            surface.blit(file_text, (self.file_button.x + 40, self.file_button.y + 12))

            for name, btn in self.alg_buttons:
                btn.draw(surface)
                text = self.font.render(name, True, (0, 0, 0))
                surface.blit(text, (btn.x + 10, btn.y + 12))

        elif self.screen == "heuristic":
            for name, btn in self.h_buttons:
                btn.draw(surface)
                text = self.font.render(name, True, (0, 0, 0))
                surface.blit(text, (btn.x + 10, btn.y + 12))

    def handle_click(self, mouse_pos):
        if self.screen == "algorithm":
            rectFile = pygame.Rect(self.file_button.x, self.file_button.y, self.file_button.width, self.file_button.height)

            if rectFile.collidepoint(mouse_pos):
                return -1

            for name, btn in self.alg_buttons:
                rect = pygame.Rect(btn.x, btn.y, btn.width, btn.height)
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