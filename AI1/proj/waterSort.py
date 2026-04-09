

class TreeNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.cost = 0   
        self.depth = 0
        self.heuristic_value = 0
        self.f = 0
    
    def add_child(self, child_node, operator_cost=0, heuristic_value=0):
        self.children.append(child_node)
        child_node.cost = self.cost + operator_cost  
        child_node.depth = self.depth + 1
        child_node.heuristic_value = heuristic_value
        child_node.f = child_node.heuristic_value + child_node.cost
        child_node.parent = self
        


class WaterSort:

    def __init__(self, board, move_history=[]):
        self.board = tuple(tuple(bottle) for bottle in board)


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

    def can_move(self,tube_to_move,tube_to_receive):
        
        tube1 = self.board[tube_to_move]
        tube2 = self.board[tube_to_receive]
        color1 = self.get_top(tube1)   
        if color1 != None:
            color2 = self.get_top(tube2)
            if color2 == None:
                return True
            
            if color2 == color1 and self.get_top_indice(tube2) != (len(tube2) - 1):
                return True
    
        return False

    
    def move_color(self,tube_to_move, tube_to_receive):

        new_board = [list(tube) for tube in self.board]

        tube1 = new_board[tube_to_move]
        tube2 = new_board[tube_to_receive]
        color1 = self.get_top(tube1)
        color1_index = self.get_top_indice(tube1)
        color_2_index = self.get_first_empty(tube2)


        tube2[color_2_index] = color1 
        tube1[color1_index] = (255,255,255)


        return WaterSort(new_board)


    def is_won(self):
        
        for tube in self.board:
            color_verify = self.get_top(tube)

            if color_verify is None:
                continue
            if self.get_first_empty(tube) is not None:
                return False
            for color in tube:
                if color != color_verify:
                    return False
        return True
    


    def generate_boards(self):
        child_boards = []
        
        for i in range(len(self.board)):
            for j in range(len(self.board)):
                if i != j:
                    state_temp = self
                    color_tube_move = self.get_top(self.board[i])
                    while(state_temp.get_top(state_temp.board[i]) == color_tube_move and state_temp.can_move(i, j)): 
                        state_temp = state_temp.move_color(i, j)
                    
                    if state_temp != self:
                        child_boards.append(state_temp)

        return child_boards

    def __hash__(self):
        return hash(self.board)

    
    def __eq__(self, other):
        return self.board == other.board