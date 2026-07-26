import json
from playwright.sync_api import sync_playwright

def read_grid(page):
    raw = page.evaluate("() => localStorage.getItem('phaser2048_game_state')")
    return json.loads(raw) if raw else None

def print_grid(label, state):
    print(label)
    if state is None:
        print("(no state)"); return
    for row in state["grid"]:
        print("".join(f"{n:5d}" for n in row))
    print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://2048game.online/")
    page.evaluate("() => localStorage.removeItem('phaser2048_game_state')")
    page.reload(); page.wait_for_timeout(2000)
    page.locator("canvas").first.click()
    changes, left_last, final_score, prev = 0, None, None, None
    try:
        state = read_grid(page)
        prev = state["grid"] if state else None
        final_score = state["score"] if state else None
        print_grid("starting grid", state)
        for n in range(1, 5):
            page.keyboard.press("ArrowLeft"); page.wait_for_timeout(600)
            state = read_grid(page); print_grid(f"after LEFT #{n}", state)
            grid = state["grid"] if state else None
            if grid != prev: changes += 1
            prev, left_last = grid, grid
            final_score = state["score"] if state else final_score
        for n in range(1, 5):
            page.keyboard.press("ArrowUp"); page.wait_for_timeout(600)
            state = read_grid(page); print_grid(f"after UP #{n}", state)
            grid = state["grid"] if state else None
            if grid != prev: changes += 1
            prev = grid
            final_score = state["score"] if state else final_score
    except Exception as e:
        print(f"move sequence error: {e}")
    left_hint = "unknown"
    if left_last is not None:
        g = left_last
        col0 = sum(1 for r in range(4) if g[r][0])
        row0 = sum(1 for c in range(4) if g[0][c])
        o_col = sum(1 for r in range(4) for c in range(1, 4) if g[r][c])
        o_row = sum(1 for r in range(1, 4) for c in range(4) if g[r][c])
        if col0 and not o_col:
            left_hint = "nonzero concentrated in grid[r][0] (array LEFT col)"
        elif row0 and not o_row:
            left_hint = "nonzero concentrated in grid[0][c] (array TOP row)"
        else:
            left_hint = f"mixed; col0={col0} row0={row0} o_col={o_col} o_row={o_row}"
    print("=== VERDICT ===")
    print(f"presses that changed grid: {changes}/8")
    print(f"grid ever changed: {'yes' if changes else 'no'}")
    print(f"after LEFT presses: {left_hint}")
    print(f"final score: {final_score}")
    page.wait_for_timeout(4000)
    browser.close()
