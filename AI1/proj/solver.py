from waterSort import TreeNode
from waterSort import WaterSort



class Solver:


    def __init__(self, inital_state):
        self.initialBoard = inital_state

    def heuristic_1(self, state):
        changes_in_tube = 0
        total_changes = 0

        for tube in state.board:
            for i in range(0,len(tube)-1,1):
                if tube[i] != tube[i + 1]:
                    changes_in_tube += 1
            
            total_changes += changes_in_tube
        
        return total_changes
            
    def heuristic_2(self,state):
        count_tubes = 0

        for tube in state.board:
            color_verify = state.get_top(tube)

            if color_verify is None:
                continue

            if state.get_first_empty(tube) is not None:
                count_tubes += 1
                continue

            for color in tube:
                if color != color_verify:
                    count_tubes += 1
    
        return count_tubes

    def heuristic_3(self, board):
        return self.heuristic_1(board) + self.heuristic_2(board)
    

    def a_star_search(self,initial_board,heuristic):
        root = TreeNode(initial_board)
        queue = [(root,0 + heuristic(root.state))]

        visited_states = set()
  
        while queue:
            current_board, _ = queue.pop(0)

            if current_board.state in visited_states:
                continue
            

            visited_states.add(current_board.state)
            
            if current_board.state.is_won():
                return current_board


            possible_boards = current_board.state.generate_boards()


            for state in possible_boards:
                child_board = TreeNode(state)

                child_board.parent = current_board
                
                heuristic_value = heuristic(state)

                current_board.add_child(child_board, 1, heuristic_value)

                queue.append([child_board,current_board.cost + 1 + heuristic_value])
            
            queue = sorted(queue, key=lambda x: x[1])

        return None

    def weigth_star_search(self,initial_board,heuristic, weight):
        root = TreeNode(initial_board)
        queue = [(root,0 + weight * heuristic(root.state))]

        visited_states = set()
  
        while queue:
            current_board, _ = queue.pop(0)

            if current_board.state in visited_states:
                continue
            

            visited_states.add(current_board.state)
            
            if current_board.state.is_won():
                return current_board


            possible_boards = current_board.state.generate_boards()


            for state in possible_boards:
                child_board = TreeNode(state)

                child_board.parent = current_board
                
                heuristic_value = heuristic(state)

                current_board.add_child(child_board, 1, heuristic_value)

                queue.append([child_board,current_board.cost + 1 + weight * heuristic_value])
            
            queue = sorted(queue, key=lambda x: x[1])

        return None

    def greedy_search(self, initial_board, heuristic):
        root = TreeNode(initial_board)
        queue = [(root, heuristic(root.state))]

        visited_states = set()
  
        while queue:
            current_board, _ = queue.pop(0)

            if current_board.state in visited_states:
                continue
            

            visited_states.add(current_board.state)
            
            if current_board.state.is_won():
                return current_board


            possible_boards = current_board.state.generate_boards()


            for state in possible_boards:
                child_board = TreeNode(state)

                child_board.parent = current_board
                
                heuristic_value = heuristic(state)

                current_board.add_child(child_board, 1, heuristic_value)

                queue.append([child_board,heuristic_value])
            
            queue = sorted(queue, key=lambda x: x[1])

        return None

    