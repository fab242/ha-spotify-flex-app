"""Card options (width/align, depth, buttons, background, ball) and the visual editor.

python3 tests/card_editor.py OUTDIR
"""
import asyncio
import functools
import http.server
import json
import sys
import threading
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "shots")

FAKE_FORM = """
customElements.define('ha-form', class extends HTMLElement {
  set data(d) { this._data = d; window.__formData = d; }
  get data() { return this._data; }
  set schema(s) { window.__formSchema = s; }
});
"""


def serve() -> int:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    port = serve()
    errors = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        p = await b.new_page(viewport={"width": 1400, "height": 700})
        p.on("pageerror", lambda e: errors.append(str(e)))
        extra = {"width": 70, "align": "center", "depth": "raised", "background": "plain",
                 "buttons": ["speakers", "eq"], "karaoke_ball": False}
        await p.add_init_script(f"window.__extraConfig = {json.dumps(extra)};")
        await p.goto(f"http://127.0.0.1:{port}/tests/card_harness.html")
        await p.wait_for_function("window.__card?.shadowRoot?.querySelector('.surface.ready')")
        await p.wait_for_timeout(800)
        info = await p.evaluate("""() => {
          const r = window.__card.shadowRoot;
          const card = r.querySelector('ha-card').getBoundingClientRect(), host = window.__card.getBoundingClientRect();
          return { ratio: +(card.width / host.width).toFixed(2), leftGap: Math.round(card.left - host.left), rightGap: Math.round(host.right - card.right),
                   buttons: [...r.querySelectorAll('.actions [data-a]')].map((x) => x.dataset.a),
                   raised: window.__card.classList.contains('depth-raised'), art: window.__card.classList.contains('has-art'),
                   ball: r.querySelector('.lyrics-panel .ball')?.classList.contains('on') };
        }""")
        print("card:", info)
        assert info["ratio"] == 0.7 and abs(info["leftGap"] - info["rightGap"]) <= 1
        assert info["buttons"] == ["speakers", "eq"] and info["raised"] and not info["art"] and not info["ball"]
        await p.screenshot(path=str(OUT / "card_options.png"))

        # editor with a stand-in ha-form
        await p.evaluate(FAKE_FORM)
        res = await p.evaluate("""async () => {
          const Card = customElements.get('spotify-flex-flow-card');
          const ed = Card.getConfigElement();
          document.body.appendChild(ed);
          ed.setConfig({ type: 'custom:spotify-flex-flow-card', entity: 'media_player.spotify_flex_player', grid_options: { columns: 'full' } });
          ed.hass = window.__card._hass;
          await new Promise((r) => setTimeout(r, 50));
          let got = null;
          ed.addEventListener('config-changed', (e) => { got = e.detail.config; });
          const form = ed.querySelector('ha-form');
          form.dispatchEvent(new CustomEvent('value-changed', { detail: { value: { ...window.__formData, width: 75, depth: 'inset', cover_intensity: 'normal' } } }));
          const names = []; const walk = (s) => s.forEach((x) => { if (x.schema) walk(x.schema); else names.push(x.name); }); walk(window.__formSchema);
          return { got, names, defaultsShown: window.__formData.height === 600 && window.__formData.align === 'center' };
        }""")
        print("editor:", res)
        g = res["got"]
        assert g["width"] == 75 and g["cover_intensity"] == "normal" and g["grid_options"] == {"columns": "full"}
        assert "height" not in g and "depth" not in g and g["type"] == "custom:spotify-flex-flow-card"  # defaults not written
        assert res["defaultsShown"] and {"entity", "width", "buttons", "karaoke_ball"} <= set(res["names"])
        await b.close()
    print("errors:", errors or "none")
    assert not errors


asyncio.run(main())
