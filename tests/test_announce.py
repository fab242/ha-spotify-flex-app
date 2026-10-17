import asyncio

import pytest

from flex import announce
from flex.announce import AnnounceError, Announcer


class FakeOwnTone:
    def __init__(self, play_for=0.3):
        self.outs = [{"id": "1", "name": "L", "selected": True, "volume": 60},
                     {"id": "2", "name": "R", "selected": True, "volume": 55},
                     {"id": "3", "name": "Bad", "selected": False, "volume": 40}]
        self.log, self.play_for, self.until = [], play_for, 0.0

    async def outputs(self):
        return [dict(o) for o in self.outs]

    async def set_output(self, oid, volume=None, **_):
        self.log.append(("vol", oid, volume))
        for o in self.outs:
            if o["id"] == oid and volume is not None:
                o["volume"] = volume

    async def play_url(self, url):
        self.log.append(("play", url, {o["id"]: o["volume"] for o in self.outs if o["selected"]}))
        self.until = asyncio.get_running_loop().time() + self.play_for

    async def player(self):
        return {"state": "play" if asyncio.get_running_loop().time() < self.until else "stop"}

    async def stop(self):
        self.log.append(("stop",)); self.until = 0

    async def clear_queue(self):
        self.log.append(("clear",))


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(announce, "POLL", 0.05)
    monkeypatch.setattr(announce, "START_TIMEOUT", 0.5)


def make(ot):
    calls = []

    async def pause():
        calls.append("pause")

    async def group(name):
        calls.append(("group", name))

    return Announcer(ot, pause, group), calls


def test_items_validation():
    assert announce._items("http://x/a.mp3") == [{"url": "http://x/a.mp3", "volume": None}]
    assert announce._items([{"url": "https://x/b", "volume": "35"}])[0]["volume"] == 35
    for bad in ([], "media-source://tts/x", [{"url": "ftp://x"}], [{"url": "http://x", "volume": "laut"}]):
        with pytest.raises(AnnounceError):
            announce._items(bad)


def test_plays_in_order_with_volume_and_restores():
    async def run():
        ot = FakeOwnTone()
        an, calls = make(ot)
        res = await an.play([{"url": "http://h/tts.wav", "volume": 35}, {"url": "http://h/news.mp3", "volume": 50}], group="Wohnzimmer")
        assert res == {"played": 2}
        plays = [x for x in ot.log if x[0] == "play"]
        assert [p[1] for p in plays] == ["http://h/tts.wav", "http://h/news.mp3"]
        assert plays[0][2] == {"1": 35, "2": 35} and plays[1][2] == {"1": 50, "2": 50}
        assert {o["id"]: o["volume"] for o in ot.outs} == {"1": 60, "2": 55, "3": 40}  # restored
        assert calls == [("group", "Wohnzimmer"), "pause"] and not an.active
    asyncio.run(run())


def test_unreachable_url_errors_and_restores():
    async def run():
        ot = FakeOwnTone(play_for=0)  # never starts
        an, _ = make(ot)
        with pytest.raises(AnnounceError):
            await an.play([{"url": "http://h/missing.mp3", "volume": 20}])
        assert {o["id"]: o["volume"] for o in ot.outs}["1"] == 60 and not an.active
    asyncio.run(run())


def test_stop_cancels_and_restores():
    async def run():
        ot = FakeOwnTone(play_for=5)
        an, _ = make(ot)
        await an.play([{"url": "http://h/news.mp3", "volume": 50}], wait=False)
        await asyncio.sleep(0.2)
        assert an.active and an.state()["current"]["url"] == "http://h/news.mp3"
        await an.stop()
        assert ("stop",) in ot.log and ("clear",) in ot.log
        assert not an.active and {o["id"]: o["volume"] for o in ot.outs}["1"] == 60
    asyncio.run(run())


class CrashingOwnTone(FakeOwnTone):
    """OwnTone stürzt beim ersten Abspielen ab und ist kurz nicht erreichbar."""

    def __init__(self):
        super().__init__(play_for=0.2)
        self.down_until = 0.0
        self.crashed = False

    def _check(self):
        if asyncio.get_running_loop().time() < self.down_until:
            raise announce.SpotifyError("OwnTone nicht erreichbar (ClientConnectorError).")

    async def outputs(self):
        self._check()
        return await super().outputs()

    async def play_url(self, url):
        self._check()
        if not self.crashed:
            self.crashed = True
            self.down_until = asyncio.get_running_loop().time() + 0.3
            raise announce.SpotifyError("OwnTone nicht erreichbar (ServerDisconnectedError).")
        await super().play_url(url)

    async def set_output(self, oid, volume=None, **kw):
        self._check()
        await super().set_output(oid, volume=volume, **kw)


def test_owntone_crash_is_retried_once(monkeypatch):
    monkeypatch.setattr(announce, "OWNTONE_RESTART", 3.0)

    async def run():
        ot = CrashingOwnTone()
        an, calls = make(ot)
        res = await an.play([{"url": "http://h/news.wav", "volume": 40}], group="Wohnzimmer")
        assert res == {"played": 1}
        assert [x[1] for x in ot.log if x[0] == "play"] == ["http://h/news.wav"]
        assert calls.count(("group", "Wohnzimmer")) == 2  # Gruppe nach dem Neustart wieder eingeschaltet
        assert {o["id"]: o["volume"] for o in ot.outs} == {"1": 60, "2": 55, "3": 40}
    asyncio.run(run())


def test_media_prep_converts_streamed_wav_and_serves_clean_mp3(tmp_path):
    import io
    import shutil
    import wave

    from aiohttp import web
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg fehlt")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:  # 1 s Stille
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(b"\0\0" * 22050)
    data = bytearray(buf.getvalue())
    data[40:44] = b"\xff\xff\xff\xff"  # wie ein TTS-Stream: Länge unbekannt

    async def run():
        async def tts(_req):  # chunked, ohne Content-Length – wie /api/tts_proxy
            resp = web.StreamResponse(headers={"Content-Type": "audio/x-wav"})
            await resp.prepare(_req)
            await resp.write(bytes(data))
            await resp.write_eof()
            return resp

        async def mp3(_req):
            return web.Response(body=b"ID3fake-mp3", content_type="audio/mpeg")

        app = web.Application()
        app.router.add_get("/tts.wav", tts)
        app.router.add_get("/news.mp3", mp3)
        app.router.add_get("/gone", lambda r: web.Response(status=404))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        async with aiohttp.ClientSession() as s:
            prep = announce.MediaPrep(s, "http://127.0.0.1:8099", tmp_path)
            local = await prep(f"http://127.0.0.1:{port}/tts.wav")
            name = local.rsplit("/", 1)[1]
            assert local.startswith("http://127.0.0.1:8099/announce-media/") and name.endswith(".mp3")
            path = prep.path(name)
            assert path and path.stat().st_size > 1000
            assert sorted(p.suffix for p in tmp_path.iterdir()) == [".mp3"]  # Rohdatei entfernt
            same = await prep(f"http://127.0.0.1:{port}/news.mp3")  # fertige MP3: unverändert
            assert prep.path(same.rsplit("/", 1)[1]).read_bytes() == b"ID3fake-mp3"
            with pytest.raises(AnnounceError):
                await prep(f"http://127.0.0.1:{port}/gone")
            prep.cleanup(local)
            assert prep.path(name) is None and prep.path("../etc/passwd") is None
        await runner.cleanup()
    import aiohttp
    asyncio.run(run())
