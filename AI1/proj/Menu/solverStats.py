import pygame
from Menu.background import Background
from Menu.menu import Button
from objects.replay_button import ReplayButton
from objects.exit_button import ExitButton
from objects.empty import Empty

class SolverStats:
    def __init__(self, screen_width, screen_height, solver, num_moves, algorithm, heuristic_name):
        self.background = Background(screen_width, screen_height)
        self.empty = Empty(screen_width, screen_height)
        self.font = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 24)

        self.solver = solver
        self.num_moves = num_moves
        self.algorithm = algorithm
        self.heuristic_name = heuristic_name

        self.btn_replay = ReplayButton(screen_width, screen_height)
        self.btn_menu   = ExitButton(screen_width, screen_height)



        self.save_results()


    def save_results(self):
        with open("output_files/results.txt", "a") as f:
            f.write(f"="*10 + " Stats " + "="*10 + "\n")

            f.write(f"Algorithm: {self.algorithm}\n")
            f.write(f"Heuristic: {self.heuristic_name}\n\n")

            f.write(f"Moves: {self.num_moves}\n")
            f.write(f"Expanded Nodes: {self.solver.expanded_nodes}\n")
            f.write(f"Generated Nodes: {self.solver.generated_nodes}\n")
            f.write(f"Expanded Nodes: {self.solver.time_execution:.4f}\n")
            f.write("\n"*5)



    def draw(self, surface):
        self.background.draw(surface)
        self.empty.draw(surface)

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
            lbl = self.font_small.render(f"{label}:", True, (117, 28, 92))
            val = self.font_small.render(value, True, (237, 135, 37))
            surface.blit(lbl, (80, y))
            surface.blit(val, (280, y))
            y += 40

        self.btn_replay.draw(surface)
        self.btn_menu.draw(surface)

    def handle_click(self, mouse_pos):
        r = self.btn_replay.rect
        m = self.btn_menu.rect
        if r.collidepoint(mouse_pos):
            return 1  # replay
        if m.collidepoint(mouse_pos):
            return 2  # menu
        return 0
