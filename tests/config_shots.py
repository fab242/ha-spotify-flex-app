"""Render the settings page inside a fake Home Assistant window (light and dark theme) and
exercise speakers/groups against a mocked backend. Saves screenshots for a visual check.

python3 tests/config_shots.py OUTDIR
"""
import asyncio
import json
import sys
from pathlib import Path

from aiohttp import web
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "spotify_flex/rootfs/opt/flex/static"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "shots")

THEMES = {
    "light": "--primary-color:#03a9f4;--primary-background-color:#fafafa;--card-background-color:#fff;"
             "--primary-text-color:#212121;--secondary-text-color:#727272;--divider-color:rgba(0,0,0,.12);"
             "--secondary-background-color:#e5e5e5;--ha-card-border-radius:12px;",
    "dark": "--primary-color:#ff9800;--primary-background-color:#111111;--card-background-color:#1c1c1c;"
            "--primary-text-color:#e1e1e1;--secondary-text-color:#9b9b9b;--divider-color:rgba(225,225,225,.12);"
            "--secondary-background-color:#282828;--ha-card-border-radius:16px;"
            "--ha-card-box-shadow:0 2px 6px rgba(0,0,0,.6);",
}

DB = {
    "speakers": [
        {"id": "111", "name": "HomePod Links", "device_name": "HomePod Links", "type": "AirPlay 2", "selected": True,
         "volume": 50, "needs_pin": False, "alias": None, "hidden": False, "start_volume": None, "max_volume": None},
        {"id": "222", "name": "HomePod Rechts", "device_name": "HomePod Rechts", "type": "AirPlay 2", "selected": True,
         "volume": 50, "needs_pin": False, "alias": None, "hidden": False, "start_volume": 40, "max_volume": 80},
        {"id": "333", "name": "FabTV", "device_name": "FabTV", "type": "AirPlay 2", "selected": False,
         "volume": 50, "needs_pin": True, "alias": None, "hidden": False, "start_volume": None, "max_volume": None},
        {"id": "444", "name": "Kinderzimmer", "device_name": "Kinderzimmer", "type": "AirPlay 2", "selected": False,
         "volume": 30, "needs_pin": False, "alias": None, "hidden": True, "start_volume": None, "max_volume": 50},
    ],
    "groups": [{"id": "abcdef123456", "name": "Wohnzimmer", "speakers": ["111", "222"]}],
}
APP = {"device_name": "Home Flex", "bitrate": 320, "normalisation": True}
STATE = {
    "version": "1.6.0", "integration": "current",
    "receiver": {"running": True, "logged_in": True, "auth_code": None},
    "web": {"configured": True, "connected": True, "redirect_uri": "http://127.0.0.1:8765/callback"},
    "player": {"username": "fab242", "device_name": "Home Flex", "track": {"latency_ms": 4465}},
    "network": {"checked_at": 1792000000, "checked": 9,
                "unreachable": [{"host": "gew4-spclient.spotify.com", "ips": ["35.186.224.28"]}],
                "overrides": {"gew4-spclient.spotify.com": "35.186.224.31"}},
}


def app() -> web.Application:
    a = web.Application()

    async def parent(r):
        theme = THEMES[r.query.get("theme", "light")]
        return web.Response(content_type="text/html", text=f"""<!doctype html><html style="{theme}"><body style="margin:0;background:var(--primary-background-color)">
            <iframe src="/ingress/" style="border:0;width:100vw;height:100vh"></iframe></body></html>""")

    async def index(_r):
        return web.FileResponse(STATIC / "index.html")

    async def state(_r):
        return web.json_response(STATE)

    async def cfg(_r):
        return web.json_response(DB)

    async def cfg_put(r):
        data = await r.json()
        s = next(x for x in DB["speakers"] if x["id"] == r.match_info["oid"])
        s.update(data)
        s["name"] = s.get("alias") or s["device_name"]
        return web.json_response({"all": DB["speakers"], "groups": DB["groups"]})

    async def app_get(_r):
        return web.json_response({"settings": APP, "bitrates": [96, 160, 320]})

    async def app_put(r):
        APP.update(await r.json())
        return web.json_response({"settings": APP, "restarted": True})

    async def grp_create(r):
        data = await r.json()
        DB["groups"].append({"id": "fedcba654321", **data})
        return web.json_response({"groups": DB["groups"]})

    a.router.add_get("/parent.html", parent)
    a.router.add_get("/ingress/", index)
    a.router.add_static("/ingress/static", STATIC)
    a.router.add_get("/ingress/api/state", state)
    a.router.add_get("/ingress/api/config/speakers", cfg)
    a.router.add_put("/ingress/api/config/speakers/{oid}", cfg_put)
    a.router.add_post("/ingress/api/groups", grp_create)
    a.router.add_get("/ingress/api/config/app", app_get)
    a.router.add_put("/ingress/api/config/app", app_put)
    return a


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    runner = web.AppRunner(app())
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    errors = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        for theme, (w, h) in (("light", (1100, 900)), ("dark", (1100, 900)), ("dark", (390, 860))):
            p = await b.new_page(viewport={"width": w, "height": h})
            p.on("pageerror", lambda e: errors.append(str(e)))
            await p.goto(f"http://127.0.0.1:{port}/parent.html?theme={theme}")
            f = p.frame_locator("iframe")
            await f.locator(".card").first.wait_for()
            tag = f"{theme}_{w}"
            await p.screenshot(path=str(OUT / f"cfg_{tag}_accounts.png"))
            await f.locator('#tabs button[data-tab="speakers"]').click()
            await f.locator('.spk[data-id="222"] [data-act="spk-open"]').click()
            await p.wait_for_timeout(200)
            await p.screenshot(path=str(OUT / f"cfg_{tag}_speakers.png"))
            await f.locator('.spk[data-id="222"] input[data-key="alias"]').fill("Wohnzimmer rechts")
            await f.locator('.spk[data-id="222"] input[data-key="alias"]').press("Tab")
            await p.wait_for_timeout(300)
            await f.locator('[data-act="g-new"]').click()
            await f.locator("#g-name").fill("Überall")
            await f.locator('.editor input[value="111"]').check()
            await f.locator('.editor input[value="333"]').check()
            await p.screenshot(path=str(OUT / f"cfg_{tag}_group_edit.png"))
            await f.locator('[data-act="g-save"]').click()
            await p.wait_for_timeout(300)
            await p.screenshot(path=str(OUT / f"cfg_{tag}_groups.png"))
            await f.locator('#tabs button[data-tab="system"]').click()
            await f.locator("#receiver-cfg").wait_for()
            await p.screenshot(path=str(OUT / f"cfg_{tag}_system.png"))
            await f.locator('[data-opt="device_name"]').fill("Wohnzimmer Flex")
            await f.locator('[data-opt="device_name"]').press("Tab")
            await p.wait_for_timeout(300)
            await f.locator('[data-opt="bitrate"]').select_option("160")
            await p.wait_for_timeout(300)
            await f.locator('[data-act="opt-norm"]').click()
            await p.wait_for_timeout(300)
            await p.screenshot(path=str(OUT / f"cfg_{tag}_system_saved.png"))
            print(tag, "app options:", APP)
            APP.update({"device_name": "Home Flex", "bitrate": 320, "normalisation": True})
            bg = await f.locator("body").evaluate("e => getComputedStyle(e).backgroundColor")
            print(tag, "body background:", bg)
            await p.close()
            DB["groups"] = DB["groups"][:1]
        await b.close()
    await runner.cleanup()
    print("renamed:", next(x for x in DB["speakers"] if x["id"] == "222")["name"])
    print("errors:", errors or "none")


asyncio.run(main())
