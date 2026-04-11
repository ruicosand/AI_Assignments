from waterSort import TreeNode
from waterSort import WaterSort
from collections import deque
import heapq
import time

# Class responsible for solving the Water Sort puzzle using different search strategies
class Solver:

    def __init__(self, inital_state):
        # Initial board configuration
        self.initialBoard = inital_state
        # Metrics for performance evaluation
        self.time_execution = 0
        self.expanded_nodes = 0
        self.generated_nodes = 0

    # ---------------- HEURISTICS ----------------
    # Each heuristic estimates how far a given state is from the goal

    def heuristic_1(self, state):
        # Counts color changes inside tubes (fewer is better)
        from waterSort import EMPTY
        total_changes = 0
        for tube in state.board:
            real_colors = [c for c in tube if c != EMPTY]
            for i in range(len(real_colors) - 1):
                if real_colors[i] != real_colors[i + 1]:
                    total_changes += 1
        return total_changes

    def heuristic_2(self, state):
        # Counts how many tubes contain mixed colors
        from waterSort import EMPTY
        count_tubes = 0
        for tube in state.board:
            colors = set(c for c in tube if c != EMPTY)
            if len(colors) > 1:
                count_tubes += 1
        return count_tubes

    def heuristic_3(self, state):
        # Combined heuristic
        return self.heuristic_1(state) + self.heuristic_2(state)

    # ---------------- A* SEARCH ----------------

    def a_star_search(self, heuristic):
        # Reset metrics
        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        root.cost = 0

        # Priority queue based on f = g + h
        queue = []
        counter = 0
        heapq.heappush(queue, (heuristic(root.state), counter, root))
        counter += 1

        visited_states = {}
        time1 = time.perf_counter()

        # Main loop
        while queue:
            _, _, current_board = heapq.heappop(queue)

            # Skip if already visited with lower cost
            if current_board.state in visited_states and visited_states[current_board.state] <= current_board.cost:
                continue

            visited_states[current_board.state] = current_board.cost
            self.expanded_nodes += 1

            # Goal check
            if current_board.state.is_won():
                self.time_execution = time.perf_counter() - time1
                return current_board

            # Expand neighbors
            for state, move in current_board.state.generate_boards(current_board.last_move):
                child_board = TreeNode(state)
                self.generated_nodes += 1
                child_board.parent = current_board
                child_board.cost = current_board.cost + 1
                child_board.last_move = move
                h = heuristic(state)
                f = child_board.cost + h
                current_board.add_child(child_board, 1, h)
                heapq.heappush(queue, (f, counter, child_board))
                counter += 1

        self.time_execution = time.perf_counter() - time1
        return None

    # ---------------- WEIGHTED A* SEARCH ----------------

    def weigth_star_search(self, heuristic, weight):
        # Similar to A*, but heuristic is weighted
        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        root.cost = 0

        queue = []
        counter = 0
        heapq.heappush(queue, (weight * heuristic(root.state), counter, root))
        counter += 1

        visited_states = {}
        time1 = time.perf_counter()

        while queue:
            _, _, current_board = heapq.heappop(queue)

            if current_board.state in visited_states and visited_states[current_board.state] <= current_board.cost:
                continue

            visited_states[current_board.state] = current_board.cost
            self.expanded_nodes += 1

            if current_board.state.is_won():
                self.time_execution = time.perf_counter() - time1
                return current_board

            for state, move in current_board.state.generate_boards(current_board.last_move):
                child_board = TreeNode(state)
                self.generated_nodes += 1
                child_board.parent = current_board
                child_board.cost = current_board.cost + 1
                child_board.last_move = move
                h = heuristic(state)
                f = child_board.cost + weight * h
                current_board.add_child(child_board, 1, h)
                heapq.heappush(queue, (f, counter, child_board))
                counter += 1

        self.time_execution = time.perf_counter() - time1
        return None

    # ---------------- GREEDY SEARCH ----------------

    def greedy_search(self, heuristic):
        # Always expands the node with the best heuristic value
        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        queue = []
        counter = 0
        heapq.heappush(queue, (heuristic(root.state), counter, root))
        counter += 1

        visited_states = set()
        time1 = time.perf_counter()

        while queue:
            _, _, current_board = heapq.heappop(queue)

            if current_board.state in visited_states:
                continue

            visited_states.add(current_board.state)
            self.expanded_nodes += 1

            if current_board.state.is_won():
                self.time_execution = time.perf_counter() - time1
                return current_board

            for state, move in current_board.state.generate_boards(current_board.last_move):
                child_board = TreeNode(state)
                self.generated_nodes += 1
                child_board.parent = current_board
                child_board.last_move = move
                h = heuristic(state)
                current_board.add_child(child_board, 1, h)
                heapq.heappush(queue, (h, counter, child_board))
                counter += 1

        self.time_execution = time.perf_counter() - time1
        return None

    # ---------------- BREADTH-FIRST SEARCH ----------------

    def bfs_search(self):
        # Explore states layer by layer
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

            for state, move in current_board.state.generate_boards(current_board.last_move):
                child_board = TreeNode(state)
                self.generated_nodes += 1
                child_board.parent = current_board
                child_board.last_move = move
                current_board.add_child(child_board)
                queue.append(child_board)

        self.time_execution = time.perf_counter() - time1
        return None

    # ---------------- DEPTH-FIRST SEARCH ----------------

    def dfs_search(self):
        # Explores as deep as possible before backtracking
        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        stack = [root]
        visited_states = set()
        time1 = time.perf_counter()

        while stack:
            current_board = stack.pop()

            if current_board.state in visited_states:
                continue

            visited_states.add(current_board.state)
            self.expanded_nodes += 1

            if current_board.state.is_won():
                self.time_execution = time.perf_counter() - time1
                return current_board

            for state, move in current_board.state.generate_boards(current_board.last_move):
                child_board = TreeNode(state)
                self.generated_nodes += 1
                child_board.parent = current_board
                child_board.last_move = move
                current_board.add_child(child_board)
                stack.append(child_board)

        self.time_execution = time.perf_counter() - time1
        return None

    # ---------------- UNIFORM COST SEARCH ----------------

    def uniform_cost_search(self):
        # Expands nodes in order of lowest path cost
        self.expanded_nodes = 0
        self.generated_nodes = 0
        self.time_execution = 0

        root = TreeNode(self.initialBoard)
        root.cost = 0

        queue = []
        counter = 0
        heapq.heappush(queue, (0, counter, root))
        counter += 1

        visited_states = {}
        time1 = time.perf_counter()

        while queue:
            current_cost, _, current_board = heapq.heappop(queue)

            if current_board.state in visited_states and visited_states[current_board.state] <= current_cost:
                continue

            visited_states[current_board.state] = current_cost
            self.expanded_nodes += 1

            if current_board.state.is_won():
                self.time_execution = time.perf_counter() - time1
                return current_board

            for state, move in current_board.state.generate_boards(current_board.last_move):
                child_board = TreeNode(state)
                self.generated_nodes += 1
                child_board.parent = current_board
                child_board.cost = current_cost + 1
                child_board.last_move = move
                current_board.add_child(child_board, 1, 0)
                heapq.heappush(queue, (child_board.cost, counter, child_board))
                counter += 1

        self.time_execution = time.perf_counter() - time1
        return None
