"""Sample the lyrics panel across a line change: ball path and scrolling must be continuous.

python3 tests/card_line_change.py [OUTDIR]
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
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        p = await b.new_page(viewport={"width": 1400, "height": 660})
        errors = []
        p.on("pageerror", lambda e: errors.append(str(e)))
        # 40 lines, 3 s apart -> the panel has to scroll at every change
        lines = "\n".join(f"[00:{i * 3:02d}.00]Zeile {i} mit ein paar Worten zum Mitsingen" for i in range(20))
        await p.add_init_script(f"window.__longLrc = {lines!r};")
        await p.goto(f"http://127.0.0.1:{port}/tests/card_harness.html?pos=28.6")
        await p.wait_for_function("window.__card?.shadowRoot?.querySelector('.lyrics-panel .lyric-line')")
        samples = await p.evaluate("""async () => {
          const box = window.__card.shadowRoot.querySelector('.lyrics-panel .lyrics-copy');
          const ball = box.querySelector('.ball');
          const out = [];
          const t0 = performance.now();
          while (performance.now() - t0 < 3200) {
            await new Promise((r) => requestAnimationFrame(r));
            const m = /translate\\(([-\\d.]+)px, ([-\\d.]+)px\\)/.exec(ball.style.transform) || [];
            out.push({ t: Math.round(performance.now() - t0), x: +m[1], y: +m[2], s: box.scrollTop,
                       cur: box.dataset.cur, on: ball.classList.contains('on') });
          }
          return out;
        }""")
        await p.screenshot(path=str(OUT / "line_change_end.png"))
        await b.close()
    samples = [x for x in samples if x["t"] > 150]  # nach dem Einschwingen
    jumps = [(a["t"], round(((b["x"] - a["x"]) ** 2 + ((b["y"] - b["s"]) - (a["y"] - a["s"])) ** 2) ** 0.5))
             for a, b in zip(samples, samples[1:])]
    scroll_steps = [round(b["s"] - a["s"], 1) for a, b in zip(samples, samples[1:]) if b["s"] != a["s"]]
    change = next((s["t"] for a, s in zip(samples, samples[1:]) if s["cur"] != a["cur"]), None)
    print("line change at ms:", change, "| ball always visible:", all(s["on"] for s in samples))
    print("largest ball step on screen per frame (px):", max(j for _t, j in jumps))
    print("top steps:", sorted(jumps, key=lambda x: -x[1])[:4], "line change", change)
    print("scroll frames:", len(scroll_steps), "max step:", max(scroll_steps, default=0))
    print("errors:", errors or "none")


asyncio.run(main())
