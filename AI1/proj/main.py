import pygame
from pygame.locals import *
from Menu.menu import Menu
from game import Game
from solverGame import SolverGame
from Menu.solverMenu import SolverMenu

class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.state = "menu"
        self.size = self.width, self.height = 600, 800
        self.clock = None
        self.game = None
        self.solverMenu = None
        self.pending_win = 0

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.menu = Menu(self.width, self.height)
        self.clock = pygame.time.Clock()
        self._running = True
        return True

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
                if clicked == 1:
                    self.solver = SolverGame(self.width, self.height)
                    self.solver.handle_board("Star", self.solver.solver.heuristic_1)
                    self.state = "solving"

                elif clicked == 2:
                    self.solver = SolverGame(self.width, self.height)
                    self.solver.handle_board("Greedy", self.solver.solver.heuristic_1)
                    self.state = "solving"

                elif clicked == 3:
                    self.solver = SolverGame(self.width, self.height)
                    self.solver.handle_board("Weight",  self.solver.solver.heuristic_1, 2)
                    self.state = "solving"
            
            elif self.state == "solver_stats":
                clicked = self.solverStats.handle_click(event.pos)
                if clicked == 1:  # voltar
                    self.current_state = 0  # reinicia animação
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
                self.state = "solver_stats"

    def on_render(self):
        if self.state == "menu":
            self.menu.draw(self._display_surf)
        if self.state == "game":
            self.game.draw(self._display_surf)
        if self.state == "solverMenu":
            self.solverMenu.draw(self._display_surf)
        if self.state == "solving":
            self.solver.draw(self._display_surf)
        if self.state == "win":
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