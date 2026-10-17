"""Services with responses for the Spotify Flex player card (search, queue, like, sleep timer, equalizer, announcements)."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

try:
    import probatio as vol
except ImportError:  # HA < 2026.x
    import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from homeassistant.components import media_source
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .client import FlexError
from .const import DOMAIN

NODE = "flex:node:"
SEARCH_TYPES = ("track", "artist", "album", "playlist", "show", "episode", "audiobook")
CONTAINERS = ("playlist", "album", "artist", "show", "audiobook")


def media_item(it: dict, context_uri: str | None = None) -> dict:
    """App item -> compact dict the card can show, play and open."""
    kind = it.get("type") or ""
    uri = it.get("uri")
    browse_id = None
    if kind in CONTAINERS and it.get("id"):
        browse_id = f"{NODE}{kind}:{it['id']}@0"
    if browse_id:
        play_id = f"{browse_id}#{uri}" if uri and it.get("playable", True) else None
    else:
        ctx = it.get("context_uri") or context_uri
        play_id = (uri + (f"|{ctx}" if ctx else "")) if uri else None
    out = {"title": it.get("name") or "", "subtitle": it.get("subtitle") or "", "image": it.get("image"),
           "type": kind, "uri": uri, "play_id": play_id, "browse_id": browse_id,
           "duration_ms": it.get("duration_ms")}
    if kind == "episode":  # Podcast-Folge: Erscheinungsdatum und Hörfortschritt
        out.update({k: it.get(k) for k in ("release_date", "resume_ms", "progress", "fully_played")})
    return out


def _coordinator(hass: HomeAssistant):
    entries = [e for e in hass.config_entries.async_loaded_entries(DOMAIN)]
    if not entries:
        raise ServiceValidationError("Spotify Flex ist nicht eingerichtet.")
    return entries[0].runtime_data


async def _call(hass: HomeAssistant, method: str, path: str, body: Any = None, params: dict | None = None) -> Any:
    try:
        return await _coordinator(hass).client.request(method, path, body, params=params, timeout=30)
    except FlexError as err:
        raise HomeAssistantError(str(err)) from err


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "search"):
        return

    async def search(call: ServiceCall) -> ServiceResponse:
        types = [t for t in call.data.get("types") or ["track", "artist", "album", "playlist"] if t in SEARCH_TYPES]
        data = await _call(hass, "GET", "/api/search",
                           params={"q": call.data["query"], "types": ",".join(types or ["track"])})
        groups = []
        for kind in types:
            page = (data or {}).get(kind + "s") or {}
            items = [media_item(it) for it in page.get("items") or []]
            if items:
                groups.append({"type": kind, "items": items})
        return {"groups": groups}

    async def browse(call: ServiceCall) -> ServiceResponse:
        """Eine Ebene der Bibliothek mit Untertiteln (Besitzer, Datum, Länge, Hörfortschritt)."""
        node = call.data.get("node") or "root"
        if node.startswith(NODE):
            node = node.removeprefix(NODE).partition("#")[0]
        offset = call.data.get("offset", 0)
        if "@" in node:
            node, _, off = node.rpartition("@")
            offset = int(off or 0) if off.isdigit() else offset
        page = await _call(hass, "GET", "/api/browse", params={"node": node, "offset": offset}) or {}
        items = [media_item(it) for it in page.get("items") or [] if it.get("uri") or it.get("node")]
        for it, raw in zip(items, [r for r in page.get("items") or [] if r.get("uri") or r.get("node")]):
            if raw.get("type") == "category":  # Startseite: Bereiche wie Playlists, Podcasts …
                it.update({"browse_id": f"{NODE}{raw['node']}@0", "play_id": None})
        nxt = page.get("next_offset")
        return {"title": page.get("title") or "", "node": f"{NODE}{node}@{offset}",
                "context_uri": page.get("context_uri"), "total": page.get("total"),
                "items": items, "next": f"{NODE}{node}@{nxt}" if nxt else None}

    async def queue(call: ServiceCall) -> ServiceResponse:
        data = await _call(hass, "GET", "/api/queue") or {}
        cur = data.get("currently_playing")
        return {"current": media_item(cur) if cur else None,
                "items": [media_item(it) for it in data.get("queue") or []][:50]}

    async def add_to_queue(call: ServiceCall) -> None:
        await _call(hass, "POST", "/api/player/queue", {"uri": call.data["uri"]})

    async def like(call: ServiceCall) -> ServiceResponse:
        action = call.data.get("action", "status")
        uri = call.data.get("uri")
        if not uri:
            now = await _call(hass, "GET", "/api/now/liked") or {}
            uri, liked = now.get("uri"), now.get("liked")
        else:
            res = await _call(hass, "POST", "/api/library", {"action": "contains", "uris": [uri]}) or {}
            liked = (res.get("contains") or [None])[0]
        if not uri:
            raise ServiceValidationError("Es läuft gerade kein Titel.")
        target = {"save": True, "remove": False, "toggle": not liked}.get(action)
        if target is not None and target != liked:
            await _call(hass, "POST", "/api/library", {"action": "save" if target else "remove", "uris": [uri]})
            liked = target
        return {"uri": uri, "liked": liked}

    async def sleep_timer(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator(hass)
        minutes = int(call.data["minutes"])
        if coordinator.sleep_cancel:
            coordinator.sleep_cancel()
            coordinator.sleep_cancel = None
        coordinator.sleep_ends = None
        if minutes > 0:
            async def _fire(_now) -> None:
                coordinator.sleep_cancel = None
                coordinator.sleep_ends = None
                try:
                    await coordinator.client.request("POST", "/api/player/pause", {})
                finally:
                    coordinator.async_update_listeners()

            coordinator.sleep_ends = dt_util.utcnow() + timedelta(minutes=minutes)
            coordinator.sleep_cancel = async_call_later(hass, minutes * 60, _fire)
        coordinator.async_update_listeners()
        return {"ends_at": coordinator.sleep_ends.isoformat() if coordinator.sleep_ends else None}

    async def _absolute(media_id: str) -> str:
        """media-source://… (z. B. TTS) auflösen und relative Pfade zu einer für die App erreichbaren URL machen."""
        url = media_id
        if media_source.is_media_source_id(media_id):
            try:
                url = (await media_source.async_resolve_media(hass, media_id, None)).url
            except Exception as err:  # noqa: BLE001 - message for the user
                raise HomeAssistantError(f"Durchsage konnte nicht erzeugt werden: {err}") from err
        if url.startswith("/"):
            try:
                base = get_url(hass, allow_external=False, prefer_external=False, allow_ip=True)
            except NoURLAvailableError:
                base = get_url(hass)
            url = base.rstrip("/") + url
        if not url.startswith(("http://", "https://")):
            raise ServiceValidationError("Für Durchsagen wird eine http(s)-Adresse oder media-source://… erwartet.")
        return url

    async def announce(call: ServiceCall) -> ServiceResponse:
        items = []
        for it in call.data["media"]:
            if isinstance(it, str):
                it = {"media_content_id": it}
            items.append({"url": await _absolute(str(it["media_content_id"])), "volume": it.get("volume")})
        wait = call.data.get("wait", True)
        timeout = int(call.data.get("timeout", 900))
        body = {"items": items, "group": call.data.get("group"), "wait": wait, "timeout": timeout}
        try:
            return await _coordinator(hass).client.request("POST", "/api/announce", body, timeout=timeout + 60 if wait else 30)
        except FlexError as err:
            raise HomeAssistantError(str(err)) from err

    async def stop_announcement(call: ServiceCall) -> None:
        await _call(hass, "POST", "/api/announce/stop", {})

    async def equalizer(call: ServiceCall) -> ServiceResponse:
        changes = {k: call.data[k] for k in ("enabled", "preset", "gains") if k in call.data}
        if changes:
            return await _call(hass, "PUT", "/api/config/eq", changes)
        return await _call(hass, "GET", "/api/config/eq")

    hass.services.async_register(DOMAIN, "search", search, vol.Schema({
        vol.Required("query"): vol.All(cv.string, vol.Length(min=1, max=200)),
        vol.Optional("types"): [vol.In(SEARCH_TYPES)],
    }), supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "queue", queue, vol.Schema({}), supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "browse", browse, vol.Schema({
        vol.Optional("node", default="root"): vol.All(cv.string, vol.Length(max=300)),
        vol.Optional("offset", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=100000)),
    }), supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "add_to_queue", add_to_queue, vol.Schema({
        vol.Required("uri"): vol.All(cv.string, vol.Match(r"^spotify:(track|episode):[A-Za-z0-9]+$")),
    }))
    hass.services.async_register(DOMAIN, "like", like, vol.Schema({
        vol.Optional("action", default="status"): vol.In(("status", "save", "remove", "toggle")),
        vol.Optional("uri"): vol.All(cv.string, vol.Match(r"^spotify:[a-z]+:[A-Za-z0-9]+$")),
    }), supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "equalizer", equalizer, vol.Schema({
        vol.Optional("enabled"): cv.boolean,
        vol.Optional("preset"): vol.All(cv.string, vol.Match(r"^[a-z_]{2,30}$")),
        vol.Optional("gains"): vol.All([vol.All(vol.Coerce(float), vol.Range(min=-12, max=12))], vol.Length(min=6, max=6)),
    }), supports_response=SupportsResponse.OPTIONAL)
    announce_item = vol.Any(cv.string, vol.Schema({
        vol.Required("media_content_id"): cv.string,
        vol.Optional("volume"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }, extra=vol.ALLOW_EXTRA))
    hass.services.async_register(DOMAIN, "announce", announce, vol.Schema({
        vol.Required("media"): vol.All(cv.ensure_list, [announce_item], vol.Length(min=1, max=10)),
        vol.Optional("group"): cv.string,
        vol.Optional("wait", default=True): cv.boolean,
        vol.Optional("timeout", default=900): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
    }), supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "stop_announcement", stop_announcement, vol.Schema({}))
    hass.services.async_register(DOMAIN, "sleep_timer", sleep_timer, vol.Schema({
        vol.Required("minutes"): vol.All(vol.Coerce(int), vol.Range(min=0, max=480)),
    }), supports_response=SupportsResponse.OPTIONAL)
