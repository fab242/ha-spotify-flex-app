"""Integration test for custom_components/spotify_flex_app against a faked app API.

Run: pytest tests_ha  (needs pytest-homeassistant-custom-component)
"""
from __future__ import annotations

import asyncio
import copy
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.hassio import HassioServiceInfo

import custom_components.spotify_flex_app.client  # noqa: E402,F401  (patch target)

DOMAIN = "spotify_flex_app"

STATE = {
    "version": "1.1.0",
    "receiver": {"running": True, "logged_in": True, "auth_code": None},
    "web": {"configured": True, "connected": True},
    "player": {"online": True, "playing": True, "paused": False, "stopped": False, "volume": 60,
               "shuffle": False, "repeat": "off",
               "track": {"uri": "spotify:track:T1", "name": "Closer", "artists": "NIN", "album": "Downward",
                         "image": "https://i.scdn.co/x", "position_ms": 1000, "duration_ms": 300000}},
    "speakers": [
        {"id": "111", "name": "Badezimmer", "selected": True, "volume": 40, "needs_pin": False},
        {"id": "222", "name": "Kinderzimmer", "selected": False, "volume": 50, "needs_pin": False},
    ],
    "groups": [{"id": "abcdef123456", "name": "Oben", "speakers": ["111", "222"]}],
    "active_group": None,
}


class FakeApp:
    def __init__(self) -> None:
        self.state = copy.deepcopy(STATE)
        self.calls: list[tuple] = []

    def _spk(self):
        st = self.state
        sel = {s["id"] for s in st["speakers"] if s["selected"]}
        st["active_group"] = next((g["id"] for g in st["groups"] if set(g["speakers"]) == sel), None)
        return {"speakers": st["speakers"], "groups": st["groups"], "active_group": st["active_group"]}

    async def request(self, method, path, body=None, params=None, timeout=20):
        self.calls.append((method, path, body, params))
        if path == "/api/state":
            self._spk()
            return copy.deepcopy(self.state)
        if path == "/api/speakers" and method == "POST":
            ids = set(body["speakers"])
            for s in self.state["speakers"]:
                s["selected"] = s["id"] in ids
            return self._spk()
        if path.startswith("/api/speakers/"):
            sid = path.rsplit("/", 1)[1]
            for s in self.state["speakers"]:
                if s["id"] == sid:
                    if "selected" in body:
                        s["selected"] = body["selected"]
                    if "volume" in body:
                        s["volume"] = body["volume"]
            return self._spk()
        if path.endswith("/activate"):
            gid = path.split("/")[3]
            g = next(g for g in self.state["groups"] if g["id"] == gid)
            for s in self.state["speakers"]:
                s["selected"] = s["id"] in g["speakers"]
            return self._spk()
        if path.startswith("/api/player/"):
            return {"player": self.state["player"]}
        if path == "/api/play":
            return {"ok": True, "warning": None}
        if path == "/api/browse":
            return {"node": params["node"], "title": "Spotify-Bibliothek", "items": [
                {"id": "playlists", "node": "playlists", "uri": None, "type": "category", "name": "Playlists",
                 "playable": False, "expandable": True},
                {"id": "P1", "node": "playlist:P1", "uri": "spotify:playlist:P1", "type": "playlist",
                 "name": "Fabian", "playable": True, "expandable": True},
                {"id": "T2", "uri": "spotify:track:T2", "type": "track", "name": "Euphoria", "playable": True,
                 "expandable": False, "context_uri": "spotify:playlist:P1"},
            ], "next_offset": 50}
        raise AssertionError(f"unexpected {method} {path}")

    async def state_(self):
        return await self.request("GET", "/api/state")

    async def events(self, on_message, stop):
        await stop.wait()


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def fake():
    app = FakeApp()
    with patch(f"custom_components.{DOMAIN}.client.FlexClient.request", side_effect=app.request), \
         patch(f"custom_components.{DOMAIN}.client.FlexClient.state", side_effect=app.state_), \
         patch(f"custom_components.{DOMAIN}.client.FlexClient.events", side_effect=app.events):
        yield app


async def _setup_via_discovery(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_HASSIO},
        data=HassioServiceInfo(config={"host": "127.0.0.1", "port": 8099, "token": "x" * 43},
                               name="Spotify Flex", slug="f97c5b11_spotify_flex", uuid="1234"))
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "hassio_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY, result
    await hass.async_block_till_done()
    return result["result"]


async def test_discovery_entities_and_grouping(hass: HomeAssistant, fake: FakeApp) -> None:
    entry = await _setup_via_discovery(hass)
    assert entry.state is config_entries.ConfigEntryState.LOADED

    main = hass.states.get("media_player.spotify_flex_player")
    bad = hass.states.get("media_player.badezimmer_spotify_flex")
    kid = hass.states.get("media_player.kinderzimmer_spotify_flex")
    sel = hass.states.get("select.spotify_flex_speaker_group")
    assert main and bad and kid and sel, hass.states.async_entity_ids()
    assert main.state == "playing" and main.attributes["media_title"] == "Closer"
    assert main.attributes["group_members"] == ["media_player.spotify_flex_player",
                                                "media_player.badezimmer_spotify_flex"]
    assert bad.state == "playing" and kid.state == "off"
    assert main.attributes["source_list"] == ["Oben", "Badezimmer", "Kinderzimmer"]
    assert sel.attributes["options"] == ["Aus", "Oben"]

    # standard HA grouping dialog: join Kinderzimmer to the player
    await hass.services.async_call("media_player", "join", {
        "entity_id": "media_player.spotify_flex_player",
        "group_members": ["media_player.kinderzimmer_spotify_flex"]}, blocking=True)
    assert ("POST", "/api/speakers", {"speakers": ["111", "222"]}, None) in fake.calls
    await hass.async_block_till_done()
    assert hass.states.get("media_player.kinderzimmer_spotify_flex").state == "playing"
    assert hass.states.get("select.spotify_flex_speaker_group").state == "Oben"
    assert hass.states.get("media_player.spotify_flex_player").attributes["source"] == "Oben"

    # unjoin one speaker
    await hass.services.async_call("media_player", "unjoin",
                                   {"entity_id": "media_player.badezimmer_spotify_flex"}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get("media_player.badezimmer_spotify_flex").state == "off"

    # source = single speaker, then group via select
    await hass.services.async_call("media_player", "select_source", {
        "entity_id": "media_player.spotify_flex_player", "source": "Badezimmer"}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get("media_player.kinderzimmer_spotify_flex").state == "off"
    await hass.services.async_call("select", "select_option", {
        "entity_id": "select.spotify_flex_speaker_group", "option": "Oben"}, blocking=True)
    assert ("POST", "/api/groups/abcdef123456/activate", {}, None) in fake.calls
    await hass.services.async_call("select", "select_option", {
        "entity_id": "select.spotify_flex_speaker_group", "option": "Aus"}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get("select.spotify_flex_speaker_group").state == "Aus"

    # transport + speaker volume
    await hass.services.async_call("media_player", "media_pause",
                                   {"entity_id": "media_player.spotify_flex_player"}, blocking=True)
    assert ("POST", "/api/player/pause", {}, None) in fake.calls
    await hass.services.async_call("media_player", "turn_on",
                                   {"entity_id": "media_player.kinderzimmer_spotify_flex"}, blocking=True)
    await hass.services.async_call("media_player", "volume_set", {
        "entity_id": "media_player.kinderzimmer_spotify_flex", "volume_level": 0.3}, blocking=True)
    assert ("POST", "/api/speakers/222", {"volume": 30}, None) in fake.calls

    # play media from browse ids
    await hass.services.async_call("media_player", "play_media", {
        "entity_id": "media_player.spotify_flex_player", "media_content_type": "music",
        "media_content_id": "spotify:track:T2|spotify:playlist:P1"}, blocking=True)
    assert ("POST", "/api/play", {"uri": "spotify:track:T2", "context_uri": "spotify:playlist:P1"},
            None) in fake.calls


async def test_browse(hass: HomeAssistant, fake: FakeApp) -> None:
    await _setup_via_discovery(hass)
    ent = hass.data["media_player"].get_entity("media_player.spotify_flex_player")
    root = await ent.async_browse_media()
    titles = [c.title for c in root.children]
    assert titles == ["Playlists", "Fabian", "Euphoria", "Mehr …"]
    fabian = root.children[1]
    assert fabian.can_play and fabian.can_expand and fabian.media_content_id.endswith("#spotify:playlist:P1")
    await ent.async_play_media("playlist", fabian.media_content_id)
    assert fake.calls[-1][1:3] == ("/api/play", {"uri": "spotify:playlist:P1", "context_uri": None})
    more = await ent.async_browse_media("directory", root.children[-1].media_content_id)
    assert fake.calls[-1][3] == {"node": "root", "offset": 50}
    assert more.title


async def test_rediscovery_updates_token(hass: HomeAssistant, fake: FakeApp) -> None:
    entry = await _setup_via_discovery(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_HASSIO},
        data=HassioServiceInfo(config={"host": "127.0.0.1", "port": 8099, "token": "y" * 43},
                               name="Spotify Flex", slug="f97c5b11_spotify_flex", uuid="1234"))
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"
    assert entry.data["token"] == "y" * 43
    await asyncio.sleep(0)
