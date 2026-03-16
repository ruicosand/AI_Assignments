

class WaterSortState:


    def __init__(self, board, move_history=[]):
        self.board = tuple(tuple(bottle) for bottle in board)
      

    def __hash__(self):
        # to be able to use the state in sets we use tuples for efficiency and performance 
        return hash(self.board)

    
    def __eq__(self, other):
        # compares each tuples of the board
        return self.board == other.board
    



