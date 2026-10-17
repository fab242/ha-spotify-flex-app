"""Turn Spotify Web API objects into one small, stable shape.

Pure module, no Home Assistant imports, so it is unit-testable.

Handles every wrapper variant seen in the wild:
* Feb-2026 playlist items: ``{"added_at": ..., "item": {...track...}}``
* legacy playlist items:   ``{"added_at": ..., "track": {...}}``
* saved items:             ``{"added_at": ..., "album"|"show"|"audiobook"|"episode"|"track": {...}}``
* recently played:         ``{"played_at": ..., "track": {...}}``
* bare media objects (search, top items, artist albums ...)

A real media object is detected *before* trying wrapper keys, so a track
is never unwrapped into its own ``album``. Boolean flags such as
``"track": true`` / ``"episode": false`` inside a media object are never
treated as wrappers.
"""
from __future__ import annotations

from typing import Any

MEDIA_TYPES = (
    "track", "episode", "album", "artist", "playlist", "show", "audiobook", "chapter", "user",
)
WRAPPER_KEYS = ("item", "track", "episode", "album", "show", "audiobook", "chapter", "artist", "playlist")
EXPANDABLE = {"album", "artist", "playlist", "show", "audiobook", "collection"}
MAX_UNWRAP = 8


def _uri_type(uri: Any) -> str | None:
    if isinstance(uri, str) and uri.startswith("spotify:"):
        parts = uri.split(":")
        if len(parts) >= 3:
            if parts[1] == "user" and len(parts) >= 4 and parts[3] == "collection":
                return "collection"
            return parts[1]
    return None


def _is_media(obj: dict) -> bool:
    kind = obj.get("type")
    if isinstance(kind, str) and kind in MEDIA_TYPES and (obj.get("uri") or obj.get("id")):
        return True
    return kind is None and _uri_type(obj.get("uri")) in MEDIA_TYPES and bool(obj.get("name"))


def unwrap(raw: Any) -> dict | None:
    """Return the innermost media object or None."""
    obj = raw
    for _ in range(MAX_UNWRAP):
        if not isinstance(obj, dict):
            return None
        if _is_media(obj):
            return obj
        nxt = None
        for key in WRAPPER_KEYS:
            value = obj.get(key)
            if isinstance(value, dict) and value:
                nxt = value
                break
        if nxt is None:
            return None
        obj = nxt
    return None


def pick_image(images: Any, target: int = 300) -> str | None:
    if not isinstance(images, list):
        return None
    best, best_score = None, None
    for image in images:
        if not isinstance(image, dict) or not isinstance(image.get("url"), str):
            continue
        width = image.get("width") or target
        score = abs(int(width) - target) if isinstance(width, (int, float)) else 0
        if best_score is None or score < best_score:
            best, best_score = image["url"], score
    return best


def _names(people: Any) -> str:
    if not isinstance(people, list):
        return ""
    return ", ".join(p.get("name", "") for p in people if isinstance(p, dict) and p.get("name"))


MONTHS = ("Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez.")


def _date_de(value: Any) -> str:
    """'2026-10-12' -> '12. Okt. 2026'; '2026-10' -> 'Okt. 2026'; '2026' -> '2026'."""
    if not isinstance(value, str):
        return ""
    parts = value.split("-")
    try:
        if len(parts) >= 3:
            return f"{int(parts[2])}. {MONTHS[int(parts[1]) - 1]} {parts[0]}"
        if len(parts) == 2:
            return f"{MONTHS[int(parts[1]) - 1]} {parts[0]}"
    except (ValueError, IndexError):
        return ""
    return parts[0]


def _minutes(ms: Any) -> str:
    if not isinstance(ms, (int, float)) or ms <= 0:
        return ""
    total = max(1, round(ms / 60000))
    return f"{total // 60} Std. {total % 60} Min." if total >= 60 else f"{total} Min."


def episode_info(obj: dict) -> dict:
    """Release date, length and listening progress of a podcast episode."""
    duration = obj.get("duration_ms") if isinstance(obj.get("duration_ms"), int) else None
    resume = obj.get("resume_point") if isinstance(obj.get("resume_point"), dict) else {}
    played = bool(resume.get("fully_played"))
    pos = resume.get("resume_position_ms") if isinstance(resume.get("resume_position_ms"), int) else 0
    if played or (duration and pos >= duration - 15000):
        played, pos = True, 0
    parts = [_date_de(obj.get("release_date")), _minutes(duration)]
    if played:
        parts.append("angehört")
    elif pos > 0 and duration:
        parts.append(f"noch {_minutes(duration - pos)}")
    return {
        "release_date": obj.get("release_date") if isinstance(obj.get("release_date"), str) else None,
        "resume_ms": pos or None,
        "progress": round(pos / duration, 3) if pos and duration else (1.0 if played else 0.0),
        "fully_played": played,
        "detail": " · ".join(p for p in parts if p),
    }


def _count(obj: dict) -> int | None:
    for key in ("items", "tracks"):
        value = obj.get(key)
        if isinstance(value, dict) and isinstance(value.get("total"), int):
            return value["total"]
    total = obj.get("total_episodes") or obj.get("total_chapters") or obj.get("total_tracks")
    return total if isinstance(total, int) else None


def normalize(raw: Any) -> dict | None:
    """Normalize any Spotify object (wrapped or bare) to the card/browser shape."""
    obj = unwrap(raw)
    if obj is None:
        return None
    kind = obj.get("type") if isinstance(obj.get("type"), str) else None
    uri = obj.get("uri") if isinstance(obj.get("uri"), str) else None
    kind = _uri_type(uri) if kind in (None, "user") and _uri_type(uri) else kind
    if kind is None:
        return None
    is_local = bool(obj.get("is_local")) or (uri or "").startswith("spotify:local:")
    if not uri and obj.get("id"):
        uri = f"spotify:{kind}:{obj['id']}"

    if kind in ("track",):
        album = obj.get("album") if isinstance(obj.get("album"), dict) else {}
        subtitle = _names(obj.get("artists")) or album.get("name", "")
        image = pick_image(album.get("images")) or pick_image(obj.get("images"))
    elif kind == "episode":
        show = obj.get("show") if isinstance(obj.get("show"), dict) else {}
        extra = episode_info(obj)
        # in einer Podcast-Liste fehlt "show": dann nur Datum · Länge · Fortschritt
        subtitle = " · ".join(p for p in (show.get("name"), extra["detail"]) if p) or "Folge"
        image = pick_image(obj.get("images")) or pick_image(show.get("images"))
    elif kind == "album":
        subtitle = _names(obj.get("artists")) or "Album"
        image = pick_image(obj.get("images"))
    elif kind == "playlist":
        owner = obj.get("owner") if isinstance(obj.get("owner"), dict) else {}
        count = _count(obj)
        subtitle = owner.get("display_name") or owner.get("id") or "Playlist"
        if count is not None:
            subtitle = f"{subtitle} · {count} Titel"
        image = pick_image(obj.get("images"))
    elif kind == "artist":
        subtitle = "Künstler"
        image = pick_image(obj.get("images"))
    elif kind in ("show", "audiobook"):
        subtitle = _names(obj.get("authors")) or ("Hörbuch" if kind == "audiobook" else "Podcast")
        image = pick_image(obj.get("images"))
    else:
        subtitle = ""
        image = pick_image(obj.get("images"))

    playable = (not is_local) and obj.get("is_playable", True) is not False and bool(uri)
    out = {
        "id": obj.get("id"),
        "uri": uri,
        "type": kind,
        "name": obj.get("name") or ("Lokale Datei" if is_local else "Unbekannt"),
        "subtitle": subtitle,
        "image": image,
        "duration_ms": obj.get("duration_ms") if isinstance(obj.get("duration_ms"), int) else None,
        "explicit": bool(obj.get("explicit")),
        "playable": playable,
        "expandable": kind in EXPANDABLE,
        "is_local": is_local,
    }
    if kind == "episode":
        out.update(extra)
    return out


def page_container(payload: Any, key: str | None = None) -> dict:
    """Find the paging object (``{"items": [...]}``) inside a response."""
    if not isinstance(payload, dict):
        return {}
    if key and isinstance(payload.get(key), dict):
        return payload[key]
    if isinstance(payload.get("items"), list):
        return payload
    for value in payload.values():
        if isinstance(value, dict) and isinstance(value.get("items"), list):
            return value
    return {}


def normalize_page(payload: Any, offset: int = 0, key: str | None = None) -> dict:
    """Normalize a paged response; unusable entries are dropped, not fatal."""
    page = page_container(payload, key)
    raw_items = page.get("items") if isinstance(page.get("items"), list) else []
    items = [n for n in (normalize(raw) for raw in raw_items) if n]
    total = page.get("total") if isinstance(page.get("total"), int) else None
    has_next = bool(page.get("next"))
    next_offset = offset + len(raw_items) if has_next and raw_items else None
    cursor = None
    cursors = page.get("cursors")
    if has_next and isinstance(cursors, dict):
        cursor = cursors.get("after") or cursors.get("before")
    return {
        "items": items,
        "total": total if total is not None else (offset + len(raw_items) if not has_next else None),
        "offset": offset,
        "next_offset": next_offset,
        "cursor": cursor,
        "skipped": len(raw_items) - len(items),
    }


def normalize_device(raw: Any) -> dict | None:
    if not isinstance(raw, dict) or not raw.get("id"):
        return None
    return {
        "id": raw["id"],
        "name": raw.get("name") or "Spotify-Gerät",
        "type": raw.get("type") or "Unknown",
        "is_active": bool(raw.get("is_active")),
        "is_restricted": bool(raw.get("is_restricted")),
        "volume_percent": raw.get("volume_percent"),
        "supports_volume": raw.get("supports_volume", True) is not False,
    }
