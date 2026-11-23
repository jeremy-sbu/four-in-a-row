"""Anytime search agents. Deadlines use time.perf_counter() in seconds."""
import math
import random
from time import perf_counter

from game import winning_lines


def evaluate(board):
    """Value from the side to move. Four-cell windows shared by X and O score zero."""
    weights = (0, 1, 6, 40, 0)
    score = 0
    for line in winning_lines(board.size):
        x = board.x & line
        o = board.o & line
        if not o:
            score += weights[x.bit_count()]
        if not x:
            score -= weights[o.bit_count()]
    return score if board.turn == 'X' else -score


def ordered(board):
    center = board.size - 1
    def distance(move):
        r, c = divmod(move, board.size)
        return (2 * r - center) ** 2 + (2 * c - center) ** 2
    return sorted(board.moves(), key=distance)


def alpha_beta(board, depth, alpha, beta, deadline, first=None):
    if perf_counter() >= deadline:
        raise TimeoutError
    if board.outcome:
        value = 0 if board.outcome == 'draw' else -10000 - depth
        return value, None
    if depth == 0:
        return evaluate(board), None
    moves = ordered(board)
    if first is not None:
        moves.remove(first)
        moves.insert(0, first)
    best, best_move = -math.inf, moves[0]
    for move in moves:
        reply, _ = alpha_beta(board.play(move), depth - 1, -beta, -alpha, deadline)
        if -reply > best:
            best, best_move = -reply, move
        alpha = max(alpha, best)
        if alpha >= beta:
            break
    return best, best_move


def minimax(board, deadline, seed=0):
    moves = ordered(board)
    if not moves:
        raise ValueError("No legal move.")
    best = moves[0]
    for depth in range(1, len(moves) + 1):
        try:
            value, best = alpha_beta(board, depth, -math.inf, math.inf, deadline, best)
        except TimeoutError:
            break
        if abs(value) >= 10000:
            break
    return best


class Node:
    def __init__(self, board):
        self.board = board
        self.untried = board.moves()
        self.children = {}
        self.visits = 0
        self.points = 0.0  # Reward to the player who moved into this node.

    def select(self):
        exploration = 2 * math.log(self.visits)
        return max(self.children.values(), key=lambda n:
                   n.points / n.visits + math.sqrt(exploration / n.visits))


def mcts(board, deadline, seed=0, max_rollouts=None):
    rng = random.Random(seed)
    root = Node(board)
    if not root.untried:
        raise ValueError("No legal move.")
    fallback = rng.choice(root.untried)
    while perf_counter() < deadline and (max_rollouts is None or root.visits < max_rollouts):
        node = root
        path = [node]
        while not node.untried and node.children:
            node = node.select()
            path.append(node)
        if node.untried:
            move = node.untried.pop(rng.randrange(len(node.untried)))
            child = Node(node.board.play(move))
            node.children[move] = child
            node = child
            path.append(node)
        position = node.board
        # Shuffling the empty cells samples uniform legal moves without replacement.
        remaining = position.moves()
        rng.shuffle(remaining)
        while not position.outcome:
            position = position.play(remaining.pop())
        for visited in path:
            visited.visits += 1
            if position.outcome == 'draw':
                visited.points += 0.5
            elif position.outcome != visited.board.turn:
                visited.points += 1
    if not root.children:
        return fallback
    return max(root.children, key=lambda m: root.children[m].visits)


AGENTS = {'minimax': minimax, 'mcts': mcts}
