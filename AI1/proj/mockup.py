import pygame
from pygame.locals import *
import random

class Particle:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.vy = random.uniform(-1.5, -1) 
        self.vx = random.uniform(-0.5, 0.5)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        
    def update(self, screen_width, screen_height):
        self.x += self.vx
        self.y += self.vy

        if self.y < -self.radius:
            self.y = screen_height + self.radius
            self.x = random.randint(100, 500)

class Background:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        self.spawn_timer = 0
        self.spawn_rate = 30 
        self.MAX_PARTICLES = 15 
        
        self.PARTICLE_COLORS = [
            (255, 87, 51), (255, 189, 51), (219, 255, 51),
            (51, 255, 87), (51, 255, 249), (51, 87, 255), (165, 51, 255)
        ]

        try:
            raw_image = pygame.image.load("background.png").convert()
            self.image = pygame.transform.scale(raw_image, (self.screen_width, self.screen_height))
        except:
            self.image = pygame.Surface((self.screen_width, self.screen_height))
            self.image.fill((30, 30, 30))

    def update(self):
        self.spawn_timer += 1
        if len(self.particles) < self.MAX_PARTICLES and self.spawn_timer >= self.spawn_rate:
            assigned_color = random.choice(self.PARTICLE_COLORS)
            new_particle = Particle(random.randint(100, 500), self.screen_height, 14, assigned_color)
            self.particles.append(new_particle)
            self.spawn_timer = 0

        for particle in self.particles:
            particle.update(self.screen_width, self.screen_height)

    def draw(self, surface):
        surface.blit(self.image, (0, 0))
        for particle in self.particles:
            particle.draw(surface)

class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 600, 800
        self.clock = None

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.background = Background(self.width, self.height)
        self.clock = pygame.time.Clock()
        self._running = True
        return True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

    def on_loop(self):
        self.background.update()

    def on_render(self):
        self.background.draw(self._display_surf)
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