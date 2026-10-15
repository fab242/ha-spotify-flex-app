import asyncio, functools, http.server, threading
from playwright.async_api import async_playwright
from pathlib import Path
ROOT=str(Path(__file__).resolve().parent.parent)
h=functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); h.log_message=lambda *a:None
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),h); threading.Thread(target=srv.serve_forever,daemon=True).start()
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(); p=await b.new_page(viewport={"width":1400,"height":660})
        # first two lrclib calls (get + search) for the new track fail, later ones succeed
        await p.add_init_script("window.__silence = 0; window.__lrcHook = (u) => !u.includes('Silence') || (++window.__silence > 2);")
        await p.goto(f"http://127.0.0.1:{srv.server_address[1]}/tests/card_harness.html")
        await p.wait_for_function("window.__card && window.__card.shadowRoot.querySelector('.surface.ready')")
        await p.wait_for_timeout(600)
        await p.evaluate("""() => { const h = window.__hass; const old = h.states['media_player.spotify_flex_player'];
          const st = {...old, attributes: {...old.attributes, media_title: 'Silence', media_artist: 'Delerium', media_content_id: 'spotify:track:T2'}};
          window.__card.hass = {...h, states: {...h.states, 'media_player.spotify_flex_player': st}}; }""")
        info = "() => { const box = window.__card.shadowRoot.querySelector('.lyrics-panel .lyrics-copy'); return {lines: box.querySelectorAll('.lyric-line').length, msg: (box.querySelector('.lmsg')||{}).textContent, calls: window.__lrc}; }"
        await p.wait_for_timeout(1000); print("1s", await p.evaluate(info))
        await p.wait_for_timeout(6500); print("7.5s", await p.evaluate(info))
        await b.close()
asyncio.run(main())
