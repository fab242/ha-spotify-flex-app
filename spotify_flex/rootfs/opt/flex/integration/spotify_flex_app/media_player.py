"""Media players: the Spotify Flex player plus one player per AirPlay speaker.

Speakers can be grouped with the standard Home Assistant "join" (group) dialog,
switched via the source list (saved groups and single speakers) or turned on/off.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.media_player import (
    BrowseError, BrowseMedia, MediaClass, MediaPlayerDeviceClass, MediaPlayerEntity,
    MediaPlayerEntityFeature as F, MediaPlayerState, MediaType, RepeatMode,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .client import FlexError
from .const import DOMAIN, VERSION
from .coordinator import FlexCoordinator

NODE = "flex:node:"
CLASS = {
    "track": MediaClass.TRACK, "episode": MediaClass.EPISODE, "chapter": MediaClass.EPISODE,
    "album": MediaClass.ALBUM, "artist": MediaClass.ARTIST, "playlist": MediaClass.PLAYLIST,
    "show": MediaClass.PODCAST, "audiobook": MediaClass.PODCAST, "category": MediaClass.DIRECTORY,
}
REPEAT_TO_HA = {"off": RepeatMode.OFF, "context": RepeatMode.ALL, "track": RepeatMode.ONE}
REPEAT_TO_APP = {v: k for k, v in REPEAT_TO_HA.items()}

TRANSPORT = F.PLAY | F.PAUSE | F.NEXT_TRACK | F.PREVIOUS_TRACK | F.SEEK
MAIN_FEATURES = (TRANSPORT | F.VOLUME_SET | F.VOLUME_STEP | F.SHUFFLE_SET | F.REPEAT_SET
                 | F.SELECT_SOURCE | F.GROUPING | F.PLAY_MEDIA | F.BROWSE_MEDIA | F.TURN_OFF)
SPEAKER_FEATURES = (TRANSPORT | F.VOLUME_SET | F.VOLUME_STEP | F.TURN_ON | F.TURN_OFF | F.GROUPING
                    | F.SELECT_SOURCE | F.PLAY_MEDIA | F.BROWSE_MEDIA)


def main_device(coordinator: FlexCoordinator) -> DeviceInfo:
    return DeviceInfo(identifiers={(DOMAIN, "app")}, name="Spotify Flex", manufacturer="Spotify Flex",
                      model="Spotify Connect + AirPlay", sw_version=(coordinator.data or {}).get("version"))


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: FlexCoordinator = entry.runtime_data
    main = FlexPlayer(coordinator)
    async_add_entities([main])
    known: set[str] = set()

    @callback
    def add_new() -> None:
        new = [s for s in coordinator.speakers if s["id"] not in known]
        if new:
            known.update(s["id"] for s in new)
            async_add_entities([FlexSpeaker(coordinator, s["id"], s["name"]) for s in new])

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class FlexBase(CoordinatorEntity[FlexCoordinator], MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_media_image_remotely_accessible = True
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER

    def __init__(self, coordinator: FlexCoordinator) -> None:
        super().__init__(coordinator)
        self._pos: int | None = None
        self._pos_at = None
        self._raw = None
        self._remember_position()

    # ---- shared helpers
    def _remember_position(self) -> None:
        """Position = what is audible (the app subtracts the measured audio delay).

        It is stamped with the time the app measured it; a negative value means the
        previous track is still audible, so playback of this one starts in the future."""
        track = self.coordinator.player.get("track") or {}
        pos = track.get("position_ms")
        at = track.get("position_at")
        if pos is None:
            self._pos, self._pos_at, self._raw = None, None, None
            return
        if (pos, at) == self._raw:
            return
        self._raw = (pos, at)
        base = dt_util.utc_from_timestamp(at / 1000) if isinstance(at, (int, float)) and at > 0 else dt_util.utcnow()
        if pos < 0:
            base, pos = base + timedelta(milliseconds=-pos), 0
        self._pos, self._pos_at = pos, base

    @callback
    def _handle_coordinator_update(self) -> None:
        self._remember_position()
        super()._handle_coordinator_update()

    def _speaker_entity_id(self, sid: str) -> str | None:
        return er.async_get(self.hass).async_get_entity_id("media_player", DOMAIN, f"speaker_{sid}")

    def _main_entity_id(self) -> str | None:
        return er.async_get(self.hass).async_get_entity_id("media_player", DOMAIN, "player")

    def _ids_from_entities(self, entity_ids: list[str]) -> list[str]:
        reg = er.async_get(self.hass)
        ids = []
        for eid in entity_ids:
            ent = reg.async_get(eid)
            if not ent or ent.platform != DOMAIN:
                raise ServiceValidationError(f"{eid} ist kein Spotify-Flex-Lautsprecher.")
            if ent.unique_id.startswith("speaker_"):
                ids.append(ent.unique_id.removeprefix("speaker_"))
        return ids

    @property
    def _playback_state(self) -> MediaPlayerState:
        p = self.coordinator.player
        if not p.get("online"):
            return MediaPlayerState.IDLE
        if p.get("playing"):
            return MediaPlayerState.PLAYING
        if p.get("paused"):
            return MediaPlayerState.PAUSED
        return MediaPlayerState.IDLE

    @property
    def _track(self) -> dict:
        return self.coordinator.player.get("track") or {}

    # ---- media info (shown on every player that is part of the playback)
    @property
    def media_content_id(self) -> str | None:
        return self._track.get("uri")

    @property
    def media_content_type(self) -> str | None:
        uri = self._track.get("uri") or ""
        return MediaType.PODCAST if ":episode:" in uri else MediaType.MUSIC if uri else None

    @property
    def media_title(self) -> str | None:
        return self._track.get("name")

    @property
    def media_artist(self) -> str | None:
        return self._track.get("artists")

    @property
    def media_album_name(self) -> str | None:
        return self._track.get("album")

    @property
    def media_image_url(self) -> str | None:
        return self._track.get("image")

    @property
    def media_duration(self) -> int | None:
        d = self._track.get("duration_ms")
        return round(d / 1000) if d else None

    @property
    def media_position(self) -> int | None:
        # fractions matter for synced lyrics
        return round(self._pos / 1000, 3) if self._pos is not None else None

    @property
    def media_position_updated_at(self):
        return self._pos_at if self._pos is not None else None

    @property
    def source_list(self) -> list[str]:
        return [g["name"] for g in self.coordinator.groups] + [s["name"] for s in self.coordinator.speakers]

    @property
    def source(self) -> str | None:
        active = (self.coordinator.data or {}).get("active_group")
        for g in self.coordinator.groups:
            if g["id"] == active:
                return g["name"]
        sel = [s for s in self.coordinator.speakers if s.get("selected")]
        if len(sel) == 1:
            return sel[0]["name"]
        return f"{len(sel)} Lautsprecher" if sel else None

    async def async_select_source(self, source: str) -> None:
        for g in self.coordinator.groups:
            if g["name"] == source:
                await self.coordinator.command("POST", f"/api/groups/{g['id']}/activate", {})
                return
        for s in self.coordinator.speakers:
            if s["name"] == source:
                await self.coordinator.command("POST", "/api/speakers", {"speakers": [s["id"]]})
                return
        raise ServiceValidationError(f"Unbekannte Quelle: {source}")

    # ---- transport (goes to the one Spotify Flex receiver)
    async def _player(self, action: str, body: dict | None = None) -> None:
        await self.coordinator.command("POST", f"/api/player/{action}", body or {})

    async def async_media_play(self) -> None:
        await self._player("resume")

    async def async_media_pause(self) -> None:
        await self._player("pause")

    async def async_media_next_track(self) -> None:
        await self._player("next")

    async def async_media_previous_track(self) -> None:
        await self._player("prev")

    async def async_media_seek(self, position: float) -> None:
        await self._player("seek", {"position_ms": int(position * 1000)})

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        if media_id.startswith(NODE):
            _, sep, container_uri = media_id.partition("#")
            if not sep:
                raise ServiceValidationError("Dieser Eintrag ist ein Ordner und kann nicht abgespielt werden.")
            media_id = container_uri
        uri, _, context = media_id.partition("|")
        if not uri.startswith("spotify:") and uri != "liked":
            raise ServiceValidationError("Erwartet wird eine Spotify-URI (spotify:track:…, spotify:playlist:…).")
        result = await self.coordinator.command("POST", "/api/play",
                                                {"uri": uri, "context_uri": context or None})
        if isinstance(result, dict) and result.get("warning"):
            raise HomeAssistantError(result["warning"])

    async def async_browse_media(self, media_content_type: str | None = None,
                                 media_content_id: str | None = None) -> BrowseMedia:
        node, offset = "root", 0
        if media_content_id and media_content_id.startswith(NODE):
            rest = media_content_id.removeprefix(NODE).partition("#")[0]
            node, _, off = rest.rpartition("@") if "@" in rest else (rest, "", "0")
            offset = int(off or 0)
        try:
            page = await self.coordinator.client.request("GET", "/api/browse",
                                                         params={"node": node, "offset": offset}, timeout=30)
        except FlexError as err:
            raise BrowseError(str(err)) from err
        children = []
        for it in page.get("items", []):
            if it.get("expandable") and it.get("node"):
                # containers (playlist/album/…) stay browsable and are playable via "#<uri>"
                cid = f"{NODE}{it['node']}@0" + (f"#{it['uri']}" if it.get("playable") and it.get("uri") else "")
            elif it.get("uri"):
                cid = it["uri"] + (f"|{it['context_uri']}" if it.get("context_uri") else "")
            else:
                continue
            children.append(BrowseMedia(
                media_class=CLASS.get(it.get("type"), MediaClass.MUSIC),
                media_content_id=cid, media_content_type=it.get("type") or "music",
                title=it.get("name") or "", can_play=bool(it.get("playable") and it.get("uri")),
                can_expand=bool(it.get("expandable") and it.get("node")), thumbnail=it.get("image")))
        if page.get("next_offset"):
            children.append(BrowseMedia(
                media_class=MediaClass.DIRECTORY, media_content_id=f"{NODE}{node}@{page['next_offset']}",
                media_content_type="directory", title="Mehr …", can_play=False, can_expand=True))
        return BrowseMedia(
            media_class=MediaClass.DIRECTORY, media_content_id=f"{NODE}{node}@{offset}",
            media_content_type="directory", title=page.get("title") or "Spotify",
            can_play=False, can_expand=True, children=children,
            children_media_class=MediaClass.DIRECTORY)


class FlexPlayer(FlexBase):
    """The Spotify Flex receiver; its group = the active AirPlay speakers."""

    _attr_translation_key = "player"
    _attr_supported_features = MAIN_FEATURES

    def __init__(self, coordinator: FlexCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "player"
        self._attr_device_info = main_device(coordinator)

    @property
    def state(self) -> MediaPlayerState:
        return self._playback_state

    @property
    def volume_level(self) -> float | None:
        v = self.coordinator.player.get("volume")
        return v / 100 if v is not None else None

    @property
    def shuffle(self) -> bool | None:
        return self.coordinator.player.get("shuffle")

    @property
    def repeat(self) -> RepeatMode | None:
        return REPEAT_TO_HA.get(self.coordinator.player.get("repeat") or "off")

    @property
    def group_members(self) -> list[str] | None:
        members = [self.entity_id] if self.entity_id else []
        for sid in self.coordinator.selected_ids():
            eid = self._speaker_entity_id(sid)
            if eid:
                members.append(eid)
        return members

    @property
    def extra_state_attributes(self) -> dict:
        d = self.coordinator.data or {}
        return {"speakers": [s["name"] for s in self.coordinator.speakers if s.get("selected")],
                "receiver_logged_in": (d.get("receiver") or {}).get("logged_in"),
                "library_connected": (d.get("web") or {}).get("connected"),
                "sleep_timer_ends": self.coordinator.sleep_ends.isoformat() if self.coordinator.sleep_ends else None,
                "integration": "spotify_flex_app",
                "audio_latency_ms": (self.coordinator.player.get("track") or {}).get("latency_ms"),
                # all speaker players + group select, so cards need no registry lookup
                "speaker_entities": [e for e in (self._speaker_entity_id(s["id"]) for s in self.coordinator.speakers) if e],
                "group_entity": er.async_get(self.hass).async_get_entity_id("select", DOMAIN, "group")}

    async def async_set_volume_level(self, volume: float) -> None:
        await self._player("volume", {"percent": round(volume * 100)})

    async def async_volume_up(self) -> None:
        await self.async_set_volume_level(min(1.0, (self.volume_level or 0) + 0.05))

    async def async_volume_down(self) -> None:
        await self.async_set_volume_level(max(0.0, (self.volume_level or 0) - 0.05))

    async def async_set_shuffle(self, shuffle: bool) -> None:
        await self._player("shuffle", {"on": shuffle})

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        await self._player("repeat", {"mode": REPEAT_TO_APP.get(repeat, "off")})

    async def async_turn_off(self) -> None:
        await self._player("pause")
        await self.coordinator.command("POST", "/api/speakers", {"speakers": []})

    async def async_join_players(self, group_members: list[str]) -> None:
        ids = self._ids_from_entities(group_members)
        await self.coordinator.command("POST", "/api/speakers",
                                       {"speakers": list(dict.fromkeys(self.coordinator.selected_ids() + ids))})

    async def async_unjoin_player(self) -> None:
        await self.coordinator.command("POST", "/api/speakers", {"speakers": []})


class FlexSpeaker(FlexBase):
    """One AirPlay speaker (HomePod, Apple TV …) as output of Spotify Flex."""

    _attr_name = "Spotify Flex"
    _attr_supported_features = SPEAKER_FEATURES

    def __init__(self, coordinator: FlexCoordinator, sid: str, name: str) -> None:
        super().__init__(coordinator)
        self._sid = sid
        self._attr_unique_id = f"speaker_{sid}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, f"speaker_{sid}")}, name=name,
                                            manufacturer="AirPlay", model="AirPlay-Lautsprecher",
                                            via_device=(DOMAIN, "app"))

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # the player's group_members list this speaker's entity_id -> refresh everyone
        self.coordinator.async_update_listeners()

    @property
    def _spk(self) -> dict | None:
        return next((s for s in self.coordinator.speakers if s["id"] == self._sid), None)

    @property
    def available(self) -> bool:
        return super().available and self._spk is not None

    @property
    def state(self) -> MediaPlayerState:
        spk = self._spk
        if not spk or not spk.get("selected"):
            return MediaPlayerState.OFF
        return self._playback_state

    @property
    def volume_level(self) -> float | None:
        spk = self._spk
        return spk["volume"] / 100 if spk and spk.get("volume") is not None else None

    @property
    def group_members(self) -> list[str] | None:
        spk = self._spk
        if not spk or not spk.get("selected"):
            return [self.entity_id] if self.entity_id else []
        members = [m for m in [self._main_entity_id()] if m]
        for sid in self.coordinator.selected_ids():
            eid = self._speaker_entity_id(sid)
            if eid:
                members.append(eid)
        return members

    def _guard_on(self) -> None:
        spk = self._spk
        if not spk or not spk.get("selected"):
            raise ServiceValidationError(f"{spk['name'] if spk else 'Lautsprecher'} ist nicht eingeschaltet.")

    async def async_media_play(self) -> None:
        self._guard_on()
        await super().async_media_play()

    async def async_turn_on(self) -> None:
        await self.coordinator.command("POST", f"/api/speakers/{self._sid}", {"selected": True})

    async def async_turn_off(self) -> None:
        await self.coordinator.command("POST", f"/api/speakers/{self._sid}", {"selected": False})

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.command("POST", f"/api/speakers/{self._sid}", {"volume": round(volume * 100)})

    async def async_volume_up(self) -> None:
        await self.async_set_volume_level(min(1.0, (self.volume_level or 0) + 0.05))

    async def async_volume_down(self) -> None:
        await self.async_set_volume_level(max(0.0, (self.volume_level or 0) - 0.05))

    async def async_join_players(self, group_members: list[str]) -> None:
        ids = [self._sid] + self._ids_from_entities(group_members)
        await self.coordinator.command("POST", "/api/speakers",
                                       {"speakers": list(dict.fromkeys(self.coordinator.selected_ids() + ids))})

    async def async_unjoin_player(self) -> None:
        await self.async_turn_off()

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        # playing on a speaker = make it the output (keep others that already play) and start
        if not (self._spk or {}).get("selected"):
            await self.async_turn_on()
        await super().async_play_media(media_type, media_id, **kwargs)
