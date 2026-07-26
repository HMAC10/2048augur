"""Tests for time-budgeted expectimax solver."""
from __future__ import annotations

import time

import solver
from board import from_grid, move
from solver import best_move


def _mid_game_board() -> int:
    return from_grid(
        [
            [16, 8, 4, 2],
            [8, 4, 2, 0],
            [4, 2, 0, 0],
            [2, 0, 0, 0],
        ]
    )


def _dead_board() -> int:
    return from_grid(
        [
            [2, 4, 8, 16],
            [32, 64, 128, 256],
            [512, 1024, 2048, 4096],
            [8192, 16384, 32768, 2],
        ]
    )


def _easy_board() -> int:
    return from_grid(
        [
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 2],
        ]
    )


def _fullish_board() -> int:
    return from_grid(
        [
            [64, 32, 16, 8],
            [32, 16, 8, 4],
            [16, 8, 4, 2],
            [8, 4, 2, 0],
        ]
    )


def test_best_move_legal_on_midgame():
    board = _mid_game_board()
    d = best_move(board, budget_ms=200)
    assert d in (0, 1, 2, 3)
    new_board, _ = move(board, d)
    assert new_board != board


def test_best_move_no_legal():
    assert best_move(_dead_board(), budget_ms=200) == -1


def test_generous_budget_searches_past_depth_2():
    board = _easy_board()
    d = best_move(board, budget_ms=2000, max_depth=8)
    assert d in (0, 1, 2, 3)
    new_board, _ = move(board, d)
    assert new_board != board
    assert solver.last_depth > 2


def test_tiny_budget_still_legal():
    board = _mid_game_board()
    d = best_move(board, budget_ms=1)
    assert d in (0, 1, 2, 3)
    assert d != -1
    new_board, _ = move(board, d)
    assert new_board != board


def test_budget_not_wildly_exceeded():
    board = _fullish_board()
    budget_ms = 50
    for _ in range(20):
        t0 = time.perf_counter()
        d = best_move(board, budget_ms=budget_ms)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert d in (0, 1, 2, 3)
        assert elapsed_ms <= 3 * budget_ms
