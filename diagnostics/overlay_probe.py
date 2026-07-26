"""Probe the 2048 win overlay: DOM vs canvas, localStorage keepPlaying."""
from __future__ import annotations

import json
from playwright.sync_api import sync_playwright

URL = "https://2048game.online/"
KEY = "phaser2048_game_state"
NEAR = {"grid": [[1024, 1024, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        "score": 20000, "won": False, "keepPlaying": False}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_load_state("load")

    print("=== STEP 1 - force near-win ===")
    try:
        page.evaluate("([k,v]) => localStorage.setItem(k,v)", [KEY, json.dumps(NEAR)])
        page.reload()
        page.wait_for_timeout(2000)
        page.locator("canvas").first.click()
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(2000)
        print("near-win merge attempted")
    except Exception as e:
        print(f"STEP 1 error: {e}")

    print("=== STEP 2 - report what appeared ===")
    try:
        raw = page.evaluate(f"() => localStorage.getItem({KEY!r})")
        print("--- localStorage ---")
        print(json.dumps(json.loads(raw), indent=2) if raw else None)
        print("--- visible text elements (max 40) ---")
        els = page.evaluate("""() => {
            const out = [];
            for (const el of document.body.querySelectorAll('*')) {
                const r = el.getBoundingClientRect();
                const st = getComputedStyle(el);
                if (st.visibility === 'hidden' || st.display === 'none' || r.width <= 0 || r.height <= 0) continue;
                const t = (el.innerText || '').trim();
                if (!t) continue;
                out.push({tag: el.tagName, id: el.id, class: el.className, text: t.slice(0, 120)});
                if (out.length >= 40) break;
            }
            return out;
        }""")
        for e in els:
            print(repr(e).encode("ascii", "replace").decode())
        buttons = page.evaluate("""() => Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim())""")
        print(f"--- button count: {len(buttons)} ---")
        for t in buttons:
            print(repr(t).encode("ascii", "replace").decode())
        print("--- Keep/Continue matches ---")
        matches = page.evaluate("""() => {
            const re = /keep|continue/i;
            return Array.from(document.body.querySelectorAll('*'))
                .filter(el => re.test((el.innerText || '').slice(0, 80)))
                .slice(0, 10)
                .map(el => el.outerHTML.slice(0, 500));
        }""")
        print(repr(matches).encode("ascii", "replace").decode())
        page.screenshot(path="overlay_state.png", full_page=True)
        print("saved overlay_state.png")
    except Exception as e:
        print(f"STEP 2 error: {e}")

    print("=== STEP 3 - keepPlaying without reload ===")
    try:
        before = page.evaluate(f"() => JSON.parse(localStorage.getItem({KEY!r})).grid")
        page.evaluate(f"""() => {{
            const s = JSON.parse(localStorage.getItem({KEY!r}));
            s.keepPlaying = true;
            localStorage.setItem({KEY!r}, JSON.stringify(s));
        }}""")
        page.wait_for_timeout(500)
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(1000)
        after = page.evaluate(f"() => JSON.parse(localStorage.getItem({KEY!r})).grid")
        print(f"grid changed: {before != after}")
    except Exception as e:
        print(f"STEP 3 error: {e}")

    page.wait_for_timeout(5000)
    browser.close()
