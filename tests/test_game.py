import json
import math
import unittest
from collections import Counter

from agents import AGENTS, alpha_beta, evaluate, mcts
from benchmark import CASES, answer_key
from game import Board, example, replay


class RulesTests(unittest.TestCase):
    def test_wins_in_all_directions_on_all_sizes(self):
        for n in (4, 5, 6):
            for step, start in ((1, n*n-4), (n, n-1), (n+1, 0), (n-1, n-1)):
                target = [start + j * step for j in range(4)]
                filler = iter(i for i in range(n*n) if i not in target)
                history = []
                for move in target[:3]:
                    history.extend([move, next(filler)])
                board = replay(n, history + target[-1:])
                self.assertEqual(board.outcome, 'X')
                self.assertFalse(board.moves())
                with self.assertRaises(ValueError):
                    board.play(1)

    def test_no_wraparound_or_illegal_moves(self):
        board = replay(4, [3, 0, 4, 1, 5, 8, 6])
        self.assertFalse(board.outcome)
        for bad in (-1, 16, 3, '1', True):
            with self.assertRaises(ValueError):
                board.play(bad)

    def test_last_square_win_and_draw(self):
        draw = [12, 13, 6, 0, 5, 11, 10, 9, 7, 4, 3, 15, 2, 14, 1, 8]
        win = [11, 14, 1, 0, 12, 2, 6, 5, 4, 9, 7, 3, 8, 15, 13, 10]
        self.assertEqual(replay(4, draw).outcome, 'draw')
        self.assertEqual(replay(4, win).outcome, 'O')

    def test_examples_and_held_out_cases(self):
        data = json.loads(CASES.read_text())
        counts = Counter()
        seen = {example(n, t) for n in (4, 5, 6) for t in ('win', 'block')}
        for n in (4, 5, 6):
            self.assertEqual(answer_key(example(n, 'win')), ('win', {3}))
            self.assertEqual(answer_key(example(n, 'block')), ('block', {n + 3}))
        for case in data:
            board = replay(case['size'], case['history'])
            self.assertNotIn(board, seen)
            seen.add(board)
            tactic, answers = answer_key(board)
            self.assertEqual(case['tactic'], tactic)
            self.assertTrue(answers)
            counts[board.size, tactic] += 1
        self.assertEqual(counts, {(n, t): 5 for n in (4, 5, 6) for t in ('win', 'block')})


def plain_value(board, depth):
    if board.outcome:
        return 0 if board.outcome == 'draw' else -10000 - depth
    if depth == 0:
        return evaluate(board)
    return max(-plain_value(board.play(move), depth-1) for move in board.moves())


class AgentTests(unittest.TestCase):
    def test_alpha_beta_against_exhaustive_minimax(self):
        for tactic in ('win', 'block'):
            board = example(4, tactic)
            value, move = alpha_beta(board, 3, -math.inf, math.inf, math.inf)
            self.assertEqual(value, plain_value(board, 3))
            self.assertIn(move, answer_key(board)[1])

    def test_mcts_repeatability_and_opponent_perspective(self):
        cases = [([14, 13, 8, 15, 7, 9, 11, 3, 2, 12, 6, 5], 10),
                 ([6, 9, 2, 15, 7, 14, 11, 12, 4, 3, 8, 5], 13)]
        for history, expected in cases:
            board = replay(4, history)
            # The first position has one winning move. The second has one drawing
            # move and three moves that lose against a correct opponent.
            values = {m: -plain_value(board.play(m), 3) for m in board.moves()}
            self.assertEqual([m for m in values if values[m] == max(values.values())], [expected])
            for _ in range(2):
                self.assertEqual(mcts(board, math.inf, seed=17, max_rollouts=500), expected)

    def test_expired_deadline_and_finished_game(self):
        for choose in AGENTS.values():
            for n in (4, 5, 6):
                board = example(n, 'win')
                self.assertIn(choose(board, 0), board.moves())
                with self.assertRaises(ValueError):
                    choose(board.play(3), 0)


if __name__ == '__main__':
    unittest.main()
