import pygame

class Shelf:
    def __init__(self, x, y, width, height):
        self.width = width
        self.height = height

        try:
            # 1. Load the original sprite
            raw_shelf = pygame.image.load("images/shelf.png").convert_alpha()

            # 2. Find the actual area containing pixels (removes empty space)
            cropping_rect = raw_shelf.get_bounding_rect()
            cropped_shelf = raw_shelf.subsurface(cropping_rect)

            # 3. Scale ONLY the cropped version
            self.image = pygame.transform.scale(cropped_shelf, (self.width, self.height))

            self.rect = self.image.get_rect(topleft=(x, y))
        except Exception as e:
            print(f"Shelf Image Error: {e}")
            self.image = None

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)