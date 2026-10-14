"""Audible-position sync: metadata pipe framing and latency measurement."""
import asyncio
import base64
import re
import time

from flex import server
from flex.receiver import MetaPipe


def test_progress_item_is_shairport_xml():
    raw = MetaPipe.progress_item(61234, 300000).decode()
    assert "<type>73736e63</type>" in raw and "<code>70726772</code>" in raw  # ssnc / prgr
    data = base64.b64decode(re.search(r'base64">\n(.*)</data>', raw).group(1))
    start, pos, end = (int(x) for x in data.rstrip(b"\0").split(b"/"))
    assert abs((pos - start) * 1000 // 44100 - 61234) <= 1
    assert (end - start) * 1000 // 44100 == 300000


class FakeReceiver:
    def __init__(self, pos):
        self.pos = pos

    async def status(self):
        return {"stopped": False, "paused": False,
                "track": {"uri": "spotify:track:A", "position": self.pos, "duration": 300000}}


class FakeOwnTone:
    def __init__(self, prog):
        self.prog = prog

    async def player(self):
        return {"state": "play", "item_progress_ms": self.prog}


class FakeMeta:
    def __init__(self):
        self.sent = []

    def send(self, payload):
        self.sent.append(payload)
        return True


def test_latency_measured_and_applied(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "LATENCY_FILE", tmp_path / "lat.json")
    app = server.App.__new__(server.App)
    app.auth_pending = None
    app.status, app.status_at = None, 0.0
    app.sync_track, app.sync_since = None, 0.0
    app.latency = server.deque(maxlen=15)
    app.meta = FakeMeta()
    app.receiver = FakeReceiver(60000)
    app.owntone = FakeOwnTone(55000)

    asyncio.run(app.audio_sync())
    assert app.meta.sent, "position must be sent to OwnTone"
    assert not app.latency, "no measurement before our marks are audible"

    app.sync_since = time.time() - 20
    for _ in range(5):
        asyncio.run(app.audio_sync())
    assert 4990 <= app.latency_ms() <= 5100
    assert 54900 <= app.heard_position(60000) <= 55010
    assert app.heard_position(1000) < 0  # right after a track change: old track still audible
    assert (tmp_path / "lat.json").exists()

    # stale progress of the previous track (larger than the new position) is ignored
    app.owntone = FakeOwnTone(250000)
    before = list(app.latency)
    asyncio.run(app.audio_sync())
    assert list(app.latency) == before
