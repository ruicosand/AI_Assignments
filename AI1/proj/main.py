import pygame
from pygame.locals import *
from Menu.menu import Menu
from game import Game


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.state = "menu"
        self.size = self.width, self.height = 600, 800
        self.clock = None
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
                if self.menu.handle_click(event.pos):
                    self.state = "game"
                    self.game = Game(self.width, self.height)
            if self.state == "game":
                if self.game.handle_click(event.pos):
                    self.pending_win = 2 


    def on_loop(self):
        if self.state == "menu":
            self.menu.update()
        if self.state == "game" and self.pending_win > 0:
            self.pending_win -= 1
            if self.pending_win == 0:
                self.state = "win"

    def on_render(self):
        if self.state == "menu":
            self.menu.draw(self._display_surf)
        if self.state == "game":
            self.game.draw(self._display_surf)
        
        if self.state == "solver_menu":
            self
        if self.state == "solving":

        if self.state == "solver_stats":

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