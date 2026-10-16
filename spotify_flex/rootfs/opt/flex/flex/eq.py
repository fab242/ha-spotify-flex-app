"""Equalizer settings: presets like the Spotify app, stored in /data/eq.json.

The audio itself is filtered by /usr/bin/flex-eq (see eq/flexeq.c), which watches the
control file EQ_CONTROL and fades new settings in live - no restart, no interruption.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .const import EQ_CONTROL, EQ_FILE

_LOGGER = logging.getLogger("flex.eq")

BANDS = (60, 150, 400, 1000, 2400, 15000)
GAIN_MAX = 12.0

# (id, name, gains in dB for 60 Hz, 150 Hz, 400 Hz, 1 kHz, 2.4 kHz, 15 kHz)
PRESETS: tuple[tuple[str, str, tuple[float, ...]], ...] = (
    ("flat", "Flach", (0, 0, 0, 0, 0, 0)),
    ("acoustic", "Akustik", (3, 2.5, 0.5, 1, 2, 2.5)),
    ("bass_boost", "Bass-Booster", (6, 4, 1, 0, 0, 0)),
    ("bass_cut", "Bass-Reduzierer", (-6, -4, -1, 0, 0, 0)),
    ("classical", "Klassik", (3, 2, -1, 0, 2, 3.5)),
    ("dance", "Dance", (5, 3, 0, -1, 2, 3)),
    ("deep", "Deep", (4.5, 2.5, 1, -1, -2.5, -4)),
    ("electronic", "Elektronisch", (4.5, 3, -1, 1, 2.5, 4.5)),
    ("hiphop", "Hip-Hop", (5, 3.5, 0, 1, -0.5, 2)),
    ("jazz", "Jazz", (3.5, 2, 0.5, -1.5, 1, 3.5)),
    ("latin", "Latin", (3, 0.5, -1, -1, 1, 4.5)),
    ("loudness", "Loudness", (6, 3, -1, -1.5, 1, 4)),
    ("lounge", "Lounge", (-2, 0.5, 2, 1.5, 0, 1)),
    ("piano", "Klavier", (2.5, 1, 0, 2, 3, 2)),
    ("pop", "Pop", (-1, 1, 3.5, 3, 1, -1)),
    ("rnb", "R&B", (5, 4, -1.5, -0.5, 2, 3)),
    ("rock", "Rock", (4.5, 3, -1, -0.5, 2, 4)),
    ("small_speakers", "Kleine Lautsprecher", (5, 4, 2, 0, -1, -3)),
    ("spoken", "Gesprochenes Wort", (-4, -2, 1, 3, 3.5, 0)),
    ("treble_boost", "Höhen-Booster", (0, 0, 0, 1, 3, 6)),
    ("treble_cut", "Höhen-Reduzierer", (0, 0, 0, -1, -3, -6)),
    ("vocal", "Gesangs-Booster", (-2, -2, 1.5, 3.5, 3, 0)),
)
PRESET_GAINS = {pid: list(map(float, g)) for pid, _n, g in PRESETS}
CUSTOM = "custom"


class EqError(ValueError):
    """Invalid equalizer setting."""


def _gains(value) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != len(BANDS):
        raise EqError(f"Es werden {len(BANDS)} Werte erwartet.")
    out = []
    for v in value:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise EqError("Ungültiger Equalizer-Wert.")
        out.append(round(max(-GAIN_MAX, min(GAIN_MAX, float(v))), 1))
    return out


class Equalizer:
    def __init__(self, path: str = EQ_FILE, control: str = EQ_CONTROL) -> None:
        self.path = Path(path)
        self.control = Path(control)
        self.data = {"enabled": False, "preset": "flat", "gains": PRESET_GAINS["flat"][:]}
        try:
            raw = json.loads(self.path.read_text())
            self.data = {"enabled": bool(raw.get("enabled")),
                         "preset": raw.get("preset") if raw.get("preset") in PRESET_GAINS else CUSTOM,
                         "gains": _gains(raw.get("gains"))}
        except (OSError, ValueError, EqError):
            pass

    def view(self) -> dict:
        return {**self.data, "bands": list(BANDS), "max": GAIN_MAX,
                "presets": [{"id": pid, "name": name, "gains": list(map(float, g))} for pid, name, g in PRESETS]}

    def update(self, changes: dict) -> dict:
        data = dict(self.data)
        if "preset" in changes:
            pid = changes["preset"]
            if pid not in PRESET_GAINS:
                raise EqError("Unbekannte Voreinstellung.")
            data["preset"], data["gains"] = pid, PRESET_GAINS[pid][:]
            data["enabled"] = True
        if "gains" in changes:
            data["gains"] = _gains(changes["gains"])
            data["preset"] = next((pid for pid, g in PRESET_GAINS.items() if g == data["gains"]), CUSTOM)
        if "enabled" in changes:
            if not isinstance(changes["enabled"], bool):
                raise EqError("Equalizer muss an oder aus sein.")
            data["enabled"] = changes["enabled"]
        self.data = data
        self.save()
        return self.view()

    def control_line(self) -> str:
        return f'{1 if self.data["enabled"] else 0} ' + " ".join(f"{g:.2f}" for g in self.data["gains"]) + "\n"

    def save(self) -> None:
        for path, text in ((self.path, json.dumps(self.data)), (self.control, self.control_line())):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_name(path.name + ".tmp")
                tmp.write_text(text)
                os.replace(tmp, path)  # atomic: flex-eq never reads half a line
            except OSError as err:
                _LOGGER.warning("could not write %s: %s", path, err)
