
import pygame 
import ast
from game_logic import GameController
from waterSort import WaterSort
from Menu.background import Background
from solver import Solver
import tkinter as tk
from tkinter import filedialog

class SolverGame:
    def __init__(self, width, height, num_colors, tube_size):
        self.controller = GameController(num_colors, tube_size)
        self.solver = Solver(WaterSort(self.controller.board)) 
        self.board_loaded = False
        self.num_colors = num_colors
        self.tube_size = tube_size
        self.width = width
        self.height = height
        self.current_state = 0
        self.timer = 0
        self.frames_per_second = 25
        self.board_solutions = []
        self.background = Background(width,height)
        self.tubes_positions = []
        self.setup_tubes()
    

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

    def update_state(self):
        self.timer += 1

        if self.timer >= self.frames_per_second:
            self.current_state += 1
            self.timer = 0
            return self.current_state >= len(self.board_solutions)

        return False 

    def draw(self,surface):
        board = self.board_solutions[self.current_state]
        self.background.draw(surface)
        layer_height = 120 // self.tube_size

        for i, pos in enumerate(self.tubes_positions):
            if i == self.controller.selected_tube:
                border_color = (255, 255, 255)
                y_offset = -20  
            else:
                border_color = (0, 0, 0)
                y_offset = 0

            pygame.draw.rect(surface, border_color, (pos[0], pos[1] + y_offset, 60, 120), width=2)
            for j, color in enumerate(board.board[i]):
                y = pos[1] + 120 - (j + 1) * layer_height  
                pygame.draw.rect(surface, color, (pos[0], y + y_offset, 60, layer_height))

    
    def build_board(self):
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            title="Choose a board",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not file_path:
            return 
        
        fileBoard = None
        lines = None

        with open(file_path) as f:
            lines = f.read().split('\n', 1)  # separa na primeira linha
            fileBoard = ast.literal_eval(lines[1].strip())
        self.num_colors = int(lines[0].split('=')[1].strip())


        self.tubes_positions = []  # limpa
        self.setup_tubes()          # recalcula
        self.solver = Solver(WaterSort(fileBoard))
        

    def handle_board(self,algorithm, heuristic, weight=1):
        
        winnig_state = None

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
        board_states = []

        while winnig_state.parent is not None:
            board_states.append(winnig_state.state)
            winnig_state = winnig_state.parent
        
        board_states.append(winnig_state.state)

        self.board_solutions = board_states[::-1]


        





    

            


