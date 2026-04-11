import pygame 
from game_logic import GameController
from waterSort import WaterSort
from Menu.background import Background
from Menu.menu import Button
from solver import Solver
from copy import deepcopy
from objects.shelf import Shelf
from objects.x_button import XButton
from objects.hint_button import HintButton
from objects.reset_button import ResetButton
from objects.next_button import NextButton

# Main gameplay class: handles board state, user interaction, and win condition
class Game:
    def __init__(self, width, height, num_colors, tube_size, extra_hints = 0):
        # Core game state
        self.controller = GameController(num_colors,tube_size)
        self.num_colors = num_colors
        self.initial_board = deepcopy(self.controller.board)
        self.tube_size = tube_size
        self.width = width
        self.height = height

        # Game status
        self.button = None
        self.isWon = False
        self.font = pygame.font.SysFont(None, 24)

        # Difficulty-based hint system
        if num_colors == 4:
            self.difficulty = 0
            self.num_hints = 1
        elif num_colors == 7:
            self.difficulty = 1
            self.num_hints = 2
        elif num_colors == 10:
            self.difficulty = 2
            self.num_hints = 4
            
        self.num_hints += extra_hints
        
        # Visual components
        self.background = Background(width,height)
        self.x = XButton(width,height)
        self.tubes_positions = []
        self.setup_tubes()

        # UI buttons
        self.hintButton = HintButton(self.width, self.height, self.num_hints)
        self.resetButton = ResetButton(self.width, self.height)
        self.buttonBack = ResetButton(self.width, self.height)
        self.buttonNext = NextButton(self.width, self.height)

    # Compute layout of tubes and shelves
    def setup_tubes(self):
        total_tubes = self.num_colors + 2
        total_lines = total_tubes // 3

        remaining_space = (self.width - 3 * 60) / 4
        
        shelf_width = int(3 * 60 + 2 * remaining_space)
        shelf_x = int(remaining_space)
        shelf_height = 3 * 7
        
        self.shelves = []

        for line in range(total_lines):
            pos_y = 50 + line * (120 + 40)  
            pos_x = remaining_space

            for col in range(3):
                self.tubes_positions.append((pos_x, pos_y))
                pos_x += 60 + remaining_space
            
            self.shelves.append(Shelf(shelf_x - 5, int(pos_y + 120), shelf_width + 10, shelf_height))

    # Draw current game state
    def draw(self,surface):
        self.background.draw(surface)

        # Show different UI depending on win state
        if self.isWon is False:
            self.resetButton.draw(surface)
            self.hintButton.draw(surface)
            self.x.draw(surface)
        else:
            self.buttonBack.draw(surface)
            self.buttonNext.draw(surface)

        layer_height = 120 // self.tube_size

        # Draw tubes and colors
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
                
        # Draw decorative shelves
        for shelf in self.shelves:
            shelf.draw(surface)

    # Generate a hint using heuristic-based best move
    def handle_hint(self):
        initial_state = WaterSort(self.controller.board)
        solver = Solver(initial_state)
        possible_boards = initial_state.generate_boards()

        # Choose best state according to heuristic
        best_board, _ = possible_boards[0]
        min_heuristic = solver.heuristic_3(best_board)
        
        for state, _ in possible_boards[1:]:
            heuristic_value = solver.heuristic_3(state)
            if heuristic_value < min_heuristic:
                best_board = state
                min_heuristic = heuristic_value
            
        # Apply chosen hint state
        self.controller.board = [list(tube) for tube in best_board.board]
        self.hintButton.decrement()

    # Handle user input (clicks)
    def handle_click(self,pos):
        if self.isWon:
            backRect = self.resetButton.rect
            nextRect = self.buttonNext.rect

            if backRect.collidepoint(pos):
                self.controller.board = self.initial_board
                self.isWon = False

            if nextRect.collidepoint(pos):
                return "next"

        else:
            buttonRect = self.hintButton.rect
            resetRect = self.resetButton.rect

            tube_selected = None
        
            # Detect which tube was clicked
            for i, position in enumerate(self.tubes_positions):
                rect = pygame.Rect(position[0], position[1], 60, 120)
                if rect.collidepoint(pos): 
                    tube_selected = i
                    break

            # Hint system
            if buttonRect.collidepoint(pos):
                if self.num_hints > 0:
                    self.handle_hint()
                    self.num_hints -= 1
                waterSort = WaterSort(self.controller.board)
                return waterSort.is_won()
                
            # Reset game
            if resetRect.collidepoint(pos):
                if (self.difficulty == 0):
                    self.num_hints = 1
                elif self.difficulty == 1:
                    self.num_hints = 2
                else: self.num_hints = 3

                self.controller.board = deepcopy(self.initial_board)
                self.hintButton.reset(self.num_hints)
                return False

            # Exit game
            if self.x.rect.collidepoint(pos):
                return "exit"

            # If no tube clicked, do nothing
            if tube_selected is None:
                return False
        
            # Apply move and check win condition
            self.controller.handle_click(tube_selected)
            waterSort = WaterSort(self.controller.board)
            return waterSort.is_won()
