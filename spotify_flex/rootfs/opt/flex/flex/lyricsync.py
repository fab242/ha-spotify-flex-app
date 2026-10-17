"""Liedtexte für die Kachel – und genaue Wortzeiten über den Analyse-Container (flex-lyrics-aligner).

* Liedtext: lrclib.net (wie bisher in der Kachel), hier zentral geholt und pro Titel zwischengespeichert.
* Genauigkeit: flex-eq zweigt das gespielte PCM nicht-blockierend nach /run/flex/tap.raw ab. Dieses Modul
  ordnet jede Probe der Titelposition zu und schickt sie stückweise an den Container im Heimnetz, der den
  Text Wort für Wort an den Gesang anlegt. Gespeichert werden dort nur Zeitstempel.

Zuordnung Probe -> Titelposition: Der Abzweig liefert einen lückenlosen Probenzähler. Für jede Nachricht
gilt Position ≈ (Spotify-Position laut Empfänger, hochgerechnet auf jetzt) − Probenzeit; der Median über
viele Nachrichten glättet Zufallsschwankungen. Springt die Differenz (Spulen), beginnt ein neuer Abschnitt.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import statistics
import struct
import time
from collections import OrderedDict, deque
from typing import Any, Awaitable, Callable

import aiohttp

_LOGGER = logging.getLogger("flex.lyrics")

TAP_PATH = "/run/flex/tap.raw"
RATE = 44100
FRAME_BYTES = 4
HEADER = struct.Struct("<4sIQI")   # "FXT2", Frames, Frame-Zähler, Bytes in der Pipe zu OwnTone
LA_FRAMES = 256                       # Verzögerung des Limiters in flex-eq
CHUNK_SECONDS = 10.0
LRCLIB = "https://lrclib.net/api"
TS = re.compile(r"\[(\d+):(\d+(?:[.,]\d+)?)\]")
WTS = re.compile(r"<(\d+):(\d+(?:[.,]\d+)?)>")
SPOTIFY_TRACK = re.compile(r"^spotify:track:([A-Za-z0-9]{8,40})$")
SEEK_JUMP_MS = 1500


def parse_lrc(raw: str | None) -> list[dict]:
    """LRC -> [{t (ms), text}] (sortiert, leere Zeilen weg, Wort-Marken entfernt)."""
    out = []
    for line in str(raw or "").splitlines():
        stamps = TS.findall(line)
        if not stamps:
            continue
        text = re.sub(r"\s+", " ", WTS.sub("", TS.sub("", line))).strip()
        if not text:
            continue
        for m, s in stamps:
            out.append({"t": int(round((int(m) * 60 + float(s.replace(",", "."))) * 1000)), "text": text})
    out.sort(key=lambda l: l["t"])
    return out


class Lyrics:
    """lrclib-Abruf mit Zwischenspeicher (im Speicher, pro Titel-URI)."""

    def __init__(self, session: aiohttp.ClientSession, version: str) -> None:
        self._s = session
        self._ua = f"spotify-flex {version} (https://github.com/fab242/ha-spotify-flex-app)"
        self.cache: OrderedDict[str, dict] = OrderedDict()
        self._pending: dict[str, asyncio.Task] = {}

    async def _get(self, path: str, params: dict) -> Any:
        try:
            async with self._s.get(f"{LRCLIB}/{path}", params=params, headers={"Lrclib-Client": self._ua},
                                   timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.json() if r.status == 200 else None
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return None

    async def fetch(self, uri: str, title: str, artist: str, album: str | None, duration_ms: int | None) -> dict:
        if uri in self.cache:
            self.cache.move_to_end(uri)
            return self.cache[uri]
        if uri not in self._pending:
            self._pending[uri] = asyncio.ensure_future(self._fetch(title, artist, album, duration_ms))
        try:
            res = await self._pending[uri]
        finally:
            self._pending.pop(uri, None)
        if res["lines"] or res["text"]:
            self.cache[uri] = res
            while len(self.cache) > 300:
                self.cache.popitem(last=False)
        return res

    async def _fetch(self, title: str, artist: str, album: str | None, duration_ms: int | None) -> dict:
        artist = (artist or "").split(",")[0].strip()
        params = {"track_name": title, "artist_name": artist}
        if album:
            params["album_name"] = album
        if duration_ms:
            params["duration"] = str(round(duration_ms / 1000))
        hit = await self._get("get", params)
        if not hit or not (hit.get("syncedLyrics") or hit.get("plainLyrics")):
            found = await self._get("search", {"track_name": title, "artist_name": artist})
            if isinstance(found, list) and found:
                dur = (duration_ms or 0) / 1000
                synced = [x for x in found if x.get("syncedLyrics")]
                hit = sorted(synced, key=lambda x: abs((x.get("duration") or 0) - dur))[0] if synced else found[0]
        lines = parse_lrc((hit or {}).get("syncedLyrics"))
        return {"lines": lines, "text": "" if lines else str((hit or {}).get("plainLyrics") or "").strip(),
                "source": "lrclib" if hit else None}


class AlignerClient:
    """HTTP-Zugang zum Analyse-Container. Fällt er aus, wird es eine Minute lang nicht erneut versucht."""

    def __init__(self, session: aiohttp.ClientSession, url: str, token: str = "") -> None:
        self._s = session
        self.url = url.rstrip("/")
        self._h = {"Authorization": f"Bearer {token}"} if token else {}
        self.down_until = 0.0
        self.last_error: str | None = None

    @property
    def available(self) -> bool:
        return bool(self.url) and time.monotonic() >= self.down_until

    async def call(self, method: str, path: str, *, json_body: Any = None, data: bytes | None = None,
                   params: dict | None = None, timeout: float = 20) -> Any:
        try:
            async with self._s.request(method, self.url + path, json=json_body, data=data, params=params,
                                       headers=self._h, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                body = await r.json(content_type=None)
                if r.status == 404:
                    return None
                if r.status >= 400:
                    raise RuntimeError((body or {}).get("error") or f"HTTP {r.status}")
                self.last_error = None
                return body
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, RuntimeError) as err:
            self.last_error = f"{type(err).__name__}: {err}"
            self.down_until = time.monotonic() + 60
            _LOGGER.warning("Liedtext-Analyse nicht erreichbar (%s)", self.last_error)
            return None


class TrackFeed:
    """Ein Titel, der gerade an den Container gestreamt wird."""

    def __init__(self, track_id: str) -> None:
        self.track_id = track_id
        self.diffs: deque[float] = deque(maxlen=400)   # Positions-Differenzen (ms) dieses Abschnitts
        self.buf = bytearray()
        self.buf_pos: float | None = None              # Probenindex des ersten Puffer-Samples
        self.next_frame: int | None = None
        self.state = "pending"                         # pending (Liedtext/Start läuft) | active | off
        self.held: list[tuple[int, bytes]] = []        # Stücke, die vor dem Start ankamen
        self.sent_ms = 0.0

    @property
    def active(self) -> bool:
        return self.state == "active"


class LyricSync:
    """Verbindet Abzweig, Empfänger-Status und Analyse-Container."""

    def __init__(self, session: aiohttp.ClientSession, lyrics: Lyrics, aligner: AlignerClient | None,
                 status: Callable[[], tuple[dict | None, float]], tap_path: str = TAP_PATH) -> None:
        self.lyrics = lyrics
        self.aligner = aligner
        self.status = status
        self.tap_path = tap_path
        self.feed: TrackFeed | None = None
        self.skip: set[str] = set()                    # Titel ohne Liedtext / schon fertig
        self._task: asyncio.Task | None = None
        self._sender: asyncio.Task | None = None
        self.outbox: asyncio.Queue = asyncio.Queue(maxsize=12)

    # ------------------------------------------------------------- Lebenszyklus
    def start(self) -> None:
        if self.aligner and self.aligner.url and not self._task:
            self._task = asyncio.ensure_future(self._read_tap())
            self._sender = asyncio.ensure_future(self._send_loop())

    async def stop(self) -> None:
        for task in (self._task, self._sender):
            if task:
                task.cancel()
        self._task = self._sender = None

    async def _send_loop(self) -> None:
        """Verschickt Audio, Start und Ende der Reihe nach – der Abzweig wird dabei weiter gelesen."""
        while True:
            kind, track_id, payload = await self.outbox.get()
            try:
                if kind == "audio":
                    pos_ms, data = payload
                    await self.aligner.call("POST", f"/tracks/{track_id}/audio", data=data,
                                            params={"pos_ms": str(pos_ms)}, timeout=30)
                elif kind == "finish":
                    await self.aligner.call("POST", f"/tracks/{track_id}/finish")
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Senden: %s", err)

    def _post(self, item: tuple) -> None:
        try:
            self.outbox.put_nowait(item)
        except asyncio.QueueFull:
            _LOGGER.debug("Analyse kommt nicht hinterher – Stück verworfen")

    # ------------------------------------------------------------- Abzweig lesen
    async def _read_tap(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            try:
                if not os.path.exists(self.tap_path):
                    os.mkfifo(self.tap_path)
                # lesend UND schreibend öffnen: die FIFO meldet dann nie „Ende“, auch wenn flex-eq
                # gerade (noch) nicht schreibt – flex-eq kann sich jederzeit dazuschalten
                fd = os.open(self.tap_path, os.O_RDWR | os.O_NONBLOCK)
                reader = asyncio.StreamReader(limit=1 << 22)
                transport, _ = await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader),
                                                            os.fdopen(fd, "rb", buffering=0))
                try:
                    while True:
                        head = await reader.readexactly(HEADER.size)
                        magic, frames, index, queued = HEADER.unpack(head)
                        if magic != b"FXT2" or frames > 4096:
                            raise ValueError("Abzweig: Datenstrom aus dem Tritt")
                        pcm = await reader.readexactly(frames * FRAME_BYTES)
                        self.on_audio(index, pcm, queued)
                finally:
                    transport.close()
            except asyncio.CancelledError:
                raise
            except (asyncio.IncompleteReadError, ValueError, OSError) as err:
                _LOGGER.debug("Abzweig neu öffnen: %s", err)
                await asyncio.sleep(1)

    # ------------------------------------------------------------- Zuordnung
    def _now_position(self) -> tuple[str | None, float | None]:
        st, at = self.status()
        if not st or st.get("paused") or st.get("stopped"):
            return None, None
        track = st.get("track") or {}
        uri, pos = track.get("uri"), track.get("position")
        if not uri or pos is None or not at:
            return uri, None
        return uri, pos + (time.time() - at) * 1000

    def on_audio(self, index: int, pcm: bytes, queued_bytes: int = 0) -> None:
        """Ein Block vom Abzweig. Position = Spotify-Position in dem Moment, in dem OwnTone diesen Block
        liest – dieselbe Uhr, nach der die Kachel läuft (OwnTone-Fortschritt per Metadaten). OwnTone liest
        ihn erst, nachdem die Pipe (queued_bytes) und die Limiter-Verzögerung abgespielt sind."""
        uri, pos_now = self._now_position()
        m = SPOTIFY_TRACK.match(uri or "")
        if not m or pos_now is None:
            return
        track_id = m.group(1)
        if self.feed is None or self.feed.track_id != track_id:
            self._switch(track_id, uri)
        feed = self.feed
        if feed is None or feed.state == "off":
            return
        frames = len(pcm) // FRAME_BYTES
        end_ms = (index + frames) * 1000 / RATE
        ahead_ms = (queued_bytes / FRAME_BYTES + LA_FRAMES + frames) * 1000 / RATE
        diff = pos_now + ahead_ms - end_ms
        if feed.diffs and abs(diff - statistics.median(feed.diffs)) > SEEK_JUMP_MS:
            self._flush(feed)                           # gespult: neuer Abschnitt
            feed.diffs.clear()
        if feed.next_frame is not None and index != feed.next_frame:
            self._flush(feed)                           # Lücke im Abzweig
        feed.diffs.append(diff)
        feed.next_frame = index + frames
        if not feed.buf:
            feed.buf_pos = index
        feed.buf.extend(pcm)
        if len(feed.buf) >= CHUNK_SECONDS * RATE * FRAME_BYTES:
            self._flush(feed)

    def _flush(self, feed: TrackFeed) -> None:
        if not feed.buf or feed.buf_pos is None or len(feed.diffs) < 20:
            feed.buf.clear()
            feed.buf_pos = None
            return
        offset = statistics.median(feed.diffs)
        pos_ms = int(round(feed.buf_pos * 1000 / RATE + offset))
        data, feed.buf = bytes(feed.buf), bytearray()
        feed.buf_pos = None
        if pos_ms < -500:
            return
        pos_ms = max(0, pos_ms)
        feed.sent_ms += len(data) / FRAME_BYTES * 1000 / RATE
        if feed.state == "active":
            self._post(("audio", feed.track_id, (pos_ms, data)))
        elif feed.state == "pending" and len(feed.held) < 9:   # bis ~90 s vorhalten
            feed.held.append((pos_ms, data))

    def _switch(self, track_id: str, uri: str) -> None:
        old, self.feed = self.feed, TrackFeed(track_id)
        if old:
            self._flush(old)
            if old.active:
                self._post(("finish", old.track_id, None))
        if track_id in self.skip or not (self.aligner and self.aligner.available):
            self.feed.state = "off"
            return
        asyncio.ensure_future(self._begin(self.feed, uri))

    async def _begin(self, feed: TrackFeed, uri: str) -> None:
        """Liedtext holen und die Analyse starten; bis dahin angekommenes Audio nachreichen."""
        st, _ = self.status()
        track = (st or {}).get("track") or {}
        try:
            if track.get("uri") != uri:
                feed.state = "off"
                return
            res = await self.lyrics.fetch(uri, track.get("name") or "", ", ".join(track.get("artist_names") or []),
                                          track.get("album_name"), track.get("duration"))
            if not res["lines"]:
                self.skip.add(feed.track_id)
                feed.state = "off"
                return
            started = await self.aligner.call("POST", f"/tracks/{feed.track_id}/start", json_body={
                "duration_ms": int(track.get("duration") or 0), "lines": res["lines"]})
            if not started or started.get("state") == "done":
                if started:
                    self.skip.add(feed.track_id)          # schon exakt – nichts zu tun
                feed.state = "off"
                return
            feed.state = "active"
            for pos_ms, data in feed.held:
                self._post(("audio", feed.track_id, (pos_ms, data)))
            feed.held.clear()
            if self.feed is not feed:                     # Titel schon wieder gewechselt
                self._post(("finish", feed.track_id, None))
            _LOGGER.info("Liedtext-Analyse: %s (%s)", track.get("name"), feed.track_id)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Liedtext-Analyse konnte nicht starten")
            feed.state = "off"

    # ------------------------------------------------------------- für die Kachel
    async def for_track(self, uri: str, title: str, artist: str, album: str | None, duration_ms: int | None) -> dict:
        res = await self.lyrics.fetch(uri, title, artist, album, duration_ms)
        out = {"uri": uri, "source": res.get("source"), "lines": [dict(l) for l in res["lines"]], "text": res["text"],
               "exact": False, "aligned": 0, "total": 0, "analysis": "off"}
        m = SPOTIFY_TRACK.match(uri or "")
        if not (m and res["lines"] and self.aligner and self.aligner.url):
            return out
        out["analysis"] = "unreachable" if not self.aligner.available else "pending"
        if not self.aligner.available:
            return out
        al = await self.aligner.call("GET", f"/tracks/{m.group(1)}", timeout=8)
        if not al:
            return out
        texts = [l["text"] for l in out["lines"]]
        if [l["text"] for l in al.get("lines", [])] != texts:
            return out                                  # anderer Liedtext als analysiert – nicht mischen
        for line, a in zip(out["lines"], al["lines"]):
            if a.get("words"):
                line["words"] = a["words"]
        out.update(aligned=al.get("aligned", 0), total=al.get("total", 0), exact=bool(al.get("complete")),
                   analysis="done" if al.get("complete") else "running")
        return out

    async def coverage(self, uris: list[str]) -> dict:
        ids = {SPOTIFY_TRACK.match(u).group(1): u for u in uris if SPOTIFY_TRACK.match(u or "")}
        if not ids or not (self.aligner and self.aligner.available):
            return {"available": False, "exact": 0, "total": len(ids)}
        res = await self.aligner.call("POST", "/lookup", json_body={"ids": list(ids)}, timeout=10)
        if res is None:   # Container nicht erreichbar: keine Anzeige statt „0 von N“
            return {"available": False, "exact": 0, "total": len(ids)}
        tracks = res.get("tracks") or {}
        exact = sum(1 for t in tracks.values() if t.get("complete"))
        return {"available": True, "exact": exact, "total": len(ids),
                "tracks": {ids[k]: v for k, v in tracks.items()}}

    def health(self) -> dict:
        return {"configured": bool(self.aligner and self.aligner.url),
                "reachable": bool(self.aligner and self.aligner.available),
                "error": self.aligner.last_error if self.aligner else None,
                "current": self.feed.track_id if self.feed and self.feed.active else None}
