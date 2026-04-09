from waterSort import TreeNode
from waterSort import WaterSort
from collections import deque
import time


class Solver:


    def __init__(self, inital_state):
        self.initialBoard = inital_state
        self.time_execution = 0
        self.expanded_nodes = 0
        self.generated_nodes = 0


    def heuristic_1(self, state):
        empty = (255, 255, 255)
        total_changes = 0

        for tube in state.board:
            real_colors = [c for c in tube if c != empty]  
            for i in range(len(real_colors) - 1):
                if real_colors[i] != real_colors[i + 1]:
                    total_changes += 1

        return total_changes
            
    def heuristic_2(self, state):
        count_tubes = 0
        empty = (255, 255, 255)

        for tube in state.board:
            colors = set(c for c in tube if c != empty)  
            if len(colors) > 1:
                count_tubes += 1

        return count_tubes

    def heuristic_3(self, board):
        return self.heuristic_1(board) + self.heuristic_2(board)
    

    def a_star_search(self,heuristic):

        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        queue = [(root,0 + heuristic(root.state))]

        visited_states = set()

        time1 = time.perf_counter()

        while queue:
            current_board, _ = queue.pop(0)
            
            self.expanded_nodes += 1

            if current_board.state in visited_states:
                continue
            

            visited_states.add(current_board.state)
            
            if current_board.state.is_won():

                time2 = time.perf_counter()
                self.time_execution = time2 - time1

                return current_board


            possible_boards = current_board.state.generate_boards()


            for state in possible_boards:
                child_board = TreeNode(state)

                self.generated_nodes += 1

                child_board.parent = current_board
                
                heuristic_value = heuristic(state)

                current_board.add_child(child_board, 1, heuristic_value)

                queue.append([child_board,current_board.cost + 1 + heuristic_value])
            
            queue = sorted(queue, key=lambda x: x[1])

        time2 = time.perf_counter()
        self.time_execution = time2 - time1

        return None

    def weigth_star_search(self,heuristic, weight):

        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        queue = [(root,0 + weight * heuristic(root.state))]

        visited_states = set()

        time1 = time.perf_counter()

        while queue:
            current_board, _ = queue.pop(0)

            self.expanded_nodes += 1

            if current_board.state in visited_states:
                continue
            

            visited_states.add(current_board.state)
            
            if current_board.state.is_won():

                time2 = time.perf_counter()
                self.time_execution = time2 - time1

                return current_board


            possible_boards = current_board.state.generate_boards()


            for state in possible_boards:
                child_board = TreeNode(state)

                self.generated_nodes += 1

                child_board.parent = current_board
                
                heuristic_value = heuristic(state)

                current_board.add_child(child_board, 1, heuristic_value)

                queue.append([child_board,current_board.cost + 1 + weight * heuristic_value])
            
            queue = sorted(queue, key=lambda x: x[1])

        time2 = time.perf_counter()
        self.time_execution = time2 - time1

        return None

    def greedy_search(self, heuristic):

        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        queue = [(root, heuristic(root.state))]

        visited_states = set()
  
        time1 = time.perf_counter()

        while queue:
            current_board, _ = queue.pop(0)
            
            self.expanded_nodes += 1

            if current_board.state in visited_states:
                continue
            

            visited_states.add(current_board.state)
            
            if current_board.state.is_won():
                       
                time2 = time.perf_counter()
                self.time_execution = time2 - time1

                return current_board


            possible_boards = current_board.state.generate_boards()


            for state in possible_boards:
                child_board = TreeNode(state)
                self.generated_nodes += 1

                child_board.parent = current_board
                
                heuristic_value = heuristic(state)

                current_board.add_child(child_board, 1, heuristic_value)

                queue.append([child_board,heuristic_value])
            
            queue = sorted(queue, key=lambda x: x[1])

        time2 = time.perf_counter()
        self.time_execution = time2 - time1

        return None
    
    def bfs_search(self):
        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        queue = deque([root])
        visited_states = set()

        time1 = time.perf_counter()

        while queue:
            current_board = queue.popleft()

            if current_board.state in visited_states:
                continue

            visited_states.add(current_board.state)
            self.expanded_nodes += 1

            if current_board.state.is_won():
                self.time_execution = time.perf_counter() - time1
                return current_board

            for state in current_board.state.generate_boards():
                child_board = TreeNode(state)
                self.generated_nodes += 1
                child_board.parent = current_board
                current_board.add_child(child_board)
                queue.append(child_board)

        self.time_execution = time.perf_counter() - time1
        return None
    

    def dfs_search(self):
        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        visited_states = set()

        time1 = time.perf_counter()

        result = self.dfs_recursive(root, visited_states)

        self.time_execution = time.perf_counter() - time1

        return result

    def dfs_recursive(self, node, visited_states):
        if node.state in visited_states:
            return None

        visited_states.add(node.state)
        self.expanded_nodes += 1

        if node.state.is_won():
            return node

        for state in node.state.generate_boards():
            child_board = TreeNode(state)
            self.generated_nodes += 1
            child_board.parent = node
            node.add_child(child_board)

            result = self.dfs_recursive(child_board, visited_states)

            if result is not None:
                return result

        return None


    def uniform_cost_search(self):
        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        queue = [(root, 0)]
        visited_states = set()

        time1 = time.perf_counter()

        while queue:
            current_board, current_cost = queue.pop(0)

            if current_board.state in visited_states:
                continue

            visited_states.add(current_board.state)
            self.expanded_nodes += 1

            if current_board.state.is_won():
                self.time_execution = time.perf_counter() - time1
                return current_board

            for state in current_board.state.generate_boards():
                child_board = TreeNode(state)
                self.generated_nodes += 1
                child_board.parent = current_board
                current_board.add_child(child_board, 1, 0)
                queue.append((child_board, current_cost + 1))

            queue = sorted(queue, key=lambda x: x[1])

        self.time_execution = time.perf_counter() - time1
        
        return None

    