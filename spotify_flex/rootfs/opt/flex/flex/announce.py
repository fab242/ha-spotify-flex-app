"""Durchsagen: Audio-Links (TTS, Nachrichten, Radio …) über die AirPlay-Lautsprecher von OwnTone.

Spotify läuft über die Pipe; eine Durchsage ersetzt kurz die OwnTone-Warteschlange durch die
gewünschten Links und spielt sie nacheinander – synchron auf allen gewählten Lautsprechern.
Laufendes Spotify wird vorher pausiert, die Lautsprecher-Lautstärken werden danach
wiederhergestellt. Sobald Spotify wieder spielt, übernimmt OwnTone die Pipe von selbst.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

from .api import SpotifyError

_LOGGER = logging.getLogger("flex.announce")

START_TIMEOUT = 20.0      # s bis OwnTone einen Link tatsächlich abspielt
POLL = 0.5


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


class Announcer:
    def __init__(self, owntone, pause_spotify: Callable[[], Awaitable[None]],
                 select_group: Callable[[str], Awaitable[None]]) -> None:
        self.owntone = owntone
        self.pause_spotify = pause_spotify
        self.select_group = select_group
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
                if it["volume"] is not None:
                    for o in outputs:
                        await self.owntone.set_output(o["id"], volume=it["volume"])
                await self.owntone.play_url(it["url"])
                await self._wait_done(deadline)
                played += 1
            return {"played": played}
        finally:
            self.active, self.current = False, None
            await self._restore_volumes()

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
