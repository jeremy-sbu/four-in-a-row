"""Generate reproducible tactical cases, time both agents, and summarize raw trials."""
import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from time import perf_counter

from agents import AGENTS
from game import Board, example, lines_at, replay

DATA = Path(__file__).resolve().parent / 'data'
CASES = DATA / 'positions.json'
RESULTS = DATA / 'results.csv'
SEEDS = (11, 23, 47)


def threats(board, mark):
    owned = board.x if mark == 'X' else board.o
    return {m for m in board.moves()
            if any(((owned | (1 << m)) & line) == line for line in lines_at(board.size, m))}


def answer_key(board):
    wins = threats(board, board.turn)
    if wins:
        return 'win', wins
    opponent = 'O' if board.turn == 'X' else 'X'
    if threats(board, opponent):
        blocks = {m for m in board.moves() if not threats(board.play(m), opponent)}
        if blocks:
            return 'block', blocks
    return '', set()


def generate_cases():
    rng = random.Random(352)
    cases = []
    for size in (4, 5, 6):
        seen = {example(size, tactic) for tactic in ('win', 'block')}
        for tactic in ('win', 'block'):
            for index in range(5):
                # Approximately 40%-60% occupancy, alternating the side to move.
                plies = max(6, round(size * size * (0.40 + index * 0.05)))
                plies += (plies + index) % 2
                while True:
                    history = rng.sample(range(size * size), plies)
                    try:
                        board = replay(size, history)
                    except ValueError:
                        continue
                    if board.outcome or board in seen or answer_key(board)[0] != tactic:
                        continue
                    seen.add(board)
                    cases.append(dict(id=f'{size}-{tactic}-{index+1}', size=size,
                                      tactic=tactic, history=history))
                    break
    return cases


def measure(cases, budgets):
    for budget in budgets:
        for case in cases:
            board = replay(case['size'], case['history'])
            tactic, answers = answer_key(board)
            if tactic != case['tactic']:
                raise ValueError(f"Incorrect tactic for {case['id']}")
            for agent, choose in AGENTS.items():
                for seed in (SEEDS if agent == 'mcts' else (None,)):
                    start = perf_counter()
                    move = choose(board, start + budget / 1000, seed)
                    elapsed = (perf_counter() - start) * 1000
                    yield dict(position=case['id'], size=board.size, tactic=tactic,
                               budget_ms=budget, agent=agent, seed=seed, move=move,
                               correct=int(move in answers), elapsed_ms=round(elapsed, 3))


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[int(row['budget_ms']), int(row['size']), row['tactic'],
               row['agent'], str(row['seed'])].append(int(row['correct']))
    print('Budget(ms)  Size  Tactic   Minimax   MCTS (seed 11 / 23 / 47)')
    for budget, size, tactic in sorted({k[:3] for k in groups}):
        def count(agent, seed):
            values = groups[budget, size, tactic, agent, seed]
            return f'{sum(values)}/{len(values)}'
        rates = '   '.join(count('mcts', str(seed)) for seed in SEEDS)
        print(f"{budget:10}  {size:4}  {tactic:6}   {count('minimax', ''):7}   {rates}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true', help='read the saved results')
    parser.add_argument('--budgets', nargs='+', type=int, default=[250, 1000], metavar='MS')
    args = parser.parse_args()
    if not args.summary:
        if any(b <= 0 for b in args.budgets) or len(set(args.budgets)) != len(args.budgets):
            parser.error('Budgets must be positive and distinct.')
        if not CASES.exists():
            CASES.write_text(json.dumps(generate_cases(), indent=2) + '\n')
        cases = json.loads(CASES.read_text())
        rows = list(measure(cases, args.budgets))
        temporary = RESULTS.with_suffix('.tmp')
        with temporary.open('w', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(RESULTS)
    with RESULTS.open(newline='') as source:
        summarize(csv.DictReader(source))


if __name__ == '__main__':
    main()
