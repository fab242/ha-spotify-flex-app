import asyncio
import json

import pytest

from flex import appopts

CFG = """log_level: info
log_disable_timestamp: true
device_name: "Home Flex"
device_type: speaker
bitrate: 320
audio_backend: pipe
normalisation_disabled: false
zeroconf_enabled: false
server:
  enabled: true
  port: 3678
"""


def test_validate():
    assert appopts.validate({"device_name": "  Wohn   zimmer ", "bitrate": "160", "normalisation": False}) == {
        "device_name": "Wohn zimmer", "bitrate": 160, "normalisation": False}
    for bad in ({"device_name": " "}, {"device_name": 'a"b'}, {"device_name": "x" * 61},
                {"bitrate": 128}, {"bitrate": "viel"}, {"normalisation": "ja"}):
        with pytest.raises(appopts.OptionsError):
            appopts.validate(bad)
    assert appopts.validate({"zeroconf": True, "client_id": "x"}) == {}  # not editable here


def test_render_librespot_keeps_other_keys():
    out = appopts.render_librespot(CFG, {"device_name": "Küche", "bitrate": 96, "normalisation": False})
    assert 'device_name: "Küche"' in out
    assert "\nbitrate: 96\n" in out
    assert "normalisation_disabled: true" in out
    assert "device_type: speaker" in out and "  port: 3678" in out and "zeroconf_enabled: false" in out
    assert out.count("bitrate:") == 1


def test_apply(tmp_path, monkeypatch):
    opts = tmp_path / "options.json"
    cfg = tmp_path / "config.yml"
    cfg.write_text(CFG)
    monkeypatch.setattr(appopts, "OPTIONS_FILE", str(opts))
    monkeypatch.setattr(appopts, "LIBRESPOT_CONFIG", str(cfg))
    pushed, restarts = [], []

    async def push(_session, options):
        pushed.append(options)

    async def restart():
        restarts.append(1)
        return True

    monkeypatch.setattr(appopts, "push_supervisor", push)
    monkeypatch.setattr(appopts, "restart_receiver", restart)
    current = {"device_name": "Home Flex", "bitrate": 320, "normalisation": True, "zeroconf": False,
               "client_id": "", "log_level": "info", "ha_integration": True}

    # unchanged value: nothing is written, receiver keeps running
    new, restarted = asyncio.run(appopts.apply(None, current, {"bitrate": 320}))
    assert new == current and not restarted and not pushed and not restarts

    new, restarted = asyncio.run(appopts.apply(None, current, {"bitrate": 160, "device_name": "Küche"}))
    assert restarted and restarts == [1]
    assert pushed == [{**current, "bitrate": 160, "device_name": "Küche"}]  # full option set
    assert json.loads(opts.read_text())["device_name"] == "Küche"
    assert "\nbitrate: 160\n" in cfg.read_text() and 'device_name: "Küche"' in cfg.read_text()
    assert new["zeroconf"] is False and new["ha_integration"] is True


def test_apply_refused_by_supervisor(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yml"
    cfg.write_text(CFG)
    monkeypatch.setattr(appopts, "LIBRESPOT_CONFIG", str(cfg))
    monkeypatch.setattr(appopts, "OPTIONS_FILE", str(tmp_path / "options.json"))

    async def push(_session, _options):
        raise appopts.OptionsError("abgelehnt")

    monkeypatch.setattr(appopts, "push_supervisor", push)
    with pytest.raises(appopts.OptionsError):
        asyncio.run(appopts.apply(None, {"bitrate": 320}, {"bitrate": 96}))
    assert cfg.read_text() == CFG  # nothing changed locally
