import pygame

class PlayButton:
    def __init__(self, screen_width, screen_height):
        try:
            # 1. Load the original 64x64 sprite
            raw_sprite = pygame.image.load("images/play_button.png").convert_alpha()
            
            # 2. Find the actual area containing pixels (removes empty space)
            cropping_rect = raw_sprite.get_bounding_rect()
            cropped_sprite = raw_sprite.subsurface(cropping_rect)
            
            # 3. Scale ONLY the cropped version
            self.width = 41 * 7
            self.height = 11 * 7
            self.image = pygame.transform.scale(cropped_sprite, (self.width, self.height))
            
            # 4. Set the rect based on the new tight image
            self.rect = self.image.get_rect(center=(screen_width // 2 + 150, screen_height // 2.15))
            
        except Exception as e:
            print(f"Title Image Error: {e}")
            self.image = None

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)