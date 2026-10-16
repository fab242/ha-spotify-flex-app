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
