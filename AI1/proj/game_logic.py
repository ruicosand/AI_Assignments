import random 
from waterSort import WaterSort


class GameController:
    def __init__(self,num = 4):
        self.selected_tube = None
        self.board = []
        self.count_moves = 0
        self.generate_tubes(num,num)

    def generate_tubes(self, num_colors = 4, size_tubes=4):
        colors = [(255,255,0), (255,0,0), (0,255,0), (0,255,255)]
        
        tubes = [colors[0],colors[0], colors[0], colors[0], colors[1], colors[1], colors[1], colors[1], colors[2], colors[2], colors[2], colors[2], colors[3], colors[3], colors[3], colors[3]]

        random.shuffle(tubes)

        self.board.append(tubes[0:4])
        self.board.append(tubes[4:8])
        self.board.append(tubes[8:12])
        self.board.append(tubes[12:16])


        for j in range (0,2):
            tube_0 = [(255,255,255) for i in range (0,4)]
            self.board.append(tube_0)
    
    

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


        