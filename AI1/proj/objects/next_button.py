import pygame

class NextButton:
    def __init__(self, screen_width, screen_height):

        try:
            # Load and crop, same as DiffButton
            raw_sprite = pygame.image.load("images/next_button.png").convert_alpha()
            cropping_rect = raw_sprite.get_bounding_rect()
            cropped_sprite = raw_sprite.subsurface(cropping_rect)

            self.width = 41 * 7
            self.height = 11 * 7
            self.image = pygame.transform.scale(cropped_sprite, (self.width, self.height))
            self.rect = self.image.get_rect(center=(screen_width - 155, screen_height - 70))
        except Exception as e:
            print(f"Next Button Image Error: {e}")
            self.image = None
            
    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)