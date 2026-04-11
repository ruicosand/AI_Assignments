import pygame
import random


class Particle:
    def __init__(self, x, y, radius, color):
        # Initial position and appearance
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        # Initial random velocity
        self.vy = random.uniform(-1.5, -1)
        self.vx = random.uniform(-0.5, 0.5)

    # Draw the particle on the screen
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        
    # Update particle position and reset when off-screen
    def update(self, screen_width, screen_height):
        self.x += self.vx
        self.y += self.vy
        if self.y < -self.radius:
            # Respawn at the bottom when leaving the top
            self.y = screen_height + self.radius
            self.x = random.randint(100, 500)


# Background manager responsible for particles and background color
class Background:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        self.spawn_timer = 0
        self.spawn_rate = 30
        self.MAX_PARTICLES = 15
        
        # Particle colors and background color
        self.PARTICLE_COLORS = [(255,182,193), (173,216,230), (221,160,221)]
        self.bg_color = (245, 245, 220)  # Beige background

    # Update particles and spawn new ones over time
    def update(self):
        self.spawn_timer += 1
        if len(self.particles) < self.MAX_PARTICLES and self.spawn_timer >= self.spawn_rate:
            self.particles.append(Particle(random.randint(100, 500), self.screen_height, 14, random.choice(self.PARTICLE_COLORS)))
            self.spawn_timer = 0
        for p in self.particles:
            p.update(self.screen_width, self.screen_height)

    # Draw background and particles
    def draw(self, surface):
        surface.fill(self.bg_color)
        for p in self.particles:
            p.draw(surface)
