import pygame
from pygame.locals import *
from Menu.menu import Menu
from game import Game
from solverGame import SolverGame
from Menu.solverMenu import SolverMenu
from Menu.solverStats import SolverStats

HEURISTIC_NAMES = {
    2: "h1 => Color changes",
    3: "h2 => Mixed tubes",
    4: "h3 => h1 + h2",
    None: "None",
}

class App:
    def __init__(self):
        self.board_loaded = False
        self._running = True
        self._display_surf = None
        self.state = "menu"
        self.size = self.width, self.height = 600, 800
        self.clock = None
        self.game = None
        self.solverMenu = None
        self.solverStats = None
        self.solver = None
        self.pending_win = 0
        self.selected_heuristic_code = None

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.menu = Menu(self.width, self.height)
        self.clock = pygame.time.Clock()
        self._running = True
        return True
    
    def _launch_solver(self, algorithm, heuristic_code):
        if not self.board_loaded:
            self.solver = SolverGame(self.width, self.height)
        
        self.board_loaded = False

        self.selected_heuristic_code = heuristic_code

        heuristic_map = {
            2: self.solver.solver.heuristic_1,
            3: self.solver.solver.heuristic_2,
            4: self.solver.solver.heuristic_3,
        }
        heuristic = heuristic_map.get(heuristic_code, None)
        self.solver.handle_board(algorithm, heuristic)
        self.state = "solving"

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == "menu":
                clicked = self.menu.handle_click(event.pos)
                if clicked == 1:
                    self.state = "game"
                    self.game = Game(self.width, self.height)
                elif clicked == 2:
                    self.state = "solverMenu"
                    self.solverMenu = SolverMenu(self.width, self.height)

            elif self.state == "game":
                if self.game.handle_click(event.pos):
                    self.pending_win = 2 
            
            elif self.state == "solverMenu":
                clicked = self.solverMenu.handle_click(event.pos)
                algorithm = self.solverMenu.selected_algorithm
                if clicked == -1:
                    self.solver = SolverGame(self.width, self.height)
                    self.solver.build_board()
                    self.board_loaded = True    

                if clicked == 1:
                    
                    self._launch_solver(algorithm, None)

                elif clicked in (2, 3, 4):
                   
                    self._launch_solver(algorithm, clicked)

            elif self.state == "solver_stats":
                clicked = self.solverStats.handle_click(event.pos)
                if clicked == 1:  # replay
                    self.solver.current_state = 0
                    self.solver.timer = 0
                    self.state = "solving"
                elif clicked == 2:  # menu
                    self.state = "menu"

    def on_loop(self):
        if self.state == "menu":
            self.menu.update()
        if self.state == "game" and self.pending_win > 0:
            self.pending_win -= 1
            if self.pending_win == 0:
                self.state = "win"

        if self.state == "solving":
            if self.solver.update_state():
                num_moves = len(self.solver.board_solutions) - 1
                algorithm = self.solverMenu.selected_algorithm
                h_name = HEURISTIC_NAMES.get(self.selected_heuristic_code, "None")
                self.solverStats = SolverStats(
                    self.width, self.height,
                    self.solver.solver,
                    num_moves,
                    algorithm,
                    h_name
                )
                self.state = "solver_stats"

    def on_render(self):
        if self.state == "menu":
            self.menu.draw(self._display_surf)
        elif self.state == "game":
            self.game.draw(self._display_surf)
        elif self.state == "solverMenu":
            self.solverMenu.draw(self._display_surf)
        elif self.state == "solving":
            self.solver.draw(self._display_surf)
        elif self.state == "solver_stats":
            self.solverStats.draw(self._display_surf)
        elif self.state == "win":
            print("Won")
        pygame.display.update()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if not self.on_init():
            self._running = False

        while self._running:
            self.clock.tick(60)
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()

if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()