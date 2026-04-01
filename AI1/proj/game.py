import pygame 
from game_logic import GameController
from waterSort import WaterSort
from Menu.background import Background

def calculate_space(width,size):
        total_space = ( size / 3) * 60
        remaining_space = width - total_space
        
        remaining_space = remaining_space / 4

        return (total_space, remaining_space)

class Game:
    def __init__(self, width, height):
        self.controller = GameController()
        self.width = width
        self.height = height
        self.background = Background(width,height)
        self.tubes_positions = []
        self.setup_tubes()
    

    def setup_tubes(self):
        (total_space, remaining_space) = calculate_space(self.width,len(self.controller.board))
        bottom_tube_pos_y = 260
        bottom_tube_pos_x = remaining_space

        for _ in range (1,4):
            self.tubes_positions.append((bottom_tube_pos_x,bottom_tube_pos_y))
            bottom_tube_pos_x += 60 + remaining_space

        bottom_tube_pos_y = (self.height / 2) + 20
        bottom_tube_pos_x = remaining_space

        for _ in range (1,4):
            self.tubes_positions.append((bottom_tube_pos_x,bottom_tube_pos_y))
            bottom_tube_pos_x += 60 + remaining_space
    

    def draw(self,surface):
        self.background.draw(surface)



        for i, pos in enumerate(self.tubes_positions):
            if i == self.controller.selected_tube:
                border_color = (255, 255, 255)
                y_offset = -20  
            else:
                border_color = (0, 0, 0)
                y_offset = 0

            pygame.draw.rect(surface, border_color, (pos[0], pos[1] + y_offset, 60, 120), width=2)
            for j, color in enumerate(self.controller.board[i]):
                y = pos[1] + 120 - (j + 1) * 30
                pygame.draw.rect(surface,color,(pos[0],y + y_offset,60,30))



    def handle_click(self,pos):
        waterSort = WaterSort(self.controller.board)
        tube_selected = None
        
        for i, position in enumerate(self.tubes_positions):
            rect = pygame.Rect(position[0], position[1], 60, 120)
            if rect.collidepoint(pos): 
                tube_selected = i
                break

        if tube_selected is None:
            return False
       
        self.controller.handle_click(tube_selected)
        return waterSort.is_won()

    

            


