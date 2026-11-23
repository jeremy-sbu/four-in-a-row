# Four in a Row

Jeremy and Depinder · CSE 352 · Stony Brook University

## Project overview

Does spotting an immediate threat predict how well an agent plays a full game? We compared minimax and Monte Carlo tree search (MCTS) on 4×4, 5×5, and 6×6 boards. With 250 ms per move, both agents found a winning move or a forced block in all 30 tactical positions. Under the same time budget, minimax won all six recorded 6×6 games, including the three in which it played second.

[Run the project](#run-the-project)

## Game rules

Four in a Row is like tic-tac-toe, but the goal is to line up four of your marks instead of three. Start with an empty square board. X goes first, then X and O take turns placing one mark on any empty square. Marks stay where they are placed; they do not drop to the bottom of a column.

A player wins as soon as four of their marks occupy consecutive squares in a row, in a column, or along either diagonal. On a larger board, the four marks do not need to span the whole board. If the last empty square is filled without a win, the game ends in a draw. [Game rules](game.py)

## Search agents

**Minimax.** The agent looks for the move that leaves it in the best position after the opponent’s strongest reply. At the depth limit, it scores each four-square segment. An unblocked segment with one, two, or three friendly marks earns 1, 6, or 40 points, respectively. Opposing segments subtract the same values. This gives an immediate threat more weight than several promising pairs. A known win or loss takes priority over any estimate.

The agent starts by comparing moves one turn ahead, then looks one turn deeper with each pass. If it finds an opponent reply that makes a move worse than an alternative it already has, it can skip the remaining replies to that move. When time runs out, it uses the best move from the deepest pass it finished.

**Monte Carlo tree search.** Instead of scoring patterns on the board, we built this agent to learn about moves by playing out possible games. Each simulation follows a sequence of moves, tries an unexplored move when one is available, then plays random legal moves until someone wins or the board fills. The result counts toward each move in the sequence from the perspective of the player who made it, with a draw counting halfway between a win and a loss.

Once the agent has tried every legal move from a position, it uses Upper Confidence Bounds applied to Trees (UCT) to decide which move to explore next. UCT adds an exploration bonus to each move’s average reward. Moves with fewer visits get a larger bonus. When time runs out, the agent plays the most-visited move at the root of the search tree. [Agent implementations](agents.py)

## Experiments and findings

### Immediate wins and forced blocks

We used five immediate-win positions and five forced-block positions on each board size, for 30 distinct positions. On a win trial, the scoring code accepted any move that completed four in a row. On a block trial, the player had no immediate win and had to remove every threat that could win on the opponent’s next turn. [Saved positions](data/positions.json) · [Scoring code](benchmark.py)

Each row combines the three board sizes. Minimax played each of the 15 positions once. MCTS played those same positions with three random seeds (11, 23, and 47), giving 45 decisions per row. The last two columns show measured time per decision. [Trial data](data/results.csv)

| Time budget | Task | Minimax correct (1 run per position) | MCTS correct (3 seeds per position) | Minimax median time | MCTS median time |
|---:|---|---:|---:|---:|---:|
| 250 ms | Win in one move | 15/15 | 45/45 | 0.03 ms | 250.10 ms |
| 250 ms | Block a win | 15/15 | 45/45 | 15.25 ms | 251.50 ms |
| 1,000 ms | Win in one move | 15/15 | 45/45 | 0.04 ms | 1,000.17 ms |
| 1,000 ms | Block a win | 15/15 | 45/45 | 15.94 ms | 1,007.99 ms |

Both agents solved every position at 250 ms, leaving no room for the longer budget to improve accuracy on this set. The timing results show a difference that accuracy alone misses. Minimax could prove an immediate win after searching one move ahead and return early. MCTS kept sampling until its time budget expired. It checks the clock between simulations, so a final simulation can finish slightly over budget.

### Full games

We played six games from an empty board at each size, giving each agent 250 ms per move. For each of the three seeds, the agents played twice and swapped colors so each went first once. [Match runner](matches.py) · [Complete move histories](data/head_to_head.csv)

| Board | Minimax wins | MCTS wins | Draws |
|---|---:|---:|---:|
| 4×4 | 0 | 0 | 6 |
| 5×5 | 1 | 0 | 5 |
| 6×6 | 6 | 0 | 0 |
| **Total** | **7** | **0** | **11** |

The tactical trials tested whether each agent could spot a win or block in one move. Full games also required the agents to anticipate threats. In the first 6×6 game, minimax built a diagonal of three with both ends open. MCTS could cover only one end on its turn.

Minimax won the recorded 6×6 games playing both first and second. With six games per size and a single head-to-head time budget, the series leaves open how often that advantage would persist with more seeds or longer searches.

## Run the project

Use Python 3.10 or later from the repository root. The game and experiments use the standard library. The desktop interface also requires a Python installation with Tkinter.

```sh
python3 gui.py                              # Desktop game
python3 play.py --size 5 --agent mcts       # Terminal game
python3 -m unittest -v                      # Rules, search, and benchmark tests
python3 benchmark.py --summary              # Summarize the saved tactical trials
```

In the desktop game, select **Load block** and **Compare moves** to see both agents’ suggestions for the same turn. To watch two complete games with the agents swapping colors, run `python3 matches.py --sizes 5 --seeds 11 --watch`.

To repeat the tactical experiment, run `python3 benchmark.py`. It replaces `data/results.csv`. To repeat the full match series and save a separate copy, run `python3 matches.py --output new_matches.csv`. Fixed seeds determine the random sequences, but the number of simulations completed within a time budget can vary between runs.
