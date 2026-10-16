import json

import pytest

from flex.eq import BANDS, PRESETS, EqError, Equalizer


def make(tmp_path):
    return Equalizer(str(tmp_path / "eq.json"), str(tmp_path / "run" / "eq.conf"))


def test_presets_valid():
    ids = [p[0] for p in PRESETS]
    assert len(ids) == len(set(ids)) and ids[0] == "flat"
    for _pid, _name, gains in PRESETS:
        assert len(gains) == len(BANDS) and all(-12 <= g <= 12 for g in gains)


def test_default_off(tmp_path):
    v = make(tmp_path).view()
    assert v["enabled"] is False and v["preset"] == "flat" and v["gains"] == [0] * 6
    assert v["bands"] == [60, 150, 400, 1000, 2400, 15000] and len(v["presets"]) == len(PRESETS)


def test_preset_and_custom(tmp_path):
    eq = make(tmp_path)
    v = eq.update({"preset": "bass_boost"})
    assert v["enabled"] and v["gains"] == [6, 4, 1, 0, 0, 0]
    assert (tmp_path / "run" / "eq.conf").read_text() == "1 6.00 4.00 1.00 0.00 0.00 0.00\n"
    v = eq.update({"gains": [6, 4, 1, 0, 0, 20]})  # clamped, no preset any more
    assert v["preset"] == "custom" and v["gains"][-1] == 12
    v = eq.update({"gains": [0, 0, 0, 1, 3, 6]})  # matches a preset again
    assert v["preset"] == "treble_boost"
    v = eq.update({"enabled": False})
    assert (tmp_path / "run" / "eq.conf").read_text().startswith("0 ")
    # persisted
    again = make(tmp_path).view()
    assert again["enabled"] is False and again["gains"] == [0, 0, 0, 1, 3, 6]
    assert json.loads((tmp_path / "eq.json").read_text())["preset"] == "treble_boost"


@pytest.mark.parametrize("bad", [{"preset": "metal"}, {"gains": [1, 2]}, {"gains": [1, 2, 3, 4, 5, "x"]},
                                 {"enabled": "yes"}])
def test_invalid(tmp_path, bad):
    with pytest.raises(EqError):
        make(tmp_path).update(bad)
