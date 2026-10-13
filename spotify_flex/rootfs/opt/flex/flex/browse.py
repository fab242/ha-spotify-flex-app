"""Library navigation shared by the HA media browser and the dashboard card."""
from __future__ import annotations

from typing import Any

from .api import SpotifyClient, SpotifyError, valid_id

ROOT = "root"
CATEGORIES: list[tuple[str, str, str]] = [
    # node, title, mdi icon (card) – order = display order
    ("playlists", "Playlists", "mdi:playlist-music"),
    ("liked", "Lieblingssongs", "mdi:heart"),
    ("albums", "Alben", "mdi:album"),
    ("artists", "Künstler", "mdi:account-music"),
    ("recent", "Zuletzt gehört", "mdi:history"),
    ("top_tracks", "Meine Top-Titel", "mdi:trophy"),
    ("top_artists", "Meine Top-Künstler", "mdi:star"),
    ("shows", "Podcasts", "mdi:podcast"),
    ("episodes", "Gespeicherte Episoden", "mdi:microphone"),
    ("audiobooks", "Hörbücher", "mdi:book-music"),
]
TITLES = {node: title for node, title, _ in CATEGORIES}
CONTAINERS = ("playlist", "album", "artist", "show", "audiobook")


def _with_nodes(page: dict, context_uri: str | None = None) -> dict:
    for item in page.get("items", []):
        if item["expandable"] and item.get("id") and item["type"] in CONTAINERS:
            item["node"] = f"{item['type']}:{item['id']}"
        if context_uri and item["type"] in ("track", "episode", "chapter"):
            item["context_uri"] = context_uri
    return page


async def browse(api: SpotifyClient, user_id: str, node: str | None, offset: int = 0) -> dict[str, Any]:
    node = (node or ROOT).strip()
    offset = max(0, int(offset or 0))

    if node == ROOT:
        return {
            "node": ROOT, "title": "Spotify-Bibliothek", "context_uri": None,
            "items": [
                {"id": n, "node": n, "uri": None, "type": "category", "name": t, "subtitle": "",
                 "image": None, "icon": i, "playable": n == "liked", "expandable": True}
                for n, t, i in CATEGORIES
            ],
            "total": len(CATEGORIES), "offset": 0, "next_offset": None,
        }

    collection = f"spotify:user:{user_id}:collection"
    context = None
    title = TITLES.get(node)
    if node == "playlists":
        page = await api.my_playlists(offset)
    elif node == "liked":
        page = await api.liked_tracks(offset)
        context = collection
    elif node == "albums":
        page = await api.saved_albums(offset)
    elif node == "artists":
        page = await api.followed_artists()
    elif node == "recent":
        page = await api.recently_played()
    elif node == "top_tracks":
        page = await api.top("tracks", offset=offset)
    elif node == "top_artists":
        page = await api.top("artists", offset=offset)
    elif node == "shows":
        page = await api.saved_shows(offset)
    elif node == "episodes":
        page = await api.saved_episodes(offset)
    elif node == "audiobooks":
        page = await api.saved_audiobooks(offset)
    elif ":" in node:
        kind, ident = node.split(":", 1)
        ident = valid_id(ident)
        context = f"spotify:{kind}:{ident}"
        if kind == "playlist":
            meta = await api.playlist(ident)
            try:
                page = await api.playlist_items(ident, offset)
            except SpotifyError as err:
                if err.status != 403:
                    raise
                page = {"items": [], "total": None, "offset": offset, "next_offset": None,
                        "cursor": None, "skipped": 0, "notice": str(err)}
            title = meta.get("name") if meta else None
            owner = (meta.get("owner") or {}).get("id")
            page["playlist"] = {
                "id": ident, "name": title, "description": meta.get("description") or "",
                "public": meta.get("public"), "snapshot_id": meta.get("snapshot_id"),
                "owner_id": owner, "editable": owner == user_id or bool(meta.get("collaborative")),
            }
        elif kind == "album":
            page = await api.album_tracks(ident, offset)
            title = page.pop("title", None)
        elif kind == "artist":
            page = await api.artist_albums(ident, offset)
        elif kind == "show":
            page = await api.show_episodes(ident, offset)
        elif kind == "audiobook":
            page = await api.audiobook_chapters(ident, offset)
        else:
            raise SpotifyError(f"Unbekannter Bereich: {node}", 400)
        if kind == "artist":
            # play the artist as context; albums inside stay expandable
            _with_nodes(page)
            return {"node": node, "title": title or "Künstler", "context_uri": context, **page}
    else:
        raise SpotifyError(f"Unbekannter Bereich: {node}", 400)

    _with_nodes(page, context)
    return {"node": node, "title": title or "Spotify", "context_uri": context, **page}
