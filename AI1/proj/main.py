import pygame
from pygame.locals import *
from Menu.menu import Menu
from game import Game
from solverGame import SolverGame
from Menu.solverMenu import SolverMenu
from Menu.solverStats import SolverStats
from Menu.levelMenu import levelMenu

# Mapping heuristic codes to readable names
HEURISTIC_NAMES = {
    2: "h1 => Color changes",
    3: "h2 => Mixed tubes",
    4: "h3 => h1 + h2",
    None: "None",
}

# Main application class that manages the entire game flow
class App:
    def __init__(self):
        # General application state
        self.board_loaded = False
        self._running = True
        self._display_surf = None
        self.state = "menu"          # Tracks which screen is active
        self.selectionMode = 0        # 1 = play mode, 2 = solver mode

        # Game parameters
        self.num_colors = None
        self.tube_size = 4
        self.size = self.width, self.height = 600, 800
        self.clock = None

        # Screens / components
        self.game = None
        self.levelMenu = None
        self.solverMenu = None
        self.solverStats = None
        self.solver = None
        self.level_name = None

        # State flags
        self.pending_win = 0
        self.selected_heuristic_code = None
        self.hint_counter = 0

    # Initialize pygame and main menu
    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.menu = Menu(self.width, self.height)
        self.clock = pygame.time.Clock()
        self._running = True
        return True

    # Start the solver process with the chosen algorithm/heuristic
    def _launch_solver(self, algorithm, heuristic_code):
        if not self.board_loaded or self.solver is None:
            self.solver = SolverGame(self.width, self.height, self.num_colors, self.tube_size)

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

    # Event handling for mouse/keyboard actions
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Handle main menu interactions
            if self.state == "menu":
                action = self.menu.handle_click(event.pos)

                if action == "exit":
                    self._running = False

                elif action == "play":
                    self.state = "level"
                    self.selectionMode = 1
                    self.levelMenu = levelMenu(self.width,self.height)

                elif action == "model":
                    self.state = "level"
                    self.selectionMode = 2
                    self.levelMenu = levelMenu(self.width,self.height)

            # Handle gameplay screen
            elif self.state == "game":
                value = self.game.handle_click(event.pos)
                
                if value == "exit":
                    self.state = "menu"

                if value == "next":
                    self.hint_counter = self.game.num_hints
                    self.game = Game(self.width, self.height, self.num_colors, self.tube_size, extra_hints=self.hint_counter)

                if value == True:
                    self.pending_win = 2

            # Handle difficulty selection
            elif self.state == "level":
                level = self.levelMenu.handle_click(event.pos)
                if level == "easy":
                    self.num_colors = 4
                    self.tube_size = 4
                    self.level_name ="Easy"
                    if self.selectionMode == 1:
                        self.state = "game"
                        self.game = Game(self.width,self.height, self.num_colors, self.tube_size)
                    else:
                        self.state = "solverMenu"
                        self.solverMenu = SolverMenu(self.width,self.height)

                if level == "medium":
                    self.num_colors = 7
                    self.tube_size = 4
                    self.level_name ="Medium"
                    if self.selectionMode == 1:
                        self.state = "game"
                        self.game = Game(self.width,self.height, self.num_colors, self.tube_size)
                    else:
                        self.state = "solverMenu"
                        self.solverMenu = SolverMenu(self.width,self.height)

                if level == "hard":
                    self.num_colors = 10
                    self.tube_size = 4
                    self.level_name ="Hard"
                    if self.selectionMode == 1:
                        self.state = "game"
                        self.game = Game(self.width,self.height, self.num_colors, self.tube_size)
                    else:
                        self.state = "solverMenu"
                        self.solverMenu = SolverMenu(self.width,self.height)

                if level == "exit":
                    self.state = "menu"

            # Handle solver menu interactions
            elif self.state == "solverMenu":
                clicked = self.solverMenu.handle_click(event.pos)
                algorithm = self.solverMenu.selected_algorithm

                if clicked == -1:
                    # Load board from file
                    self.solver = SolverGame(self.width, self.height, self.num_colors, self.tube_size)
                    self.solver.build_board()
                    self.board_loaded = True    
                    self.num_colors = self.solver.num_colors
                    return
                
                elif clicked == 1:
                    self._launch_solver(algorithm, None)

                elif clicked in (2, 3, 4):
                    self._launch_solver(algorithm, clicked)

                elif clicked == "exit":
                    self.state = "menu"

            # Handle solver stats screen
            elif self.state == "solver_stats":
                clicked = self.solverStats.handle_click(event.pos)
                if clicked == 1:  
                    self.solver.current_state = 0
                    self.solver.timer = 0
                    self.state = "solving"
                elif clicked == 2:  
                    self.state = "menu"

    # Update logic depending on the current state
    def on_loop(self):
        if self.state == "menu":
            self.menu.update()
        
        if self.state == "level":
            self.levelMenu.update()

        if self.state == "game" and self.pending_win > 0:
            self.pending_win -= 1
            if self.pending_win == 0:
                self.game.isWon = True

        if self.state == "solving":
            if self.solver.update_state():
                # When solver finishes, show stats
                num_moves = len(self.solver.board_solutions) - 1
                algorithm = self.solverMenu.selected_algorithm
                h_name = HEURISTIC_NAMES.get(self.selected_heuristic_code, "None")
                self.solverStats = SolverStats(
                    self.width, self.height,
                    self.solver.solver,
                    num_moves,
                    algorithm,
                    h_name,
                    self.level_name
                )
                self.state = "solver_stats"

    # Draw the appropriate screen
    def on_render(self):
        if self.state == "menu":
            self.menu.draw(self._display_surf)
        elif self.state == "level":
            self.levelMenu.draw(self._display_surf)
        elif self.state == "game":
            self.game.draw(self._display_surf)
        elif self.state == "solverMenu":
            self.solverMenu.draw(self._display_surf)
        elif self.state == "solving":
            self.solver.draw(self._display_surf)
        elif self.state == "solver_stats":
            self.solverStats.draw(self._display_surf)
        pygame.display.update()

    # Clean up pygame
    def on_cleanup(self):
        pygame.quit()

    # Main loop
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

# Start the application
if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()
