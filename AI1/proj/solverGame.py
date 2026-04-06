
import pygame 
from game_logic import GameController
from waterSort import WaterSort
from Menu.background import Background
from solver import Solver

def calculate_space(width,size):
        total_space = ( size / 3) * 60
        remaining_space = width - total_space
        
        remaining_space = remaining_space / 4

        return (total_space, remaining_space)

class SolverGame:
    def __init__(self, width, height):
        self.controller = GameController()
        self.solver = Solver(WaterSort(self.controller.board))
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

        for i, pos in enumerate(self.tubes_positions):
            if i == self.controller.selected_tube:
                border_color = (255, 255, 255)
                y_offset = -20  
            else:
                border_color = (0, 0, 0)
                y_offset = 0

            pygame.draw.rect(surface, border_color, (pos[0], pos[1] + y_offset, 60, 120), width=2)
            for j, color in enumerate(board.board[i]):
                y = pos[1] + 120 - (j + 1) * 30
                pygame.draw.rect(surface,color,(pos[0],y + y_offset,60,30))

    
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
        

        board_states = []

        while winnig_state.parent is not None:
            board_states.append(winnig_state.state)
            winnig_state = winnig_state.parent
        
        board_states.append(winnig_state.state)

        self.board_solutions = board_states[::-1]


        





    

            


