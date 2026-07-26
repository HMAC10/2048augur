# 2048masterbot

**IN PROGRESS.** Bot for [https://2048game.online/](https://2048game.online/).

**Built:** board engine, move simulation, evaluation.
**Not built:** solver, browser driver, benchmark harness.

Repo: [https://github.com/HMAC10/2048masterbot](https://github.com/HMAC10/2048masterbot)

## 1. Why this repo exists

Most 2048 bots target Gabriele Cirulli's original open-source game, which exposes DOM tiles and predictable state. This bot targets [https://2048game.online/](https://2048game.online/), a Phaser canvas game that reuses the original's page copy. Existing bots do not work against it.

## 2. How it works

Four-step loop:

1. Read the board
2. Choose a move
3. Press an arrow key
4. Wait for the board to change

Choosing uses **expectimax**: on the bot's turn take the best of the four directions; on the game's turn take the probability-weighted average over every possible tile spawn (90% a 2, 10% a 4). Leaf boards are scored by board health, not points.

## 3. Architecture

`board.py` and `solver.py` have zero browser dependency. They operate on a single integer board. That is what allows offline benchmarking at full speed. Browser I/O (Playwright) stays in a separate driver layer and is not required to test move logic or search.

## 4. Board representation

A board is one 64-bit Python `int`: 16 cells × 4 bits. Each cell stores **log2** of the tile value (`empty=0`, tile `2→1`, `4→2`, …, `32768→15`).

Cell `(row r, col c)` occupies the 4 bits starting at bit position `60 - (r*16 + c*4)`. `(0,0)` is the highest nibble; `(3,3)` is the lowest. Row 0 is the top row; col 0 is the left column.

At import time `board.py` builds four 65536-entry row lookup tables:

| Table | Role |
| --- | --- |
| `ROW_LEFT` | row after slide/merge left |
| `ROW_RIGHT` | row after slide/merge right |
| `SCORE` | points gained from merges on a left move of that row |
| `HEUR` | row health score used by `evaluate()` |

Up/down reuse the left/right tables via `transpose()`. `evaluate(board)` sums `HEUR` over the four rows of the board and the four rows of its transpose (columns), which produces corner anchoring without an explicit corner term.

## 5. Site reverse-engineering notes

Found by diagnostic probing (not encoded as constants in the engine):

| Fact | Value |
| --- | --- |
| Engine | Phaser, rendering to canvas |
| DOM tiles | none; `.tile-container` does not exist |
| State key | `localStorage['phaser2048_game_state']` |
| Shape | `{"grid": [[...]], "score": 0, "won": false, "keepPlaying": false}` |
| Tile values | raw (`2`, `4`, `1024`), not log2 |
| `grid[0]` | top row |
| `grid[r][0]` | left column |
| Writes | on every move that changes the board; no-ops do not write |
| Arrow keys | register only after clicking the canvas for focus |
| Win overlay | DOM over the canvas: `div.game-message.game-won` with `a.keep-playing-button` ("Keep going"), not canvas-drawn |
| `keepPlaying` write | setting `keepPlaying=true` in localStorage without a reload does not dismiss the overlay or restore keys |

`won` and `keepPlaying` arrive in the same read as the board, which makes the win overlay easy to detect. The overlay must be dismissed by clicking `a.keep-playing-button`; a naive localStorage-only approach is why bots cap around 20,700 points — one tile short of continuing past 2048.

## 6. Setup

Python 3.10+.

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
playwright install chromium
```

## 7. Usage

```bash
pytest
python live_board.py
```

`live_board.py` watches parsed board state while you play manually. The bot itself is not runnable yet.

## 8. Roadmap

- [x] Site reverse-engineering
- [x] Bitboard
- [x] Move simulation validated against naive reference
- [x] Evaluation function
- [ ] Expectimax with adaptive depth
- [ ] Offline benchmark harness
- [ ] Playwright driver
- [ ] Empirical weight tuning
- [ ] Optional canvas vision adapter

## 9. Testing approach

`board.py` ships `naive_move`, a deliberately slow nested-list implementation. The suite asserts both paths agree across 2000 random boards in all four directions. Bit-manipulation bugs are silent: they do not raise; they just make the bot play slightly wrong moves that are nearly impossible to diagnose from outside.

## 10. Credits

The bitboard-plus-lookup-table architecture and heuristic shape follow [nneonneo/2048-ai](https://github.com/nneonneo/2048-ai). Weight starting values are informed by [qpwoeirut/2048-solver](https://github.com/qpwoeirut/2048-solver). No code was copied from either.

## 11. License

MIT
