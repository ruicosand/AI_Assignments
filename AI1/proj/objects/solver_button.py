import pygame

class SolverButton:
    def __init__(self, screen_width, screen_height, model):
        try:
            # 1. Load the original 64x64 sprite
            if(model == 0):
                raw_sprite = pygame.image.load("images/bfs_button.png").convert_alpha()
            elif(model == 1):
                raw_sprite = pygame.image.load("images/dfs_button.png").convert_alpha()
            elif(model == 2):
                raw_sprite = pygame.image.load("images/ucs_button.png").convert_alpha()
            elif(model == 3):
                raw_sprite = pygame.image.load("images/star_button.png").convert_alpha()
            elif(model == 4):
                raw_sprite = pygame.image.load("images/greedy_button.png").convert_alpha()
            else:
                raw_sprite = pygame.image.load("images/weight_button.png").convert_alpha()
                

            # 2. Find the actual area containing pixels (removes empty space)
            cropping_rect = raw_sprite.get_bounding_rect()
            cropped_sprite = raw_sprite.subsurface(cropping_rect)
            
            # 3. Scale ONLY the cropped version
            self.width = 40 * 7
            self.height = 11 * 7
            self.image = pygame.transform.scale(cropped_sprite, (self.width, self.height))
            
            if model == 0:
                self.rect = self.image.get_rect(center=(screen_width // 2 - 150, screen_height // 4 + 70))
            elif model == 1:
                self.rect = self.image.get_rect(center=(screen_width // 2 + 150, screen_height // 4 + 70))
            elif model == 2:
                self.rect = self.image.get_rect(center=(screen_width // 2 - 150, screen_height // 4 + 170))
            elif model == 3:
                self.rect = self.image.get_rect(center=(screen_width // 2 + 150, screen_height // 4 + 170))
            elif model == 4:
                self.rect = self.image.get_rect(center=(screen_width // 2 - 150, screen_height //4 + 270))
            else:
                self.rect = self.image.get_rect(center=(screen_width // 2 + 150, screen_height // 4 + 270))
        except Exception as e:
            print(f"Title Image Error: {e}")
            self.image = None

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)