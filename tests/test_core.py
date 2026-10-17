import asyncio
import json
from pathlib import Path

import pytest

from flex.api import (
    SpotifyAuthError, SpotifyClient, SpotifyError, SpotifyNoDevice, SpotifyRateLimited, valid_uri,
)
from flex.normalize import normalize, normalize_page, unwrap

FIX = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------- normalize
def test_playlist_items_2026_item_wrapper():
    data = json.loads((FIX / "playlist_items_2026.json").read_text())
    page = normalize_page(data, 0)
    assert page["next_offset"] == 2
    assert page["total"] == 5
    first, local = page["items"]
    assert first["type"] == "track" and first["uri"] == "spotify:track:TR1"
    assert first["name"] == "Erster Titel"
    assert first["subtitle"] == "Künstler A, Künstler B"
    assert first["image"] == "https://i.scdn.co/300"
    assert first["playable"] is True and first["expandable"] is False
    assert local["is_local"] and local["playable"] is False


def test_boolean_track_flag_is_not_a_wrapper():
    obj = {"type": "track", "track": True, "episode": False, "id": "X", "uri": "spotify:track:X", "name": "n",
           "album": {"type": "album", "id": "A", "uri": "spotify:album:A", "name": "a"}}
    assert unwrap(obj) is obj  # must not unwrap into the album


def test_legacy_track_wrapper_and_saved_album_and_recent():
    legacy = {"added_at": "x", "track": {"type": "track", "id": "T", "uri": "spotify:track:T", "name": "Alt"}}
    assert normalize(legacy)["name"] == "Alt"
    saved = {"added_at": "x", "album": {"type": "album", "id": "A", "uri": "spotify:album:A", "name": "Alb",
                                        "artists": [{"name": "K"}]}}
    n = normalize(saved)
    assert n["type"] == "album" and n["expandable"] and n["subtitle"] == "K"
    recent = {"played_at": "x", "track": {"type": "track", "id": "R", "uri": "spotify:track:R", "name": "R"},
              "context": None}
    assert normalize(recent)["uri"] == "spotify:track:R"


def test_missing_type_uses_uri_and_garbage_is_dropped():
    assert normalize({"uri": "spotify:episode:E", "name": "Ep"})["type"] == "episode"
    page = normalize_page({"items": [None, {}, {"foo": 1}, {"item": None}], "next": None}, 0)
    assert page["items"] == [] and page["skipped"] == 4


def test_playlist_count_new_and_old_field():
    new = {"type": "playlist", "id": "P", "uri": "spotify:playlist:P", "name": "Sport",
           "owner": {"display_name": "Fab242"}, "items": {"total": 12}}
    old = {**new, "items": None, "tracks": {"total": 3}}
    assert normalize(new)["subtitle"] == "Fab242 · 12 Titel"
    assert normalize(old)["subtitle"] == "Fab242 · 3 Titel"


def test_search_page_by_key():
    data = {"tracks": {"items": [{"type": "track", "id": "T", "uri": "spotify:track:T", "name": "t"}], "next": None},
            "albums": {"items": [], "next": None}}
    assert normalize_page(data, 0, "tracks")["items"][0]["id"] == "T"
    assert normalize_page(data, 0, "albums")["items"] == []


def test_valid_uri():
    assert valid_uri("spotify:user:abc:collection")
    with pytest.raises(SpotifyError):
        valid_uri("https://evil")


# ---------------------------------------------------------------------- api
class FakeResp:
    def __init__(self, status, body="", headers=None):
        self.status, self._body, self.headers = status, body, headers or {}
        self.released = False

    async def text(self):
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.released = True


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


async def token():
    return "TOKEN"


def client(responses, clock=None):
    s = FakeSession(responses)
    return SpotifyClient(s, token, clock=clock or Clock()), s


def run(coro):
    return asyncio.run(coro)


def test_no_redirects_and_auth_header_and_release():
    resp = FakeResp(200, json.dumps({"id": "u"}))
    c, s = client([resp])
    assert run(c.profile())["id"] == "u"
    method, url, kw = s.calls[0]
    assert url == "https://api.spotify.com/v1/me"
    assert kw["allow_redirects"] is False
    assert kw["headers"]["Authorization"] == "Bearer TOKEN"
    assert resp.released


def test_rate_limit_blocks_and_serves_stale_cache():
    clock = Clock()
    c, s = client([FakeResp(200, json.dumps({"items": [], "next": None})), FakeResp(429, "", {"Retry-After": "40"})], clock)
    run(c.my_playlists())
    clock.t += 500  # cache expired
    page = run(c.my_playlists())  # 429 -> stale cache returned
    assert page["items"] == []
    assert 39 <= c.retry_after <= 40
    n = len(s.calls)
    with pytest.raises(SpotifyRateLimited):
        run(c.devices())  # blocked: nothing sent, no cache
    assert len(s.calls) == n
    clock.t += 41
    assert c.retry_after == 0


def test_writes_are_never_retried():
    c, s = client([FakeResp(503, "")])
    with pytest.raises(SpotifyError):
        run(c.next())
    assert len(s.calls) == 1


def test_get_retried_once_on_5xx():
    c, s = client([FakeResp(502, ""), FakeResp(200, json.dumps({"devices": [{"id": "d1", "name": "iPhone", "type": "Smartphone"}]}))])
    devs = run(c.devices())
    assert devs[0]["name"] == "iPhone" and len(s.calls) == 2


def test_auth_error_and_no_device():
    c, _ = client([FakeResp(401, json.dumps({"error": {"status": 401, "message": "expired"}}))])
    with pytest.raises(SpotifyAuthError):
        run(c.profile())
    c, _ = client([FakeResp(404, json.dumps({"error": {"status": 404, "message": "Player command failed: No active device found", "reason": "NO_ACTIVE_DEVICE"}}))])
    with pytest.raises(SpotifyNoDevice):
        run(c.play(None, uris=["spotify:track:X"]))


def test_empty_devices_is_not_an_error():
    c, _ = client([FakeResp(200, json.dumps({"devices": []}))])
    assert run(c.devices()) == []


def test_204_playback_is_none():
    c, _ = client([FakeResp(204, "")])
    assert run(c.playback()) is None


def test_playlist_items_uses_items_endpoint_and_403_message():
    data = (FIX / "playlist_items_2026.json").read_text()
    c, s = client([FakeResp(200, data)])
    page = run(c.playlist_items("PL1"))
    assert s.calls[0][1].endswith("/playlists/PL1/items")
    assert page["items"][0]["name"] == "Erster Titel"
    c, _ = client([FakeResp(403, json.dumps({"error": {"status": 403, "message": "Forbidden"}}))])
    with pytest.raises(SpotifyError) as err:
        run(c.playlist_items("PL2"))
    assert err.value.status == 403 and "eigene" in str(err.value)


def test_tracks_fallback_only_on_404():
    data = (FIX / "playlist_items_2026.json").read_text()
    c, s = client([FakeResp(404, json.dumps({"error": {"status": 404, "message": "nope"}})), FakeResp(200, data)])
    run(c.playlist_items("PL1"))
    assert s.calls[1][1].endswith("/playlists/PL1/tracks")


def test_path_validation_blocks_foreign_hosts():
    c, s = client([])
    for bad in ("https://evil.example/x", "/../../etc", "me/player"):
        with pytest.raises(SpotifyError):
            run(c.request("GET", bad))
    assert s.calls == []


def test_search_limit_capped_at_10():
    c, s = client([FakeResp(200, json.dumps({"tracks": {"items": [], "next": None}}))])
    run(c.search("abc", ["track"], limit=50))
    assert s.calls[0][2]["params"]["limit"] == 10


def test_library_save_uses_me_library_in_chunks_of_40():
    uris = [f"spotify:track:T{i}" for i in range(45)]
    c, s = client([FakeResp(200, ""), FakeResp(200, "")])
    run(c.library_save(uris))
    assert [x[0] for x in s.calls] == ["PUT", "PUT"]
    assert s.calls[0][1].endswith("/me/library")
    assert len(s.calls[0][2]["params"]["uris"].split(",")) == 40


def test_playlist_remove_uses_items_key():
    c, s = client([FakeResp(200, json.dumps({"snapshot_id": "s"}))])
    run(c.playlist_remove("PL1", ["spotify:track:A"]))
    assert s.calls[0][2]["json"] == {"items": [{"uri": "spotify:track:A"}]}


def test_timeout_is_reported():
    c, _ = client([asyncio.TimeoutError(), asyncio.TimeoutError()])
    with pytest.raises(SpotifyError) as err:
        run(c.devices())
    assert "Zeitüberschreitung" in str(err.value)


def test_episode_details_for_podcasts():
    from flex.normalize import normalize
    ep = {"type": "episode", "id": "E1", "uri": "spotify:episode:E1", "name": "Folge 1", "release_date": "2026-10-12",
          "duration_ms": 4_800_000, "resume_point": {"fully_played": False, "resume_position_ms": 754_000}}
    n = normalize(ep)
    assert n["subtitle"] == "12. Okt. 2026 · 1 Std. 20 Min. · noch 1 Std. 7 Min."
    assert n["resume_ms"] == 754_000 and n["progress"] == 0.157 and n["fully_played"] is False
    done = normalize({**ep, "resume_point": {"fully_played": True, "resume_position_ms": 0}})
    assert done["subtitle"].endswith("angehört") and done["resume_ms"] is None and done["progress"] == 1.0
    long = normalize({**ep, "duration_ms": 7_500_000, "resume_point": {}, "show": {"name": "Lage der Nation"}})
    assert long["subtitle"] == "Lage der Nation · 12. Okt. 2026 · 2 Std. 5 Min."
    assert normalize({**ep, "release_date": "2026-10", "release_date_precision": "month"})["subtitle"].startswith("Okt. 2026")
