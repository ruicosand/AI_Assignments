import pygame

class Shelf:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        try:
            raw_shelf = pygame.image.load("images/shelf.png").convert_alpha()
            self.image = pygame.transform.scale(raw_shelf, (self.width, self.height))
        except:
            # Fallback to a brown rectangle if image is missing
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((139, 69, 19)) 

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))