"""Local clients for go-librespot (Spotify Connect receiver) and OwnTone (AirPlay sender)."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

import aiohttp

from .api import SpotifyError, valid_uri
from .const import LIBRESPOT_URL, OWNTONE_URL

_LOGGER = logging.getLogger(__name__)
TIMEOUT = aiohttp.ClientTimeout(total=10)


async def _call(session: aiohttp.ClientSession, method: str, url: str, body: Any = None,
                params: dict | None = None, what: str = "Empfänger", timeout: float | None = None) -> Any:
    try:
        async with session.request(method, url, json=body, params=params,
                                   timeout=aiohttp.ClientTimeout(total=timeout) if timeout else TIMEOUT,
                                   allow_redirects=False) as resp:
            text = await resp.text()
            if resp.status == 204 or not text:
                return None
            if resp.status >= 400:
                raise SpotifyError(f"{what}: HTTP {resp.status} {text[:200]}", resp.status)
            try:
                return json.loads(text)
            except ValueError:
                return text
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        raise SpotifyError(f"{what} nicht erreichbar ({type(err).__name__}).") from err


class Librespot:
    """go-librespot REST API on 127.0.0.1:3678."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._s = session

    async def _post(self, path: str, body: Any = None) -> Any:
        return await _call(self._s, "POST", LIBRESPOT_URL + path, body)

    # NOTE: while go-librespot waits for the device-code login it does not answer
    # "/" or "/status" at all (the request blocks); only "/auth/code" responds.
    async def root(self) -> dict:
        return await _call(self._s, "GET", LIBRESPOT_URL + "/", timeout=3) or {}

    async def status(self) -> dict | None:
        return await _call(self._s, "GET", LIBRESPOT_URL + "/status", timeout=4)

    async def auth_code(self) -> dict | None:
        return await _call(self._s, "GET", LIBRESPOT_URL + "/auth/code", timeout=3)

    async def play(self, uri: str, skip_to_uri: str | None = None, position: int | None = None) -> None:
        body: dict[str, Any] = {"uri": valid_uri(uri)}
        if skip_to_uri:
            body["skip_to_uri"] = valid_uri(skip_to_uri)
        if position:
            body["position"] = int(position)
        await self._post("/player/play", body)

    async def resume(self) -> None:
        await self._post("/player/resume")

    async def pause(self) -> None:
        await self._post("/player/pause")

    async def playpause(self) -> None:
        await self._post("/player/playpause")

    async def next(self) -> None:
        await self._post("/player/next", {})

    async def prev(self) -> None:
        await self._post("/player/prev")

    async def seek(self, position_ms: int) -> None:
        await self._post("/player/seek", {"position": max(0, int(position_ms))})

    async def volume(self, percent: int) -> None:
        await self._post("/player/volume", {"volume": max(0, min(100, int(percent)))})

    async def shuffle(self, on: bool) -> None:
        await self._post("/player/shuffle_context", {"shuffle_context": bool(on)})

    async def repeat(self, mode: str) -> None:
        await self._post("/player/repeat_context", {"repeat_context": mode in ("context", "all")})
        await self._post("/player/repeat_track", {"repeat_track": mode == "track"})

    async def add_to_queue(self, uri: str) -> None:
        await self._post("/player/add_to_queue", {"uri": valid_uri(uri)})

    async def set_device_name(self, name: str) -> None:
        await self._post("/set_device_name", {"name": name})

    async def events(self, on_event: Callable[[dict], Awaitable[None]], stop: asyncio.Event) -> None:
        """Follow the WebSocket event stream; reconnect with backoff until stopped."""
        delay = 2
        while not stop.is_set():
            try:
                async with self._s.ws_connect(LIBRESPOT_URL.replace("http", "ws") + "/events",
                                              heartbeat=30) as ws:
                    delay = 2
                    await on_event({"type": "receiver_connected", "data": {}})
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                await on_event(json.loads(msg.data))
                            except ValueError:
                                pass
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
                pass
            if stop.is_set():
                return
            await asyncio.sleep(delay)
            delay = min(30, delay * 2)


class OwnTone:
    """OwnTone JSON API on 127.0.0.1:3689 – only used for the AirPlay outputs."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._s = session

    async def outputs(self) -> list[dict]:
        data = await _call(self._s, "GET", OWNTONE_URL + "/api/outputs", what="OwnTone") or {}
        result = []
        for o in data.get("outputs", []):
            if o.get("type") == "fifo":
                continue
            result.append({
                "id": str(o.get("id")),
                "name": o.get("name") or "Lautsprecher",
                "type": o.get("type"),
                "selected": bool(o.get("selected")),
                "volume": o.get("volume"),
                "needs_pin": bool(o.get("needs_auth_key") or o.get("requires_auth")),
                "has_password": bool(o.get("has_password")),
            })
        return sorted(result, key=lambda o: o["name"].lower())

    async def set_output(self, output_id: str, *, selected: bool | None = None,
                         volume: int | None = None, pin: str | None = None) -> None:
        body: dict[str, Any] = {}
        if selected is not None:
            body["selected"] = bool(selected)
        if volume is not None:
            body["volume"] = max(0, min(100, int(volume)))
        if pin:
            body["pin"] = str(pin)
        if not str(output_id).isdigit():
            raise SpotifyError("Ungültige Lautsprecher-ID.", 400)
        await _call(self._s, "PUT", f"{OWNTONE_URL}/api/outputs/{output_id}", body, what="OwnTone")

    async def set_outputs(self, output_ids: list[str]) -> None:
        """Select exactly these outputs (all others are deselected)."""
        ids = [str(i) for i in output_ids]
        if not all(i.isdigit() for i in ids):
            raise SpotifyError("Ungültige Lautsprecher-ID.", 400)
        await _call(self._s, "PUT", OWNTONE_URL + "/api/outputs/set", {"outputs": ids}, what="OwnTone")

    async def player(self) -> dict:
        return await _call(self._s, "GET", OWNTONE_URL + "/api/player", what="OwnTone") or {}

    async def master_volume(self, percent: int) -> None:
        await _call(self._s, "PUT", OWNTONE_URL + "/api/player/volume",
                    params={"volume": max(0, min(100, int(percent)))}, what="OwnTone")

    async def stop(self) -> None:
        await _call(self._s, "PUT", OWNTONE_URL + "/api/player/stop", what="OwnTone")

    async def clear_queue(self) -> None:
        await _call(self._s, "PUT", OWNTONE_URL + "/api/queue/clear", what="OwnTone")

    async def play_url(self, url: str) -> None:
        """Replace the queue with one stream/file URL and start it (announcements)."""
        await _call(self._s, "POST", OWNTONE_URL + "/api/queue/items/add",
                    params={"uris": url, "clear": "true", "playback": "start"}, what="OwnTone")

    async def append_url(self, url: str) -> None:
        """Append a URL to the end of the queue (plays right after the current item, gapless)."""
        await _call(self._s, "POST", OWNTONE_URL + "/api/queue/items/add", params={"uris": url}, what="OwnTone")


class MetaPipe:
    """Shairport-style metadata pipe next to the audio pipe (<pipe>.metadata).

    OwnTone attaches each message to the audio it reads next and applies it when
    that audio is actually heard (after its output buffer). Sending the Spotify
    track position this way lets OwnTone's progress follow the audible position
    exactly - which is what the synced lyrics need.
    """

    SAMPLE_RATE = 44100
    BASE = 1_000_000  # RTP-like start value; must be non-zero

    def __init__(self, path: str) -> None:
        self.path = path
        self._fd: int | None = None

    @staticmethod
    def item(code: str, data: bytes) -> bytes:
        import base64
        return (f"<item><type>{'ssnc'.encode().hex()}</type><code>{code.encode().hex()}</code>"
                f"<length>{len(data)}</length>\n<data encoding=\"base64\">\n"
                f"{base64.b64encode(data).decode()}</data></item>\n").encode()

    @classmethod
    def progress_item(cls, pos_ms: int, dur_ms: int | None) -> bytes:
        start = cls.BASE
        pos = start + int(pos_ms) * cls.SAMPLE_RATE // 1000
        end = start + int(dur_ms or 0) * cls.SAMPLE_RATE // 1000
        if end <= pos:
            end = pos + cls.SAMPLE_RATE
        return cls.item("prgr", f"{start}/{pos}/{end}".encode() + b"\0")

    def _open(self) -> int | None:
        import os
        if self._fd is not None:
            return self._fd
        try:
            self._fd = os.open(self.path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError:  # ENXIO: OwnTone is not reading (nothing playing)
            self._fd = None
        return self._fd

    def send(self, payload: bytes) -> bool:
        import os
        for _ in range(2):
            fd = self._open()
            if fd is None:
                return False
            try:
                os.write(fd, payload)
                return True
            except BlockingIOError:
                return False
            except OSError:  # reader went away -> reopen once
                self.close()
        return False

    def close(self) -> None:
        import os
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
