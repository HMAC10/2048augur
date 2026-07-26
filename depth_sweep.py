"""Sweep time budgets vs completed search depth on a fixed board set."""
from __future__ import annotations

import random
import statistics
import time

import solver
from board import is_game_over, move, spawn_tile
from solver import best_move

SEED = 42
SNAP_EVERY = 40
N_BOARDS = 25
GEN_BUDGET_MS = 50
BUDGETS_MS = [1, 5, 10, 20, 50, 100, 200, 400, 800, 1600]


def collect_positions() -> list[int]:
    rng = random.Random(SEED)
    board = 0
    board = spawn_tile(board, rng)
    board = spawn_tile(board, rng)
    boards: list[int] = []
    moves = 0
    while len(boards) < N_BOARDS:
        d = best_move(board, budget_ms=GEN_BUDGET_MS)
        if d == -1:
            break
        board, _ = move(board, d)
        moves += 1
        board = spawn_tile(board, rng)
        if moves % SNAP_EVERY == 0:
            boards.append(board)
        if is_game_over(board):
            break
    return boards


def main() -> None:
    boards = collect_positions()
    print(f"fixed boards: {len(boards)} (seed={SEED}, every {SNAP_EVERY} moves @ {GEN_BUDGET_MS}ms)")
    if not boards:
        print("no boards collected")
        return

    header = (
        f"{'budget_ms':>10} | {'avg_depth':>9} | {'min_depth':>9} | "
        f"{'max_depth':>9} | {'avg_ms':>8} | {'avg_nodes':>12}"
    )
    print(header)
    print("-" * len(header))

    avg_depth_by_budget: dict[int, float] = {}
    for budget in BUDGETS_MS:
        depths: list[int] = []
        times_ms: list[float] = []
        nodes: list[int] = []
        for board in boards:
            t0 = time.perf_counter()
            best_move(board, budget_ms=budget)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            depths.append(solver.last_depth)
            times_ms.append(elapsed_ms)
            nodes.append(solver.last_nodes)
        avg_d = statistics.mean(depths)
        avg_depth_by_budget[budget] = avg_d
        print(
            f"{budget:10d} | {avg_d:9.2f} | {min(depths):9d} | "
            f"{max(depths):9d} | {statistics.mean(times_ms):8.1f} | "
            f"{statistics.mean(nodes):12.1f}"
        )

    d20 = avg_depth_by_budget[20]
    d1600 = avg_depth_by_budget[1600]
    ratio = d1600 / d20 if d20 else float("inf")
    print(
        f"Avg depth at 1600ms is {ratio:.2f}x the avg depth at 20ms "
        f"({d1600:.2f} vs {d20:.2f})."
    )


if __name__ == "__main__":
    main()
