import random 
from waterSort import WaterSort


class GameController:
    def __init__(self,num_colors = 4,size_tubes = 4):
        self.selected_tube = None
        self.board = []
        self.count_moves = 0
        self.generate_tubes(num_colors, size_tubes)


    def generate_tubes(self, num_colors=4, size_tubes=4):
        colors_available = [
            (255,255,0), (255,0,0), (0,255,0), (0,255,255), (153,0,153), 
            (204,0,102), (102,102,0), (255, 128, 0), (153,0,0), (0,0,102)
        ]

        selected_colors = random.sample(colors_available, k=num_colors)

        all_colors = selected_colors * size_tubes
        
        random.shuffle(all_colors)

        self.board = []
        for i in range(0, len(all_colors), size_tubes):
            tube = all_colors[i : i + size_tubes]
            self.board.append(tube)

        for _ in range(2):
            empty_tube = [(255, 255, 255)] * size_tubes
            self.board.append(empty_tube)

    def handle_click(self, tube_selected):
        if self.selected_tube == None:
            self.count_moves = 0
            self.selected_tube = tube_selected
        else: 

            if self.selected_tube == tube_selected:
                return False
                
            waterSort = WaterSort(self.board)

            color_tube_move = waterSort.get_top(self.board[self.selected_tube])

            while(waterSort.get_top(self.board[self.selected_tube]) == color_tube_move and waterSort.can_move(self.selected_tube, tube_selected)):
                self.count_moves += 1 
                new_board = waterSort.move_color(self.selected_tube, tube_selected)
                self.board = [list(tube) for tube in new_board.board]
                waterSort = WaterSort(self.board)
                
            if (self.count_moves != 0):
                self.selected_tube = None
                return True
            else:
                self.selected_tube = None 
                return False


        