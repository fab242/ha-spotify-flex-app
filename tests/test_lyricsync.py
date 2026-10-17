import asyncio
import os
import struct
import time

import pytest

from flex import lyricsync as L

RATE = L.RATE


class Clock:
    """Empfänger-Status wie go-librespot: Position läuft mit der Wanduhr."""

    def __init__(self, uri="spotify:track:AAAAAAAAAAAAAAAAAAAAAA", pos=0.0):
        self.uri, self.pos0, self.t0 = uri, pos, time.time()
        self.paused = False

    def seek(self, pos):
        self.pos0, self.t0 = pos, time.time()

    def __call__(self):
        pos = self.pos0 + (time.time() - self.t0) * 1000
        st = {"paused": self.paused, "stopped": False,
              "track": {"uri": self.uri, "position": int(pos), "name": "Lied", "artist_names": ["Band"],
                        "album_name": "Album", "duration": 200000}}
        return st, time.time()


class FakeAligner:
    url = "http://nuc:8770"
    available = True
    last_error = None

    def __init__(self, done=False, result=None):
        self.calls, self.done, self.result = [], done, result

    async def call(self, method, path, *, json_body=None, data=None, params=None, timeout=20):
        self.calls.append((method, path, json_body, len(data) if data else None, params))
        if path.endswith("/start"):
            return {"state": "done"} if self.done else {"state": "started"}
        if method == "GET":
            return self.result
        if path == "/lookup":
            return {"tracks": {"AAAAAAAAAAAAAAAAAAAAAA": {"complete": True, "aligned": 5, "total": 5}}}
        return {"ok": True}


class FakeLyrics:
    def __init__(self, lines):
        self.lines = lines

    async def fetch(self, uri, title, artist, album, duration_ms):
        await asyncio.sleep(0.05)
        return {"lines": self.lines, "text": "", "source": "lrclib"}


LINES = [{"t": 1000, "text": "Ich geh nach Haus"}, {"t": 4000, "text": "und du bleibst hier"}]


def test_parse_lrc():
    raw = "[00:01.50]Ich geh <00:02.00>nach Haus\n[00:04.00][01:04.00]Refrain\n[00:05.00]\nkein Zeitstempel"
    assert L.parse_lrc(raw) == [{"t": 1500, "text": "Ich geh nach Haus"}, {"t": 4000, "text": "Refrain"},
                                {"t": 64000, "text": "Refrain"}]


async def _wait(clock, seconds):
    """Echte Wartezeit, ohne dass die simulierte Wiedergabe weiterläuft (dort fließt Audio ja durchgehend)."""
    t = time.time()
    await asyncio.sleep(seconds)
    clock.t0 += time.time() - t


def _pump(sync, clock, seconds, start_index, frames=1020, queued=0):
    """Abzweig-Nachrichten im Takt der Echtzeit (beschleunigt: Uhr wird mitgeschoben)."""
    idx = start_index
    n = int(seconds * RATE / frames)
    for _ in range(n):
        clock.t0 -= frames / RATE      # Wanduhr „läuft“ um die Nachrichtendauer weiter
        sync.on_audio(idx, b"\0" * frames * 4, queued)
        idx += frames
    return idx


def test_positions_mapped_exactly_and_seek_starts_new_section():
    async def run():
        clock = Clock(pos=0.0)
        al = FakeAligner()
        sync = L.LyricSync(None, FakeLyrics(LINES), al, clock)
        sent = []
        sync._post = lambda item: sent.append(item)
        idx = _pump(sync, clock, 0.5, start_index=5_000_000)     # Titel startet, Start läuft noch
        await _wait(clock, 0.15)                                  # Liedtext + Start fertig
        assert sync.feed.state == "active"
        idx = _pump(sync, clock, 25.0, start_index=idx)
        audio = [i for i in sent if i[0] == "audio"]
        assert len(audio) >= 2
        # erstes Stück beginnt bei Titelposition ~0 (nicht beim Probenzähler 5 Mio.)
        # ... plus Limiter-Verzögerung und Blocklänge, bis OwnTone den Block liest
        assert abs(audio[0][2][0] - (L.LA_FRAMES + 1020) * 1000 / RATE) <= 15, audio[0][2][0]
        ahead = (L.LA_FRAMES + 1020) * 1000 / RATE
        assert abs(audio[1][2][0] - 10000 - ahead) <= 30, audio[1][2][0]
        clock.seek(120000)                                        # gespult auf 2:00
        sent.clear()
        _pump(sync, clock, 12.0, start_index=idx)
        pos = [i[2][0] for i in sent if i[0] == "audio"]
        assert abs(pos[0] - 20000 - ahead) <= 60          # Rest vor dem Spulen behält seine Position
        assert abs(pos[1] - 120000 - ahead) <= 60, pos    # danach geht es exakt bei 2:00 weiter
    asyncio.run(run())


def test_audio_before_start_is_held_and_delivered():
    async def run():
        clock = Clock()
        sync = L.LyricSync(None, FakeLyrics(LINES), FakeAligner(), clock)
        sent = []
        sync._post = lambda item: sent.append(item)
        _pump(sync, clock, 10.5, start_index=0)                  # 10 s kommen, bevor Liedtext da ist
        assert not [s for s in sent if s[0] == "audio"] and sync.feed.held
        await asyncio.sleep(0.15)
        assert [s for s in sent if s[0] == "audio"] and not sync.feed.held
    asyncio.run(run())


def test_no_lyrics_or_already_done_means_nothing_is_sent():
    async def run():
        for lyr, al in ((FakeLyrics([]), FakeAligner()), (FakeLyrics(LINES), FakeAligner(done=True))):
            clock = Clock()
            sync = L.LyricSync(None, lyr, al, clock)
            sent = []
            sync._post = lambda item: sent.append(item)
            _pump(sync, clock, 0.3, 0)
            await asyncio.sleep(0.15)
            _pump(sync, clock, 12, 20000)
            assert not [s for s in sent if s[0] == "audio"]
            assert "AAAAAAAAAAAAAAAAAAAAAA" in sync.skip
    asyncio.run(run())


def test_track_change_finishes_previous():
    async def run():
        clock = Clock()
        sync = L.LyricSync(None, FakeLyrics(LINES), FakeAligner(), clock)
        sent = []
        sync._post = lambda item: sent.append(item)
        idx = _pump(sync, clock, 0.3, 0)
        await asyncio.sleep(0.15)
        idx = _pump(sync, clock, 5, idx)
        clock.uri = "spotify:track:BBBBBBBBBBBBBBBBBBBBBB"
        clock.seek(0)
        _pump(sync, clock, 0.3, idx)
        assert ("finish", "AAAAAAAAAAAAAAAAAAAAAA", None) in sent
        assert sync.feed.track_id == "BBBBBBBBBBBBBBBBBBBBBB"
    asyncio.run(run())


def test_for_track_merges_exact_words_only_for_same_text():
    async def run():
        res = {"lines": [{"text": "Ich geh nach Haus", "words": [{"w": "Ich", "s": 1210, "e": 1400}]},
                         {"text": "und du bleibst hier", "words": None}],
               "aligned": 1, "total": 2, "complete": False}
        sync = L.LyricSync(None, FakeLyrics(LINES), FakeAligner(result=res), Clock())
        out = await sync.for_track("spotify:track:AAAAAAAAAAAAAAAAAAAAAA", "Lied", "Band", None, 200000)
        assert out["lines"][0]["words"][0]["s"] == 1210 and "words" not in out["lines"][1]
        assert out["analysis"] == "running" and out["aligned"] == 1
        res["lines"][0]["text"] = "anderer Text"
        out = await sync.for_track("spotify:track:AAAAAAAAAAAAAAAAAAAAAA", "Lied", "Band", None, 200000)
        assert "words" not in out["lines"][0]
        cov = await sync.coverage(["spotify:track:AAAAAAAAAAAAAAAAAAAAAA", "spotify:episode:X"])
        assert cov["exact"] == 1 and cov["total"] == 1
    asyncio.run(run())


def test_reads_real_fifo_messages(tmp_path):
    async def run():
        path = str(tmp_path / "tap.raw")
        got = []
        sync = L.LyricSync(None, FakeLyrics(LINES), FakeAligner(), Clock(), tap_path=path)
        sync.on_audio = lambda idx, pcm, queued=0: got.append((idx, len(pcm)))
        task = asyncio.ensure_future(sync._read_tap())
        await asyncio.sleep(0.2)
        fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)          # wie flex-eq
        for i in range(3):
            os.write(fd, struct.pack("<4sIQI", b"FXT2", 1019, i * 1019, 0) + b"\1" * 4076)
        os.close(fd)
        await asyncio.sleep(0.3)
        task.cancel()
        assert got == [(0, 4076), (1019, 4076), (2038, 4076)]
    asyncio.run(run())


def test_pipe_to_owntone_is_accounted_for():
    """Ein Block, der beim Abgreifen noch hinter 64 KB in der Pipe zu OwnTone steht, wird erst ~0,37 s
    später gehört – genau so viel später muss seine Titelposition liegen (Uhr der Kachel = OwnTone)."""
    async def run():
        res = {}
        for queued in (0, 65536):
            clock = Clock(pos=0.0)
            sync = L.LyricSync(None, FakeLyrics(LINES), FakeAligner(), clock)
            sent = []
            sync._post = lambda item, sent=sent: sent.append(item)
            idx = _pump(sync, clock, 0.5, start_index=0, queued=queued)
            await _wait(clock, 0.15)
            _pump(sync, clock, 12.0, start_index=idx, queued=queued)
            res[queued] = [i for i in sent if i[0] == "audio"][0][2][0]
        assert abs((res[65536] - res[0]) - 65536 / 4 / L.RATE * 1000) <= 2, res
    asyncio.run(run())


def test_coverage_unavailable_when_container_down():
    class Down(FakeAligner):
        async def call(self, *a, **k):
            return None
    async def run():
        sync = L.LyricSync(None, FakeLyrics(LINES), Down(), Clock())
        r = await sync.coverage(["spotify:track:4uLU6hMCjMI75M1A2tKUQC"])
        assert r["available"] is False
    asyncio.run(run())
