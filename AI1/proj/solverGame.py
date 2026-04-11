import pygame 
import ast
from game_logic import GameController
from waterSort import WaterSort
from Menu.background import Background
from solver import Solver
import tkinter as tk
from tkinter import filedialog
from objects.shelf import Shelf

# Manages the solving process and visualization of the board over time
class SolverGame:
    def __init__(self, width, height, num_colors, tube_size):
        # Game and solver setup
        self.controller = GameController(num_colors, tube_size)
        self.solver = Solver(WaterSort(self.controller.board)) 
        self.board_loaded = False

        # Game settings
        self.num_colors = num_colors
        self.tube_size = tube_size
        self.width = width
        self.height = height

        # Animation state
        self.current_state = 0
        self.timer = 0
        self.frames_per_second = 25
        self.board_solutions = []

        # Visual elements
        self.background = Background(width,height)
        self.tubes_positions = []
        self.setup_tubes()
    
    # Calculate positions of tubes and shelves on screen
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

    # Move to the next solution state over time
    def update_state(self):
        self.timer += 1

        if self.timer >= self.frames_per_second:
            self.current_state += 1
            self.timer = 0
            return self.current_state >= len(self.board_solutions)

        return False 

    # Draw the current board configuration
    def draw(self,surface):
        board = self.board_solutions[self.current_state]
        self.background.draw(surface)
        layer_height = 120 // self.tube_size

        for i, pos in enumerate(self.tubes_positions):
            # Highlight selected tube
            if i == self.controller.selected_tube:
                border_color = (255, 255, 255)
                y_offset = -20  
            else:
                border_color = (0, 0, 0)
                y_offset = 0

            # Draw tube container
            pygame.draw.rect(surface, border_color, (pos[0], pos[1] + y_offset, 60, 120), width=2)

            # Draw each layer of color in the tube
            for j, color in enumerate(board.board[i]):
                y = pos[1] + 120 - (j + 1) * layer_height  
                pygame.draw.rect(surface, color, (pos[0], y + y_offset, 60, layer_height))
                
        for shelf in self.shelves:
            shelf.draw(surface)

    # Load a board from a text file and prepare solver
    def build_board(self):
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            title="Choose a board",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not file_path:
            return 
        
        with open(file_path) as f:
            lines = f.read().split('\n', 1)  
            fileBoard = ast.literal_eval(lines[1].strip())
        self.num_colors = int(lines[0].split('=')[1].strip())

        # Recalculate positions and reset solver with new board
        self.tubes_positions = []  
        self.setup_tubes()          
        self.solver = Solver(WaterSort(fileBoard))
        
    # Run selected solving algorithm and store resulting path
    def handle_board(self,algorithm, heuristic, weight=1):
        winnig_state = None

        # Select solving algorithm
        if algorithm == "BFS":
            winnig_state = self.solver.bfs_search()
        elif algorithm == "DFS":
            winnig_state = self.solver.dfs_search()
        elif algorithm == "UCS":
            winnig_state = self.solver.uniform_cost_search()
        elif (algorithm == "Star"):
            winnig_state = self.solver.a_star_search(heuristic)
        elif (algorithm == "Greedy"):
            winnig_state = self.solver.greedy_search(heuristic)
        else:
            winnig_state = self.solver.weigth_star_search(heuristic, weight)
        
        if winnig_state is None:
            print("Sem solução!")
            return

        # Reconstruct the sequence of board states from solution
        board_states = []

        while winnig_state.parent is not None:
            board_states.append(winnig_state.state)
            winnig_state = winnig_state.parent
        
        board_states.append(winnig_state.state)

        # Reverse to get initial -> final order
        self.board_solutions = board_states[::-1]
