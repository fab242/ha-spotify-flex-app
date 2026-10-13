"""Minimal, defensive Spotify Web API client.

No Home Assistant imports: the client receives an aiohttp session and an
async callable that returns a valid access token. That keeps it testable.

Design rules (lessons from 0.1/0.2 and from Music Assistant debugging):
* Only ``https://api.spotify.com/v1`` is ever contacted with the token;
  redirects are never followed.
* Every request has a hard total timeout and the response is always
  released (``async with``).
* HTTP 429 sets one shared ``blocked_until``; while blocked, nothing is
  sent. Cached GETs are served instead when available. No key rotation,
  no circumvention.
* Writes (PUT/POST/DELETE) are never retried automatically, so an
  unclear outcome cannot cause duplicate changes.
* GETs are retried once on network errors / 5xx only.
* Concurrency is limited so the dashboard cannot burst the quota.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections import OrderedDict
from typing import Any, Awaitable, Callable
from urllib.parse import quote

import aiohttp

from .const import API_BASE, LIBRARY_URIS_MAX, PAGE_LIMIT, PLAYLIST_ITEMS_MAX, SEARCH_LIMIT_MAX
from .normalize import normalize, normalize_device, normalize_page

_LOGGER = logging.getLogger(__name__)

ID_RE = re.compile(r"^[A-Za-z0-9]{1,64}$")
URI_RE = re.compile(r"^spotify:(track|episode|album|artist|playlist|show|audiobook|chapter|user)(:[A-Za-z0-9._-]{1,128}){1,2}$")
PATH_RE = re.compile(r"^/[A-Za-z0-9/_\-.%]*$")
SEARCH_TYPES = ("album", "artist", "playlist", "track", "show", "episode", "audiobook")
CACHE_SIZE = 128


class SpotifyError(Exception):
    """Spotify returned an error or could not be reached."""

    def __init__(self, message: str, status: int | None = None, reason: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason


class SpotifyAuthError(SpotifyError):
    """Token rejected (401) – re-authentication required."""


class SpotifyRateLimited(SpotifyError):
    """HTTP 429 – Spotify asked us to wait."""

    def __init__(self, retry_after: float) -> None:
        super().__init__(f"Spotify-Ratenlimit aktiv, noch {int(retry_after)} s warten.", 429)
        self.retry_after = retry_after


class SpotifyNoDevice(SpotifyError):
    """No Spotify Connect device available / active."""


def valid_id(value: Any) -> str:
    if not isinstance(value, str) or not ID_RE.match(value):
        raise SpotifyError("Ungültige Spotify-ID.", 400)
    return value


def valid_uri(value: Any) -> str:
    if not isinstance(value, str) or not URI_RE.match(value):
        raise SpotifyError(f"Ungültige Spotify-URI: {value!r}", 400)
    return value


def uri_to_id(uri: str) -> str:
    return valid_uri(uri).split(":")[2]


class SpotifyClient:
    """Thin JSON client with shared rate-limit state and a small GET cache."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token_getter: Callable[[], Awaitable[str]],
        *,
        timeout: float = 15,
        concurrency: int = 2,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._session = session
        self._token_getter = token_getter
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._sem = asyncio.Semaphore(concurrency)
        self._clock = clock
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self.blocked_until = 0.0
        self.last_status: int | None = None
        self.last_error: str | None = None
        self.request_count = 0

    # ------------------------------------------------------------------ core
    @property
    def retry_after(self) -> float:
        return max(0.0, self.blocked_until - self._clock())

    def clear_cache(self) -> None:
        self._cache.clear()

    def _cache_get(self, key: str, ttl: float, allow_stale: bool = False) -> Any:
        hit = self._cache.get(key)
        if hit is None:
            return None
        stamp, value = hit
        if allow_stale or self._clock() - stamp <= ttl:
            self._cache.move_to_end(key)
            return value
        return None

    def _cache_put(self, key: str, value: Any) -> None:
        self._cache[key] = (self._clock(), value)
        self._cache.move_to_end(key)
        while len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        body: Any = None,
        cache_ttl: float = 0,
    ) -> Any:
        method = method.upper()
        if method not in ("GET", "POST", "PUT", "DELETE"):
            raise SpotifyError("Nicht erlaubte HTTP-Methode.", 400)
        if path.startswith(API_BASE):
            path = path[len(API_BASE):]
        if not PATH_RE.match(path) or ".." in path:
            raise SpotifyError("Nur Pfade innerhalb von api.spotify.com/v1 sind erlaubt.", 400)
        params = {k: v for k, v in (params or {}).items() if v is not None}
        key = method + path + "?" + json.dumps(params, sort_keys=True, default=str)

        if method == "GET" and cache_ttl:
            cached = self._cache_get(key, cache_ttl)
            if cached is not None:
                return cached
        if self.retry_after > 0:
            if method == "GET":
                stale = self._cache_get(key, 0, allow_stale=True)
                if stale is not None:
                    return stale
            raise SpotifyRateLimited(self.retry_after)

        attempts = 2 if method == "GET" else 1
        for attempt in range(attempts):
            try:
                result = await self._send(method, path, params, body)
            except SpotifyError as err:
                retryable = err.status is None or (err.status >= 500 and err.status != 501)
                if attempt + 1 < attempts and retryable and not isinstance(err, SpotifyRateLimited):
                    await asyncio.sleep(1.0)
                    continue
                self.last_error = str(err)
                if method == "GET" and not isinstance(err, SpotifyAuthError):
                    stale = self._cache_get(key, 0, allow_stale=True)
                    if stale is not None and err.status in (None, 429, 500, 502, 503, 504):
                        return stale
                raise
            self.last_error = None
            if method == "GET" and cache_ttl and result is not None:
                self._cache_put(key, result)
            elif method != "GET":
                self.clear_cache()
            return result
        raise SpotifyError("unreachable")  # pragma: no cover

    async def _send(self, method: str, path: str, params: dict, body: Any) -> Any:
        token = await self._token_getter()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        kwargs: dict[str, Any] = {
            "headers": headers,
            "params": params or None,
            "allow_redirects": False,
            "timeout": self._timeout,
        }
        if isinstance(body, (bytes, str)) and method == "PUT" and path.endswith("/images"):
            headers["Content-Type"] = "image/jpeg"
            kwargs["data"] = body
        elif body is not None:
            kwargs["json"] = body
        async with self._sem:
            self.request_count += 1
            try:
                async with self._session.request(method, API_BASE + path, **kwargs) as resp:
                    self.last_status = resp.status
                    text = await resp.text()
                    return self._handle(resp.status, resp.headers, text)
            except asyncio.TimeoutError as err:
                self.last_status = None
                raise SpotifyError("Spotify antwortet nicht (Zeitüberschreitung).") from err
            except aiohttp.ClientError as err:
                self.last_status = None
                raise SpotifyError(f"Spotify nicht erreichbar: {type(err).__name__}") from err

    def _handle(self, status: int, headers: Any, text: str) -> Any:
        data: Any = None
        if text:
            try:
                data = json.loads(text)
            except ValueError:
                data = None
        if 200 <= status < 300:
            return data if data is not None else {}
        message, reason = f"HTTP {status}", None
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                message = err.get("message") or message
                reason = err.get("reason")
            elif isinstance(err, str):
                message = data.get("error_description") or err
        if status == 429:
            try:
                wait = float(headers.get("Retry-After", 30))
            except (TypeError, ValueError):
                wait = 30.0
            wait = max(1.0, wait)
            self.blocked_until = self._clock() + wait
            raise SpotifyRateLimited(wait)
        if status == 401:
            raise SpotifyAuthError(f"Spotify-Anmeldung abgelaufen: {message}", 401, reason)
        if status == 404 and reason == "NO_ACTIVE_DEVICE":
            raise SpotifyNoDevice("Kein aktives Spotify-Gerät.", 404, reason)
        if status == 404 and "device" in message.lower():
            raise SpotifyNoDevice(f"Spotify-Gerät nicht gefunden: {message}", 404, reason)
        if status >= 300 and status < 400:
            raise SpotifyError("Weiterleitung von Spotify wird aus Sicherheitsgründen nicht verfolgt.", status)
        raise SpotifyError(f"Spotify: {message}", status, reason)

    # -------------------------------------------------------------- profile
    async def profile(self) -> dict:
        data = await self.request("GET", "/me", cache_ttl=3600)
        return data if isinstance(data, dict) else {}

    # ---------------------------------------------------------------- player
    async def playback(self) -> dict | None:
        data = await self.request("GET", "/me/player", params={"additional_types": "track,episode"})
        return data if isinstance(data, dict) and data else None

    async def devices(self) -> list[dict]:
        data = await self.request("GET", "/me/player/devices")
        raw = data.get("devices") if isinstance(data, dict) else None
        return [d for d in (normalize_device(x) for x in (raw or [])) if d]

    async def play(
        self,
        device_id: str | None = None,
        *,
        uris: list[str] | None = None,
        context_uri: str | None = None,
        offset_uri: str | None = None,
        offset_position: int | None = None,
        position_ms: int | None = None,
    ) -> None:
        body: dict[str, Any] = {}
        if context_uri:
            body["context_uri"] = valid_uri(context_uri)
        if uris:
            body["uris"] = [valid_uri(u) for u in uris][:100]
        if offset_uri:
            body["offset"] = {"uri": valid_uri(offset_uri)}
        elif offset_position is not None:
            body["offset"] = {"position": int(offset_position)}
        if position_ms:
            body["position_ms"] = int(position_ms)
        await self.request("PUT", "/me/player/play", params={"device_id": device_id}, body=body or None)

    async def pause(self, device_id: str | None = None) -> None:
        await self.request("PUT", "/me/player/pause", params={"device_id": device_id})

    async def next(self, device_id: str | None = None) -> None:
        await self.request("POST", "/me/player/next", params={"device_id": device_id})

    async def previous(self, device_id: str | None = None) -> None:
        await self.request("POST", "/me/player/previous", params={"device_id": device_id})

    async def seek(self, position_ms: int, device_id: str | None = None) -> None:
        await self.request("PUT", "/me/player/seek", params={"position_ms": int(position_ms), "device_id": device_id})

    async def volume(self, percent: int, device_id: str | None = None) -> None:
        percent = max(0, min(100, int(percent)))
        await self.request("PUT", "/me/player/volume", params={"volume_percent": percent, "device_id": device_id})

    async def shuffle(self, state: bool, device_id: str | None = None) -> None:
        await self.request("PUT", "/me/player/shuffle", params={"state": "true" if state else "false", "device_id": device_id})

    async def repeat(self, state: str, device_id: str | None = None) -> None:
        if state not in ("off", "context", "track"):
            raise SpotifyError("Repeat muss off, context oder track sein.", 400)
        await self.request("PUT", "/me/player/repeat", params={"state": state, "device_id": device_id})

    async def transfer(self, device_id: str, play: bool = False) -> None:
        await self.request("PUT", "/me/player", body={"device_ids": [device_id], "play": bool(play)})

    async def queue_add(self, uri: str, device_id: str | None = None) -> None:
        await self.request("POST", "/me/player/queue", params={"uri": valid_uri(uri), "device_id": device_id})

    async def queue(self) -> dict:
        data = await self.request("GET", "/me/player/queue")
        data = data if isinstance(data, dict) else {}
        return {
            "currently_playing": normalize(data.get("currently_playing")),
            "queue": [n for n in (normalize(x) for x in data.get("queue") or []) if n],
        }

    # --------------------------------------------------------------- library
    async def page(self, path: str, offset: int = 0, limit: int = PAGE_LIMIT, params: dict | None = None,
                   key: str | None = None, cache_ttl: float = 120) -> dict:
        query = {"limit": max(1, min(PAGE_LIMIT, int(limit))), "offset": max(0, int(offset)), **(params or {})}
        data = await self.request("GET", path, params=query, cache_ttl=cache_ttl)
        return normalize_page(data, offset, key)

    async def my_playlists(self, offset: int = 0, limit: int = PAGE_LIMIT) -> dict:
        return await self.page("/me/playlists", offset, limit)

    async def liked_tracks(self, offset: int = 0, limit: int = PAGE_LIMIT) -> dict:
        return await self.page("/me/tracks", offset, limit)

    async def saved_albums(self, offset: int = 0, limit: int = PAGE_LIMIT) -> dict:
        return await self.page("/me/albums", offset, limit)

    async def saved_shows(self, offset: int = 0, limit: int = PAGE_LIMIT) -> dict:
        return await self.page("/me/shows", offset, limit)

    async def saved_episodes(self, offset: int = 0, limit: int = PAGE_LIMIT) -> dict:
        return await self.page("/me/episodes", offset, limit)

    async def saved_audiobooks(self, offset: int = 0, limit: int = PAGE_LIMIT) -> dict:
        return await self.page("/me/audiobooks", offset, limit)

    async def followed_artists(self, after: str | None = None, limit: int = PAGE_LIMIT) -> dict:
        query = {"type": "artist", "limit": max(1, min(PAGE_LIMIT, int(limit))), "after": after}
        data = await self.request("GET", "/me/following", params=query, cache_ttl=300)
        return normalize_page(data, 0, "artists")

    async def recently_played(self, limit: int = PAGE_LIMIT) -> dict:
        data = await self.request("GET", "/me/player/recently-played", params={"limit": min(PAGE_LIMIT, limit)}, cache_ttl=60)
        page = normalize_page(data, 0)
        page["next_offset"] = None  # cursor based – one page is enough for a browser
        return page

    async def top(self, kind: str = "tracks", time_range: str = "medium_term", offset: int = 0) -> dict:
        if kind not in ("tracks", "artists") or time_range not in ("short_term", "medium_term", "long_term"):
            raise SpotifyError("Ungültige Top-Abfrage.", 400)
        return await self.page(f"/me/top/{kind}", offset, PAGE_LIMIT, {"time_range": time_range}, cache_ttl=600)

    async def playlist(self, playlist_id: str) -> dict:
        data = await self.request("GET", f"/playlists/{valid_id(playlist_id)}",
                                  params={"fields": "id,name,uri,type,owner,images,description,public,collaborative,snapshot_id,items(total),tracks(total)"},
                                  cache_ttl=120)
        return data if isinstance(data, dict) else {}

    async def playlist_items(self, playlist_id: str, offset: int = 0, limit: int = PAGE_LIMIT) -> dict:
        """Feb-2026 ``/items`` endpoint; ``/tracks`` only as read fallback on 404."""
        pid = valid_id(playlist_id)
        query = {"limit": max(1, min(PAGE_LIMIT, int(limit))), "offset": max(0, int(offset)), "additional_types": "track,episode"}
        try:
            data = await self.request("GET", f"/playlists/{pid}/items", params=query, cache_ttl=120)
        except SpotifyError as err:
            if err.status == 403:
                raise SpotifyError(
                    "Spotify gibt die Titel dieser Playlist nicht heraus (nur eigene oder gemeinsame Playlists). "
                    "Abspielen der ganzen Playlist ist trotzdem möglich.", 403, err.reason) from err
            if err.status != 404:
                raise
            data = await self.request("GET", f"/playlists/{pid}/tracks", params=query, cache_ttl=120)
        return normalize_page(data, offset)

    async def album_tracks(self, album_id: str, offset: int = 0) -> dict:
        album = await self.request("GET", f"/albums/{valid_id(album_id)}", cache_ttl=600)
        page = await self.page(f"/albums/{valid_id(album_id)}/tracks", offset)
        image = normalize(album).get("image") if isinstance(album, dict) and normalize(album) else None
        for item in page["items"]:
            item["image"] = item["image"] or image
        page["title"] = album.get("name") if isinstance(album, dict) else None
        return page

    async def artist_albums(self, artist_id: str, offset: int = 0) -> dict:
        return await self.page(f"/artists/{valid_id(artist_id)}/albums", offset, PAGE_LIMIT,
                               {"include_groups": "album,single,compilation"}, cache_ttl=600)

    async def show_episodes(self, show_id: str, offset: int = 0) -> dict:
        return await self.page(f"/shows/{valid_id(show_id)}/episodes", offset, cache_ttl=600)

    async def audiobook_chapters(self, book_id: str, offset: int = 0) -> dict:
        return await self.page(f"/audiobooks/{valid_id(book_id)}/chapters", offset, cache_ttl=600)

    async def search(self, query: str, types: list[str] | None = None, limit: int = SEARCH_LIMIT_MAX, offset: int = 0) -> dict:
        query = (query or "").strip()
        if not query:
            raise SpotifyError("Suchbegriff fehlt.", 400)
        types = [t for t in (types or ["track", "album", "artist", "playlist"]) if t in SEARCH_TYPES] or ["track"]
        limit = max(1, min(SEARCH_LIMIT_MAX, int(limit)))  # Feb-2026: max 10
        data = await self.request("GET", "/search", params={"q": query[:200], "type": ",".join(types), "limit": limit, "offset": max(0, int(offset))}, cache_ttl=60)
        result = {}
        for kind in types:
            result[kind + "s"] = normalize_page(data, offset, kind + "s")
        return result

    # ------------------------------------------------------- library writes
    async def library_save(self, uris: list[str]) -> None:
        uris = [valid_uri(u) for u in uris]
        for i in range(0, len(uris), LIBRARY_URIS_MAX):
            await self.request("PUT", "/me/library", params={"uris": ",".join(uris[i:i + LIBRARY_URIS_MAX])})

    async def library_remove(self, uris: list[str]) -> None:
        uris = [valid_uri(u) for u in uris]
        for i in range(0, len(uris), LIBRARY_URIS_MAX):
            await self.request("DELETE", "/me/library", params={"uris": ",".join(uris[i:i + LIBRARY_URIS_MAX])})

    async def library_contains(self, uris: list[str]) -> list[bool]:
        uris = [valid_uri(u) for u in uris][:LIBRARY_URIS_MAX]
        data = await self.request("GET", "/me/library/contains", params={"uris": ",".join(uris)})
        return [bool(x) for x in data] if isinstance(data, list) else []

    async def playlist_add(self, playlist_id: str, uris: list[str], position: int | None = None) -> dict:
        uris = [valid_uri(u) for u in uris]
        result: dict = {}
        for i in range(0, len(uris), PLAYLIST_ITEMS_MAX):
            body: dict[str, Any] = {"uris": uris[i:i + PLAYLIST_ITEMS_MAX]}
            if position is not None:
                body["position"] = int(position) + i
            result = await self.request("POST", f"/playlists/{valid_id(playlist_id)}/items", body=body)
        return result or {}

    async def playlist_remove(self, playlist_id: str, uris: list[str], snapshot_id: str | None = None) -> dict:
        uris = [valid_uri(u) for u in uris]
        result: dict = {}
        for i in range(0, len(uris), PLAYLIST_ITEMS_MAX):
            body: dict[str, Any] = {"items": [{"uri": u} for u in uris[i:i + PLAYLIST_ITEMS_MAX]]}
            if snapshot_id:
                body["snapshot_id"] = snapshot_id
            result = await self.request("DELETE", f"/playlists/{valid_id(playlist_id)}/items", body=body)
        return result or {}

    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> dict:
        if not name or len(name) > 100:
            raise SpotifyError("Playlist-Name fehlt oder ist zu lang.", 400)
        data = await self.request("POST", "/me/playlists", body={"name": name, "description": description, "public": bool(public)})
        return normalize(data) or {}

    async def update_playlist(self, playlist_id: str, *, name: str | None = None,
                              description: str | None = None, public: bool | None = None) -> None:
        body = {k: v for k, v in {"name": name, "description": description, "public": public}.items() if v is not None}
        if not body:
            return
        if "name" in body and (not body["name"] or len(body["name"]) > 100):
            raise SpotifyError("Playlist-Name fehlt oder ist zu lang.", 400)
        await self.request("PUT", f"/playlists/{valid_id(playlist_id)}", body=body)

    async def reorder_playlist(self, playlist_id: str, range_start: int, insert_before: int,
                               range_length: int = 1, snapshot_id: str | None = None) -> dict:
        body: dict[str, Any] = {"range_start": int(range_start), "insert_before": int(insert_before),
                                "range_length": max(1, int(range_length))}
        if snapshot_id:
            body["snapshot_id"] = snapshot_id
        return await self.request("PUT", f"/playlists/{valid_id(playlist_id)}/items", body=body) or {}

    @staticmethod
    def quote_query(value: str) -> str:
        return quote(value, safe="")
