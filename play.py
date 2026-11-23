"""Play four-in-a-row, load a tactical position, or compare the agents."""
import argparse
from time import perf_counter

from agents import AGENTS
from game import Board, coordinates, example


def choose(board, agent):
    return AGENTS[agent](board, perf_counter() + 0.25, seed=11)


def display(board):
    print('  ' + ' '.join(str(c + 1) for c in range(board.size)))
    for row in range(board.size):
        print(row + 1, ' '.join(board.cell(row * board.size + col) for col in range(board.size)))
    if board.outcome:
        print('Draw.' if board.outcome == 'draw' else f'{board.outcome} wins.')
    else:
        print(f'{board.turn} to move.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, choices=(4, 5, 6), default=4)
    parser.add_argument('--agent', choices=AGENTS, default='mcts')
    args = parser.parse_args()
    board = Board(args.size)
    print('You play X. Enter row and column (1-based), compare, win, block, restart, or quit.')
    while True:
        display(board)
        try:
            command = input('> ').strip().lower()
        except EOFError:
            break
        if command == 'quit':
            break
        if command in ('win', 'block', 'restart'):
            board = Board(args.size) if command == 'restart' else example(args.size, command)
            continue
        if board.outcome:
            print('Enter restart, win, block, or quit.')
            continue
        if command == 'compare':
            for name in AGENTS:
                print(f'{name} suggests {coordinates(board.size, choose(board, name))}')
            continue
        try:
            row, col = map(int, command.split())
            if not 1 <= row <= board.size or not 1 <= col <= board.size:
                raise ValueError
            board = board.play((row - 1) * board.size + col - 1)
        except ValueError:
            print('Enter a legal row and column, for example 1 2.')
            continue
        if not board.outcome:
            move = choose(board, args.agent)
            print(f'{args.agent} plays {coordinates(board.size, move)}')
            board = board.play(move)


if __name__ == '__main__':
    main()
