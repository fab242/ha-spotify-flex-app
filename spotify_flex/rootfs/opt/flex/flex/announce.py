"""Durchsagen: Audio-Links (TTS, Nachrichten, Radio …) über die AirPlay-Lautsprecher von OwnTone.

Spotify läuft über die Pipe; eine Durchsage ersetzt kurz die OwnTone-Warteschlange durch die
gewünschten Links und spielt sie nacheinander – synchron auf allen gewählten Lautsprechern.
Laufendes Spotify wird vorher pausiert, die Lautsprecher-Lautstärken werden danach
wiederhergestellt. Sobald Spotify wieder spielt, übernimmt OwnTone die Pipe von selbst.

Jeder Link wird vorher heruntergeladen und – wo nötig – mit ffmpeg in eine saubere MP3 umgewandelt
und lokal bereitgestellt. TTS-Streams aus Home Assistant kommen sonst als WAV ohne gültige Länge an,
an denen OwnTone abstürzen kann. Stürzt OwnTone trotzdem ab, wartet die Durchsage auf den Neustart
und versucht es einmal erneut.
"""
from __future__ import annotations

import asyncio
import logging
import re
import secrets
import shutil
import time
from pathlib import Path
from typing import Any, Awaitable, Callable

import aiohttp

from .api import SpotifyError

_LOGGER = logging.getLogger("flex.announce")

START_TIMEOUT = 20.0      # s bis OwnTone einen Link tatsächlich abspielt
POLL = 0.5
OWNTONE_RESTART = 25.0    # s, die auf einen Neustart von OwnTone gewartet wird
MEDIA_DIR = Path("/tmp/flex-announce")
MEDIA_MAX_BYTES = 600 * 1024 * 1024
MEDIA_NAME = re.compile(r"^[0-9a-f]{32}\.(mp3|m4a|aac|ogg|opus|flac)$")


class AnnounceError(SpotifyError):
    pass


def _items(raw: Any) -> list[dict]:
    """[{'url': str, 'volume': int|None}] aus str | dict | Liste davon."""
    raw = raw if isinstance(raw, list) else [raw]
    out = []
    for it in raw:
        if isinstance(it, str):
            it = {"url": it}
        if not isinstance(it, dict):
            raise AnnounceError("Ungültiger Eintrag für die Durchsage.", 400)
        url = str(it.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            raise AnnounceError("Durchsagen brauchen eine http(s)-Adresse.", 400)
        vol = it.get("volume")
        if vol is not None:
            try:
                vol = max(0, min(100, int(round(float(vol)))))
            except (TypeError, ValueError) as err:
                raise AnnounceError("Lautstärke muss eine Zahl von 0 bis 100 sein.", 400) from err
        out.append({"url": url, "volume": vol})
    if not out:
        raise AnnounceError("Keine Durchsage angegeben.", 400)
    return out


def _unreachable(err: Exception) -> bool:
    return isinstance(err, SpotifyError) and "nicht erreichbar" in str(err)


class MediaPrep:
    """Lädt einen Durchsage-Link herunter und stellt ihn als saubere Datei lokal bereit."""

    CLEAN = {"audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/mp4": "m4a", "audio/aac": "aac",
             "audio/ogg": "ogg", "audio/opus": "opus", "audio/flac": "flac"}

    def __init__(self, session: aiohttp.ClientSession, base_url: str, directory: Path = MEDIA_DIR,
                 ffmpeg: str | None = None) -> None:
        self._s = session
        self.base = base_url.rstrip("/")
        self.dir = Path(directory)
        self.ffmpeg = ffmpeg if ffmpeg is not None else shutil.which("ffmpeg")
        self.dir.mkdir(parents=True, exist_ok=True)
        for old in self.dir.iterdir():  # Reste nach einem Absturz
            old.unlink(missing_ok=True)

    def path(self, name: str) -> Path | None:
        return self.dir / name if MEDIA_NAME.match(name or "") and (self.dir / name).is_file() else None

    def cleanup(self, local_url: str) -> None:
        name = local_url.rsplit("/", 1)[-1]
        if MEDIA_NAME.match(name):
            (self.dir / name).unlink(missing_ok=True)

    async def __call__(self, url: str) -> str:
        name = secrets.token_hex(16)
        raw = self.dir / f"{name}.src"
        try:
            async with self._s.get(url, timeout=aiohttp.ClientTimeout(total=300, sock_read=60)) as resp:
                if resp.status >= 400:
                    raise AnnounceError(f"Durchsage nicht abrufbar: HTTP {resp.status}.", 502)
                ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                known_length = resp.content_length is not None
                size = 0
                with raw.open("wb") as fh:
                    async for chunk in resp.content.iter_chunked(256 * 1024):
                        size += len(chunk)
                        if size > MEDIA_MAX_BYTES:
                            raise AnnounceError("Durchsage ist zu groß.", 413)
                        fh.write(chunk)
            if not size:
                raise AnnounceError("Durchsage ist leer.", 502)
            ext = self.CLEAN.get(ctype)
            if ext and known_length:          # fertige Datei mit bekannter Länge: unverändert bereitstellen
                raw.rename(self.dir / f"{name}.{ext}")
                return f"{self.base}/announce-media/{name}.{ext}"
            if not self.ffmpeg:
                raise AnnounceError("ffmpeg fehlt – Durchsage kann nicht umgewandelt werden.", 500)
            out = self.dir / f"{name}.mp3"
            proc = await asyncio.create_subprocess_exec(
                self.ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
                "-vn", "-ac", "2", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "192k", str(out),
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
            try:
                _, err = await asyncio.wait_for(proc.communicate(), 600)
            except asyncio.TimeoutError:
                proc.kill()
                raise AnnounceError("Umwandeln der Durchsage dauert zu lange.", 504) from None
            if proc.returncode or not out.is_file() or not out.stat().st_size:
                out.unlink(missing_ok=True)
                raise AnnounceError(f"Durchsage ist keine lesbare Audiodatei ({(err or b'').decode(errors='replace')[:160].strip()}).", 422)
            return f"{self.base}/announce-media/{name}.mp3"
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise AnnounceError(f"Durchsage nicht abrufbar ({type(err).__name__}).", 502) from err
        finally:
            raw.unlink(missing_ok=True)


class Announcer:
    def __init__(self, owntone, pause_spotify: Callable[[], Awaitable[None]],
                 select_group: Callable[[str], Awaitable[None]], prepare: MediaPrep | None = None) -> None:
        self.owntone = owntone
        self.pause_spotify = pause_spotify
        self.select_group = select_group
        self.prepare = prepare
        self.group: str | None = None
        self.task: asyncio.Task | None = None
        self.active = False
        self.current: dict | None = None
        self._restore: dict[str, int] = {}

    def state(self) -> dict:
        return {"active": self.active, "current": self.current}

    async def play(self, raw_items: Any, group: str | None = None, wait: bool = True,
                   timeout: float = 900) -> dict:
        items = _items(raw_items)
        await self.stop(restore=True)
        self.group = group
        await self._ready()
        if group:
            await self.select_group(group)
        self.task = asyncio.create_task(self._run(items, timeout))
        if not wait:
            return {"started": True, "items": len(items)}
        try:
            return await asyncio.shield(self.task)
        except asyncio.CancelledError:
            return {"stopped": True}

    async def stop(self, restore: bool = True) -> None:
        was_active = self.active
        task, self.task = self.task, None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        if was_active:
            try:
                await self.owntone.stop()
                await self.owntone.clear_queue()
            except SpotifyError:
                pass
        if restore:
            await self._restore_volumes()
        self.active, self.current = False, None

    async def _restore_volumes(self) -> None:
        saved, self._restore = self._restore, {}
        for oid, vol in saved.items():
            try:
                await self.owntone.set_output(oid, volume=vol)
            except SpotifyError:
                pass

    async def _run(self, items: list[dict], timeout: float) -> dict:
        self.active = True
        deadline = time.monotonic() + timeout
        played = 0
        try:
            await self.pause_spotify()
            outputs = [o for o in await self.owntone.outputs() if o["selected"]]
            if not outputs:
                raise AnnounceError("Es ist kein Lautsprecher ausgewählt.", 409)
            self._restore = {o["id"]: o["volume"] for o in outputs if isinstance(o.get("volume"), int)}
            for idx, it in enumerate(items):
                self.current = {"index": idx, "url": it["url"]}
                url = await self.prepare(it["url"]) if self.prepare else it["url"]
                try:
                    await self._play_item(url, it["volume"], [o["id"] for o in outputs], deadline)
                finally:
                    if self.prepare and url != it["url"]:
                        self.prepare.cleanup(url)
                played += 1
            return {"played": played}
        finally:
            self.active, self.current = False, None
            await self._restore_volumes()

    async def _play_item(self, url: str, volume: int | None, output_ids: list[str], deadline: float) -> None:
        for attempt in (0, 1):
            try:
                if volume is not None:
                    for oid in output_ids:
                        await self.owntone.set_output(oid, volume=volume)
                await self.owntone.play_url(url)
                await self._wait_done(deadline)
                return
            except SpotifyError as err:
                if attempt or not _unreachable(err):
                    raise
                _LOGGER.warning("OwnTone während der Durchsage weg (%s) – warte auf Neustart", err)
                await self._ready()
                if self.group:
                    await self.select_group(self.group)

    async def _ready(self) -> None:
        """Warten, bis OwnTone antwortet (z. B. nach einem Neustart durch s6)."""
        end = time.monotonic() + OWNTONE_RESTART
        while True:
            try:
                await self.owntone.outputs()
                return
            except SpotifyError as err:
                if not _unreachable(err) or time.monotonic() > end:
                    raise
            await asyncio.sleep(max(POLL, 1.0))

    async def _wait_done(self, deadline: float) -> None:
        start = time.monotonic()
        started = False
        while time.monotonic() < deadline:
            await asyncio.sleep(POLL)
            pl = await self.owntone.player()
            playing = pl.get("state") == "play"
            if playing:
                started = True
            elif started:
                return                                   # Eintrag fertig
            elif time.monotonic() - start > START_TIMEOUT:
                raise AnnounceError("Die Durchsage konnte nicht abgespielt werden (Adresse nicht erreichbar?).", 502)
        raise AnnounceError("Zeitüberschreitung bei der Durchsage.", 504)
