"""Rules for 4-in-a-row on a square board. Moves are row-major cell indices."""
from dataclasses import dataclass
from functools import lru_cache


@lru_cache(maxsize=None)
def winning_lines(size):
    lines = []
    for row in range(size):
        for col in range(size):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if 0 <= row + 3 * dr < size and 0 <= col + 3 * dc < size:
                    lines.append(sum(1 << ((row + i * dr) * size + col + i * dc)
                                     for i in range(4)))
    return tuple(lines)


@lru_cache(maxsize=None)
def lines_at(size, move):
    return tuple(line for line in winning_lines(size) if line & (1 << move))


@dataclass(frozen=True)
class Board:
    size: int
    x: int = 0
    o: int = 0
    turn: str = 'X'
    outcome: str = ''  # X, O, draw, or empty while play continues

    def __post_init__(self):
        if self.size not in (4, 5, 6):
            raise ValueError("Choose board size 4, 5, or 6.")

    def cell(self, move):
        bit = 1 << move
        return 'X' if self.x & bit else 'O' if self.o & bit else '.'

    def moves(self):
        if self.outcome:
            return []
        occupied = self.x | self.o
        return [i for i in range(self.size ** 2) if not occupied & (1 << i)]

    def play(self, move):
        if self.outcome:
            raise ValueError("The game has ended.")
        if type(move) is not int or not 0 <= move < self.size ** 2:
            raise ValueError("Choose a square inside the board.")
        bit = 1 << move
        if (self.x | self.o) & bit:
            raise ValueError("That square is occupied.")
        x, o = self.x, self.o
        if self.turn == 'X':
            x |= bit
            marks, following = x, 'O'
        else:
            o |= bit
            marks, following = o, 'X'
        outcome = ''
        if any(marks & line == line for line in lines_at(self.size, move)):
            outcome = self.turn
        elif (x | o).bit_count() == self.size ** 2:
            outcome = 'draw'
        return Board(self.size, x, o, following, outcome)


def replay(size, history):
    board = Board(size)
    for move in history:
        board = board.play(move)
    return board


def example(size, tactic):
    # X has three marks in the top row, or O threatens the second row.
    history = [0, size, 1, size + 1, 2, 2 * size]
    if tactic == 'block':
        history = [0, size, size ** 2 - 1, size + 1, 2, size + 2]
    return replay(size, history)


def coordinates(size, move):
    return (move // size + 1, move % size + 1)
