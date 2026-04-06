import pygame
from Menu.background import Background
from Menu.menu import Button


class SolverStats:
    def __init__(self, screen_width, screen_height, solver, num_moves, algorithm, heuristic_name):
        self.background = Background(screen_width, screen_height)
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16)

        self.solver = solver
        self.num_moves = num_moves
        self.algorithm = algorithm
        self.heuristic_name = heuristic_name

        self.btn_replay = Button(screen_width // 2 - 130, screen_height - 120, 110, 40, (0, 200, 100))
        self.btn_menu   = Button(screen_width // 2 + 20,  screen_height - 120, 110, 40, (0, 180, 230))

    def draw(self, surface):
        self.background.draw(surface)

        title = self.font.render("Solver Stats", True, (255, 255, 255))
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 40))

        stats = [
            ("Algorithm",       self.algorithm),
            ("Heuristic",       self.heuristic_name),
            ("Moves",           str(self.num_moves)),
            ("Expanded nodes",  str(self.solver.expanded_nodes)),
            ("Generated nodes", str(self.solver.generated_nodes)),
            ("Time (s)",        f"{self.solver.time_execution:.4f}"),
        ]

        y = 120
        for label, value in stats:
            lbl = self.font_small.render(f"{label}:", True, (180, 180, 180))
            val = self.font_small.render(value, True, (255, 255, 255))
            surface.blit(lbl, (80, y))
            surface.blit(val, (280, y))
            y += 40

        self.btn_replay.draw(surface)
        self.btn_menu.draw(surface)

        r_lbl = self.font_small.render("Replay", True, (0, 0, 0))
        m_lbl = self.font_small.render("Menu",   True, (0, 0, 0))
        surface.blit(r_lbl, (self.btn_replay.x + 25, self.btn_replay.y + 12))
        surface.blit(m_lbl, (self.btn_menu.x   + 30, self.btn_menu.y   + 12))

    def handle_click(self, mouse_pos):
        r = pygame.Rect(self.btn_replay.x, self.btn_replay.y, self.btn_replay.width, self.btn_replay.height)
        m = pygame.Rect(self.btn_menu.x,   self.btn_menu.y,   self.btn_menu.width,   self.btn_menu.height)
        if r.collidepoint(mouse_pos):
            return 1  # replay
        if m.collidepoint(mouse_pos):
            return 2  # menu
        return 0
