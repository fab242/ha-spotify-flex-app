"""Render the player card in Chromium with a fake hass and save screenshots (visual check).

python3 tests/card_shots.py OUTDIR
"""
import asyncio
import functools
import http.server
import sys
import threading
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "shots")


def serve() -> int:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    port = serve()
    base = f"http://127.0.0.1:{port}/tests/card_harness.html"
    errors: list[str] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()

        async def page(w, h, query=""):
            p = await browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            p.on("pageerror", lambda e: errors.append(str(e)))
            p.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            await p.goto(base + query)
            await p.wait_for_function("window.__card && window.__card.shadowRoot && window.__card.shadowRoot.querySelector('.surface.ready')")
            await p.wait_for_timeout(700)
            return p

        async def click(p, sel):
            await p.evaluate(f"window.__card.shadowRoot.querySelector('{sel}').click()")
            await p.wait_for_timeout(500)

        p = await page(1400, 660, "?timer=1")
        await p.screenshot(path=str(OUT / "wide.png"))
        await click(p, '[data-a="lyrics"]')
        await p.screenshot(path=str(OUT / "wide_nolyrics.png"))
        await click(p, '.transport [data-a="browse"]')
        await p.screenshot(path=str(OUT / "wide_library.png"))
        await click(p, '.item-main[data-a="open"]')
        await p.screenshot(path=str(OUT / "wide_playlist.png"))
        await click(p, '[data-a="view"]')
        await click(p, '[data-a="tab"][data-tab="search"]')
        await p.evaluate("(() => { const i = window.__card.shadowRoot.querySelector('.search-in'); i.value = 'Delerium'; })()")
        await click(p, '[data-a="do-search"]')
        await p.screenshot(path=str(OUT / "wide_search.png"))
        await click(p, '[data-a="close"]')
        await click(p, '.actions [data-a="speakers"]')
        await p.screenshot(path=str(OUT / "wide_speakers.png"))
        await click(p, '[data-a="close"]')
        await click(p, '.actions [data-a="queue"]')
        await p.screenshot(path=str(OUT / "wide_queue.png"))
        await click(p, '[data-a="close"]')
        await click(p, '.actions [data-a="timer"]')
        await p.screenshot(path=str(OUT / "wide_timer.png"))
        calls = await p.evaluate("JSON.stringify(window.__calls.map(c => [c[0], c[1]]))")
        await p.close()

        p = await page(400, 860)
        await p.screenshot(path=str(OUT / "phone.png"), full_page=True)
        await click(p, '.transport [data-a="lyrics"]')
        await p.screenshot(path=str(OUT / "phone_lyrics.png"))
        await click(p, '[data-a="close"]')
        await click(p, '.transport [data-a="browse"]')
        await p.screenshot(path=str(OUT / "phone_library.png"))
        await p.close()

        p = await page(820, 700, "?state=paused")
        await p.screenshot(path=str(OUT / "tablet.png"))
        await p.close()
        await browser.close()
    print("calls:", calls)
    print("errors:", errors or "none")


asyncio.run(main())
