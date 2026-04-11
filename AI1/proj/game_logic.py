import random 
from waterSort import WaterSort

# Controls board generation and player interactions (tube selection + moves)
class GameController:
    def __init__(self,num_colors = 4,size_tubes = 4):
        # Currently selected tube (for move logic)
        self.selected_tube = None
        
        # Game board state (list of tubes)
        self.board = []
        
        # Number of performed moves in a single action
        self.count_moves = 0
        
        # Generate initial random board
        self.generate_tubes(num_colors, size_tubes)

    # Creates a randomized solvable-like starting board
    def generate_tubes(self, num_colors=4, size_tubes=4):
        # Available RGB colors pool
        colors_available = [
            (255,255,0), (255,0,0), (0,255,0), (0,255,255), (153,0,153), 
            (204,0,102), (102,102,0), (255, 128, 0), (153,0,0), (0,0,102)
        ]

        # Pick subset of colors depending on difficulty
        selected_colors = random.sample(colors_available, k=num_colors)

        # Repeat colors to fill tubes
        all_colors = selected_colors * size_tubes
        
        # Shuffle for randomness
        random.shuffle(all_colors)

        # Split into tubes
        self.board = []
        for i in range(0, len(all_colors), size_tubes):
            tube = all_colors[i : i + size_tubes]
            self.board.append(tube)

        # Add empty tubes (white placeholders)
        for _ in range(2):
            empty_tube = [(255, 255, 255)] * size_tubes
            self.board.append(empty_tube)

    # Handles user tube selection and performs valid moves
    def handle_click(self, tube_selected):
        # First click: select source tube
        if self.selected_tube == None:
            self.count_moves = 0
            self.selected_tube = tube_selected
        else: 

            # Clicking same tube cancels action
            if self.selected_tube == tube_selected:
                return False
                
            waterSort = WaterSort(self.board)

            # Identify top color of selected tube
            color_tube_move = waterSort.get_top(self.board[self.selected_tube])

            # Move all possible matching top colors
            while(
                waterSort.get_top(self.board[self.selected_tube]) == color_tube_move 
                and waterSort.can_move(self.selected_tube, tube_selected)
            ):
                self.count_moves += 1 
                new_board = waterSort.move_color(self.selected_tube, tube_selected)
                self.board = [list(tube) for tube in new_board.board]
                waterSort = WaterSort(self.board)
                
            # Reset selection after move attempt
            if (self.count_moves != 0):
                self.selected_tube = None
                return True
            else:
                self.selected_tube = None 
                return False
