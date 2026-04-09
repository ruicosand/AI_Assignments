import pygame

class DiffButton:
    def __init__(self, screen_width, screen_height, difficulty):
        try:
            # 1. Load the original 64x64 sprite
            if(difficulty == 0):
                raw_sprite = pygame.image.load("images/easy_button.png").convert_alpha()
            elif(difficulty == 1):
                raw_sprite = pygame.image.load("images/medium_button.png").convert_alpha()
            else:
                raw_sprite = pygame.image.load("images/hard_button.png").convert_alpha()

            # 2. Find the actual area containing pixels (removes empty space)
            cropping_rect = raw_sprite.get_bounding_rect()
            cropped_sprite = raw_sprite.subsurface(cropping_rect)
            
            # 3. Scale ONLY the cropped version
            self.width = 41 * 7
            self.height = 11 * 7
            self.image = pygame.transform.scale(cropped_sprite, (self.width, self.height))
            
            if difficulty == 0:
                self.rect = self.image.get_rect(center=(screen_width // 2, screen_height // 4))
            elif difficulty == 1:
                self.rect = self.image.get_rect(center=(screen_width // 2, screen_height // 2))
            else:
                self.rect = self.image.get_rect(center=(screen_width // 2, 3*screen_height // 4))
        except Exception as e:
            print(f"Title Image Error: {e}")
            self.image = None

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)