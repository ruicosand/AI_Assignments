import pygame

class HintButton:
    def __init__(self, screen_width, screen_height, hint_count):
        self.hint_count = hint_count

        try:
            # Load and crop, same as DiffButton
            raw_sprite = pygame.image.load("images/hint_button.png").convert_alpha()
            cropping_rect = raw_sprite.get_bounding_rect()
            cropped_sprite = raw_sprite.subsurface(cropping_rect)

            self.width = 41 * 7
            self.height = 11 * 7
            self.image = pygame.transform.scale(cropped_sprite, (self.width, self.height))
            self.rect = self.image.get_rect(center=(screen_width - 155, screen_height - 70))
        except Exception as e:
            print(f"Hint Button Image Error: {e}")
            self.image = None

        self.font = pygame.font.SysFont(None, 68)

    def increment(self):
        self.hint_count += 1
    def decrement(self):
        if self.hint_count > 0:
            self.hint_count -= 1

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)

            # Draw the counter on top of the button
            count_text = self.font.render(str(self.hint_count), True, (237, 135, 37))
            text_rect = count_text.get_rect(midtop=(self.rect.centerx, self.rect.top - 50))
            surface.blit(count_text, text_rect)