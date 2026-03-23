import random 


class GameController:
    def __init__(self,num = 4):
        self.selected_tube = None
        self.board = []
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


    def get_top(self,tube):
        for i in range(len(tube) - 1,-1, - 1):
            if tube[i] != (255,255,255):
                    return tube[i]
        return None

    def get_top_indice(self,tube):
        for i in range(len(tube) - 1,-1, - 1):
            if tube[i] != (255,255,255):
                    return i
        return None

    def get_first_empty(self, tube):
        for i in range(len(tube)):
            if tube[i] == (255,255,255):
                return i
        return None

    def can_move(self,tube_selected):
        
        tube1 = self.board[self.selected_tube]
        tube2 = self.board[tube_selected]
        color1 = self.get_top(tube1)
        
        if color1 != None:
            color2 = self.get_top(tube2)
            if color2 == None:
                return True
            
            if color2 == color1 and self.get_top_indice(tube2) != (len(tube2) - 1):
                return True
    
        return False

    def move_color(self, tube):
        tube1 = self.board[self.selected_tube]
        tube2 = self.board[tube]
        color1 = self.get_top(tube1)
        color2 = self.get_top(tube2)
        color1_index = self.get_top_indice(tube1)
        color_2_index = self.get_first_empty(tube2)


        tube2[color_2_index] = color1 
        tube1[color1_index] = (255,255,255)
                
    def is_won(self):
        for tube in self.board:
            color_verify = self.get_top(tube)
            print(f"tubo: {tube}, top: {color_verify}, first_empty: {self.get_first_empty(tube)}")

            if color_verify is None:
                continue
            if self.get_first_empty(tube) is not None:
                return False
            for color in tube:
                if color != color_verify:
                    return False
        return True
    

    def handle_click(self, tube_selected):
        if self.selected_tube == None:
            self.selected_tube = tube_selected
        else:
            if self.can_move(tube_selected):
                self.move_color(tube_selected)
                self.selected_tube = None
                return True
            else:
                self.selected_tube = None 
                return False


        