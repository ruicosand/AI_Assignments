import pygame

class TitleScreen:
    def __init__(self, screen_width, screen_height):
        try:
            # Load the sprite provided
            raw_title = pygame.image.load("images/title_screen.png").convert_alpha()
            
            # Use 300x300 to keep the 64x64 sprite square and prevent stretching
            self.width = 480
            self.height = 480 
            
            self.image = pygame.transform.scale(raw_title, (self.width, self.height))
            self.rect = self.image.get_rect(center=(screen_width // 2, screen_height // 3.5))
        except Exception as e:
            print(f"Title Image Error: {e}")
            self.image = None

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)