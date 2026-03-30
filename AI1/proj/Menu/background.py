import pygame
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
        
        self.PARTICLE_COLORS = [(255,182,193), (173,216,230), (221,160,221)]
        # Set to a solid beige color
        self.bg_color = (245, 245, 220) 

    def update(self):
        self.spawn_timer += 1
        if len(self.particles) < self.MAX_PARTICLES and self.spawn_timer >= self.spawn_rate:
            self.particles.append(Particle(random.randint(100, 500), self.screen_height, 14, random.choice(self.PARTICLE_COLORS)))
            self.spawn_timer = 0
        for p in self.particles:
            p.update(self.screen_width, self.screen_height)

    def draw(self, surface):
        surface.fill(self.bg_color)
        for p in self.particles:
            p.draw(surface)