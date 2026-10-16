"""Smoke test of the app backend against fake go-librespot / OwnTone services."""
import asyncio
import json

from pathlib import Path

import aiohttp
import pytest
from aiohttp import web


from flex import const, groups, hassbridge, oauth, server, speakercfg  # noqa: E402

CALLS = []
STATE = {"outputs": [{"id": "111", "name": "HomePod Links", "type": "AirPlay", "selected": False, "volume": 40,
                      "needs_auth_key": False, "requires_auth": False, "has_password": False},
                     {"id": "222", "name": "Badezimmer", "type": "AirPlay 2", "selected": False, "volume": 50},
                     {"id": "100", "name": "fifo", "type": "fifo", "selected": False}]}


async def fake_librespot():
    app = web.Application()

    async def root(_r):
        return web.json_response({"playback_ready": True})

    async def status(_r):
        return web.json_response({"username": "31layadatnwuzptlp4qhdsxk7beq", "device_id": "dev1", "device_name": "Home Flex",
                                  "stopped": False, "paused": False, "buffering": False, "volume": 60, "volume_steps": 100,
                                  "repeat_context": False, "repeat_track": False, "shuffle_context": False,
                                  "track": {"uri": "spotify:track:T1", "name": "Closer", "artist_names": ["Nine Inch Nails"],
                                            "album_name": "The Downward Spiral", "album_cover_url": "https://i/x.jpg",
                                            "position": 1000, "duration": 373306}})

    async def post(r):
        CALLS.append((r.path, await r.json() if r.can_read_body else None))
        return web.Response(status=200)

    async def events(r):
        ws = web.WebSocketResponse()
        await ws.prepare(r)
        await ws.send_json({"type": "playing", "data": {}})
        await asyncio.sleep(3600)
        return ws

    app.router.add_get("/", root)
    app.router.add_get("/status", status)
    app.router.add_get("/events", events)
    app.router.add_post("/{tail:.*}", post)
    return app


async def fake_owntone():
    app = web.Application()

    async def outputs(_r):
        return web.json_response({"outputs": STATE["outputs"]})

    async def put_output(r):
        data = await r.json()
        for o in STATE["outputs"]:
            if o["id"] == r.match_info["oid"]:
                o.update({k: v for k, v in data.items() if k in ("selected", "volume")})
        return web.Response(status=204)

    async def set_outputs(r):
        ids = (await r.json())["outputs"]
        for o in STATE["outputs"]:
            o["selected"] = o["id"] in ids
        return web.Response(status=204)

    app.router.add_get("/api/outputs", outputs)
    app.router.add_put("/api/outputs/set", set_outputs)
    app.router.add_put("/api/outputs/{oid}", put_output)
    return app


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_backend_flow(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(const, "TOKEN_FILE", str(tmp_path / "tok.json"))
        monkeypatch.setattr(oauth, "TOKEN_FILE", str(tmp_path / "tok.json"))
        monkeypatch.setattr(server, "OPTIONS_FILE", str(tmp_path / "opt.json"))
        monkeypatch.setattr(groups, "GROUPS_FILE", str(tmp_path / "groups.json"))
        monkeypatch.setattr(hassbridge, "API_TOKEN_FILE", str(tmp_path / "api_token"))
        monkeypatch.setattr(speakercfg, "SPEAKERS_FILE", str(tmp_path / "speakers.json"))
        (tmp_path / "opt.json").write_text(json.dumps({"client_id": "abc123", "device_name": "Home Flex",
                                                       "ha_integration": False}))
        runners = []
        for factory, port in ((fake_librespot, 3678), (fake_owntone, 3689)):
            runner = web.AppRunner(await factory())
            await runner.setup()
            await web.TCPSite(runner, "127.0.0.1", port).start()
            runners.append(runner)
        app = server.build_app()
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "127.0.0.1", 8099).start()
        base = "http://127.0.0.1:8099/"
        try:
            async with aiohttp.ClientSession() as anon:
                async with anon.get(base + "api/state") as r:
                    assert r.status == 401  # localhost (= HA core) needs the API token
            token = (tmp_path / "api_token").read_text()
            async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {token}"}) as s:
                async with s.get(base) as r:
                    html = await r.text()
                    assert r.status == 200 and "Spotify Flex" in html
                    assert f"static/app.js?v={const.VERSION}" in html and f"static/style.css?v={const.VERSION}" in html
                async with s.get(base + "static/../flex/server.py") as r:
                    assert r.status == 404
                async with s.get(base + "static/app.js") as r:
                    assert r.status == 200
                async with s.get(base + "api/state") as r:
                    st = await r.json()
                assert st["receiver"]["logged_in"] is True
                assert st["web"] == {"configured": True, "connected": False, "redirect_uri": "http://127.0.0.1:8765/callback"}
                assert st["player"]["track"]["name"] == "Closer" and st["player"]["playing"] is True
                assert [o["name"] for o in st["speakers"]] == ["Badezimmer", "HomePod Links"]  # fifo hidden
                assert st["groups"] == [] and st["active_group"] is None
                # groups: create from two speakers, activate, detect, then switch all off
                async with s.post(base + "api/groups", json={"name": "Überall", "speakers": ["111", "222"]}) as r:
                    res = await r.json()
                gid = res["group"]["id"]
                async with s.post(base + "api/groups", json={"name": "überall", "speakers": ["111"]}) as r:
                    assert r.status == 409
                async with s.post(base + f"api/groups/{gid}/activate", json={}) as r:
                    res = await r.json()
                assert {o["id"] for o in res["speakers"] if o["selected"]} == {"111", "222"}
                assert res["active_group"] == gid
                async with s.post(base + "api/speakers", json={"speakers": ["222"]}) as r:
                    res = await r.json()
                assert [o["id"] for o in res["speakers"] if o["selected"]] == ["222"] and res["active_group"] is None
                async with s.put(base + f"api/groups/{gid}", json={"name": "Bad"}) as r:
                    assert (await r.json())["groups"][0]["name"] == "Bad"
                async with s.delete(base + f"api/groups/{gid}") as r:
                    assert (await r.json())["groups"] == []
                # speaker settings: rename, cap volume, start volume, hide
                async with s.put(base + "api/config/speakers/111",
                                 json={"alias": "Wohnzimmer links", "max_volume": 60, "start_volume": 70}) as r:
                    res = await r.json()
                cfg = next(x for x in res["all"] if x["id"] == "111")
                assert cfg["name"] == "Wohnzimmer links" and cfg["device_name"] == "HomePod Links"
                assert cfg["max_volume"] == 60 and cfg["start_volume"] == 60  # start never above max
                async with s.post(base + "api/speakers/111", json={"volume": 95}) as r:
                    assert r.status == 200
                assert next(o for o in STATE["outputs"] if o["id"] == "111")["volume"] == 60
                async with s.post(base + "api/speakers", json={"speakers": []}) as r:
                    pass
                async with s.post(base + "api/speakers", json={"speakers": ["111"]}) as r:
                    pass
                assert next(o for o in STATE["outputs"] if o["id"] == "111")["volume"] == 60
                async with s.put(base + "api/config/speakers/222", json={"hidden": True}) as r:
                    assert r.status == 200
                async with s.get(base + "api/state") as r:
                    assert [o["name"] for o in (await r.json())["speakers"]] == ["Wohnzimmer links"]
                async with s.get(base + "api/config/speakers") as r:
                    assert {o["id"] for o in (await r.json())["speakers"]} == {"111", "222"}
                async with s.put(base + "api/config/speakers/999", json={"hidden": True}) as r:
                    assert r.status == 404
                async with s.put(base + "api/config/speakers/222", json={"hidden": False}) as r:
                    assert r.status == 200
                async with s.get(base + "api/ha/token") as r:
                    assert r.status == 403  # token only visible through ingress
                async with s.post(base + "api/speakers", json={"speakers": []}) as r:
                    assert r.status == 200
                async with s.post(base + "api/web/authorize") as r:
                    url = (await r.json())["url"]
                assert "code_challenge_method=S256" in url and "client_id=abc123" in url
                async with s.post(base + "api/speakers/111", json={"selected": True, "volume": 55}) as r:
                    spk = next(o for o in (await r.json())["speakers"] if o["id"] == "111")
                assert spk["selected"] is True and spk["volume"] == 55
                async with s.post(base + "api/play", json={"uri": "spotify:track:T2", "context_uri": "spotify:playlist:P1"}) as r:
                    res = await r.json()
                assert res["warning"] is None
                assert ("/player/play", {"uri": "spotify:playlist:P1", "skip_to_uri": "spotify:track:T2"}) in CALLS
                async with s.post(base + "api/player/volume", json={"percent": 30}) as r:
                    assert r.status == 200
                assert ("/player/volume", {"volume": 30}) in CALLS
                async with s.post(base + "api/player/repeat", json={"mode": "track"}) as r:
                    assert r.status == 200
                async with s.post(base + "api/play", json={"uri": "javascript:alert(1)"}) as r:
                    assert r.status == 400
                async with s.get(base + "api/browse?node=playlists") as r:
                    assert r.status == 401 and "nicht verbunden" in (await r.json())["error"]
                async with s.ws_connect(base + "ws?token=" + token) as ws:
                    msg = await ws.receive_json(timeout=5)
                    assert msg["type"] == "status"
        finally:
            await runner.cleanup()
            for rn in runners:
                await rn.cleanup()

    asyncio.run(run())
