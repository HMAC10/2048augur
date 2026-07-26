"""Expectimax solver with time-budgeted iterative deepening."""
from __future__ import annotations

import time

from board import empty_positions, evaluate, move, set_cell

PROB_CUTOFF = 0.0001
DEFAULT_BUDGET_MS = 200
MAX_DEPTH = 8
NODE_CAP = 2_000_000

_tt: dict[tuple[int, int], float] = {}
_nodes = 0
_deadline = 0.0
_node_cap = NODE_CAP
last_depth = 0
last_nodes = 0


class SearchAborted(Exception):
    pass


def _max_node(board: int, depth: int, cprob: float) -> float:
    best = None
    for d in range(4):
        new_board, _ = move(board, d)
        if new_board == board:
            continue
        v = _chance_node(new_board, depth, cprob)
        if best is None or v > best:
            best = v
    return 0.0 if best is None else best


def _chance_node(board: int, depth: int, cprob: float) -> float:
    global _nodes
    _nodes += 1
    if _nodes > _node_cap:
        raise SearchAborted
    if (_nodes & 4095) == 0 and time.perf_counter() >= _deadline:
        raise SearchAborted

    key = (board, depth)
    if key in _tt:
        return _tt[key]

    if depth == 0 or cprob < PROB_CUTOFF:
        val = evaluate(board)
        _tt[key] = val
        return val

    cells = empty_positions(board)
    if not cells:
        val = evaluate(board)
        _tt[key] = val
        return val

    n = len(cells)
    total = 0.0
    for cell in cells:
        for rank, p in ((1, 0.9), (2, 0.1)):
            child = set_cell(board, cell, rank)
            total += p * _max_node(child, depth - 1, cprob * p / n)
    val = total / n
    _tt[key] = val
    return val


def best_move(
    board: int,
    budget_ms: int = DEFAULT_BUDGET_MS,
    max_depth: int = MAX_DEPTH,
) -> int:
    global _tt, _nodes, _deadline, _node_cap, last_depth, last_nodes

    legal: list[tuple[int, int]] = []
    for d in range(4):
        new_board, _ = move(board, d)
        if new_board != board:
            legal.append((d, new_board))
    if not legal:
        last_depth = 0
        last_nodes = 0
        return -1

    _tt = {}
    last_depth = 0
    last_nodes = 0
    best = -1
    t0 = time.perf_counter()
    deadline = t0 + budget_ms / 1000.0

    for depth in range(2, max_depth + 1):
        _nodes = 0
        if depth == 2:
            _deadline = float("inf")
            _node_cap = 10**18
        else:
            _deadline = deadline
            _node_cap = NODE_CAP

        try:
            best_v = None
            best_d = -1
            for d, new_board in legal:
                v = _chance_node(new_board, depth, 1.0)
                if best_v is None or v > best_v:
                    best_v = v
                    best_d = d
            best = best_d
            last_depth = depth
            last_nodes += _nodes
        except SearchAborted:
            last_nodes += _nodes
            break

        if time.perf_counter() >= deadline:
            break

    return best
