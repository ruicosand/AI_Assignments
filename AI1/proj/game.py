import pygame 
from game_logic import GameController
from waterSort import WaterSort
from Menu.background import Background
from Menu.menu import Button
from solver import Solver
from copy import deepcopy
from objects.shelf import Shelf
from objects.x_button import XButton



class Game:
    def __init__(self, width, height, num_colors, tube_size):
        self.controller = GameController(num_colors,tube_size)
        self.num_colors = num_colors
        self.initial_board = deepcopy(self.controller.board)
        self.tube_size = tube_size
        self.width = width
        self.height = height
        self.button = None
        self.isWon = False
        self.font = pygame.font.SysFont(None, 24)

        if num_colors == 4:
            self.difficulty = 0
            self.num_hints = 1
        
        elif num_colors == 7:
            self.difficulty = 1
            self.num_hints = 2

        elif num_colors == 10:
            self.difficulty = 2
            self.num_hints = 4
    

        self.background = Background(width,height)
        self.x = XButton(width,height)
        self.tubes_positions = []
        self.setup_tubes()

        
        self.hintButton = Button(self.width - 120, self.height - 70, 100, 40, (0,255,255))
        self.resetButton = Button(20, self.height - 70, 100, 40, (0,255,0))
        self.buttonBack = Button(self.width - 300, self.height - 70, 100, 40, (0,255,255))
        self.buttonNext = Button(self.width - 150, self.height - 70, 100, 40, (0,255,255))
     

    def setup_tubes(self):
        total_tubes = self.num_colors + 2

        total_lines = total_tubes // 3

        remaining_space = (self.width - 3 * 60) / 4

        for line in range(total_lines):
            pos_y = 100 + line * (120 + 40)  
            pos_x = remaining_space

            for col in range(3):
                self.tubes_positions.append((pos_x, pos_y))
                pos_x += 60 + remaining_space

    def draw(self,surface):
        self.background.draw(surface)

        if self.isWon is False:
            self.resetButton.draw(surface)
            self.hintButton.draw(surface)
            self.x.draw(surface)

            reset_text = self.font.render("Reset", True, (0, 0, 0))
            hint_text = self.font.render(f"Hint ({self.num_hints})", True, (0, 0, 0))
            surface.blit(reset_text, (self.resetButton.x + 5, self.resetButton.y + 5))
            surface.blit(hint_text, (self.hintButton.x + 5, self.hintButton.y + 5))

        else:
            self.buttonBack.draw(surface)
            self.buttonNext.draw(surface)

            back_text = self.font.render("Reset", True, (0, 0, 0))
            next_text = self.font.render("Next", True, (0, 0, 0))
            surface.blit(back_text, (self.buttonBack.x + 15, self.buttonBack.y + 20))
            surface.blit(next_text, (self.buttonNext.x + 15, self.buttonNext.y + 20))

        layer_height = 120 // self.tube_size

        for i, pos in enumerate(self.tubes_positions):
            if i == self.controller.selected_tube:
                border_color = (255, 255, 255)
                y_offset = -20  
            else:
                border_color = (0, 0, 0)
                y_offset = 0

            pygame.draw.rect(surface, border_color, (pos[0], pos[1] + y_offset, 60, 120), width=2)
            for j, color in enumerate(self.controller.board[i]):
                y = pos[1] + 120 - (j + 1) * layer_height
                pygame.draw.rect(surface, color, (pos[0], y + y_offset, 60, layer_height))


    def handle_hint(self):
        initial_state = WaterSort(self.controller.board)

        solver = Solver(initial_state)

        possible_boards = initial_state.generate_boards()

        best_board = possible_boards[0]
        min_heuristic = solver.heuristic_3(possible_boards[0])
        
        for i in range(1,len(possible_boards)):
            heuristic_value = solver.heuristic_3(possible_boards[i])
            if heuristic_value < min_heuristic:
                best_board = possible_boards[i]
                min_heuristic = heuristic_value 
            
            
        self.controller.board = [list(tube) for tube in best_board.board]



    def handle_click(self,pos):
        if self.isWon:
            backRect = pygame.Rect(self.width - 300, self.height - 70, 100, 40)
            nextRect = pygame.Rect(self.width - 150, self.height - 70, 100, 40)

            if backRect.collidepoint(pos):
                self.controller.board = self.initial_board
                self.isWon = False

            if nextRect.collidepoint(pos):
                return "next"

        else:
            buttonRect = pygame.Rect(self.width - 120, self.height - 70, 100, 40)
            resetRect = pygame.Rect(20, self.height - 70, 100, 40)

            tube_selected = None
        
            for i, position in enumerate(self.tubes_positions):
                rect = pygame.Rect(position[0], position[1], 60, 120)
                if rect.collidepoint(pos): 
                    tube_selected = i
                    break


            if buttonRect.collidepoint(pos):
                if self.num_hints > 0:
                    self.handle_hint()
                    self.num_hints -= 1
                waterSort = WaterSort(self.controller.board)
                return waterSort.is_won()
                
            if resetRect.collidepoint(pos):
                if (self.difficulty == 0):
                    self.num_hints = 1
                elif self.difficulty == 1:
                    self.num_hints = 2
                else: self.num_hints = 3

                self.controller.board = self.initial_board
                return False

            if self.x.rect.collidepoint(pos):
                return "exit"

            if tube_selected is None:
                return False
        
            self.controller.handle_click(tube_selected)
            waterSort = WaterSort(self.controller.board)
            return waterSort.is_won()
        
           
        
       