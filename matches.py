"""Play full games between minimax and MCTS, swapping colors for each seed."""
import argparse
import csv
from collections import Counter
from pathlib import Path
from time import perf_counter

from agents import AGENTS
from game import Board, coordinates
from play import display


def play_match(size, x_agent, o_agent, seed, budget_ms, watch=False):
    board = Board(size)
    players = {'X': x_agent, 'O': o_agent}
    moves = []
    if watch:
        print(f'\n{size}×{size} · X = {x_agent}, O = {o_agent}, seed {seed}', flush=True)
    while not board.outcome:
        agent = players[board.turn]
        # Each MCTS turn has its own random stream, paired by turn across colors.
        turn_seed = seed + len(moves) // 2
        move = AGENTS[agent](board, perf_counter() + budget_ms / 1000, turn_seed)
        if watch:
            print(f'{agent} ({board.turn}) plays {coordinates(size, move)}')
        board = board.play(move)
        moves.append(move)
        if watch:
            display(board)
            print(flush=True)
    return dict(size=size, seed=seed, budget_ms=budget_ms, x_agent=x_agent, o_agent=o_agent,
                outcome=board.outcome, winner=players.get(board.outcome, 'draw'),
                moves=' '.join(map(str, moves)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sizes', nargs='+', type=int, choices=(4, 5, 6), default=[4, 5, 6])
    parser.add_argument('--seeds', nargs='+', type=int, default=[11, 23, 47])
    parser.add_argument('--budget-ms', type=int, default=250)
    parser.add_argument('--watch', action='store_true', help='show the board after every move')
    parser.add_argument('--output', type=Path, help='save game histories to a CSV file')
    args = parser.parse_args()
    if args.budget_ms <= 0:
        parser.error('Choose a positive time budget.')
    rows = []
    print('Size   Minimax wins   MCTS wins   Draws', flush=True)
    for size in args.sizes:
        counts = Counter()
        for seed in args.seeds:
            for x, o in [('minimax', 'mcts'), ('mcts', 'minimax')]:
                row = play_match(size, x, o, seed, args.budget_ms, args.watch)
                rows.append(row)
                counts[row['winner']] += 1
        print(f"{size:4}   {counts['minimax']:12}   {counts['mcts']:9}   {counts['draw']:5}", flush=True)
    if args.output:
        with args.output.open('w', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == '__main__':
    main()
