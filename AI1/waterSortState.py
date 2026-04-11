# Represents an immutable state of the Water Sort puzzle
# This class is mainly used for search algorithms (BFS, DFS, A*, etc.)
# It allows states to be stored in sets and dictionaries efficiently
class WaterSortState:

    def __init__(self, board, move_history=[]):
        # Store board as tuple of tuples to make it immutable and hashable
        # Each tube is represented as a tuple of colors
        self.board = tuple(tuple(bottle) for bottle in board)

    # Hash function allows this object to be used in sets and as dict keys
    def __hash__(self):
        # Using tuple-based representation ensures fast and stable hashing
        return hash(self.board)

    # Equality check between two states
    def __eq__(self, other):
        # Two states are equal if their board configurations are identical
        return self.board == other.board
