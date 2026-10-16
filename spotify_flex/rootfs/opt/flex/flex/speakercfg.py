"""Per-speaker settings (name, hidden, start and maximum volume), stored in /data."""
from __future__ import annotations

import json
from pathlib import Path

from .api import SpotifyError

SPEAKERS_FILE = "/data/speakers.json"
FIELDS = ("alias", "hidden", "start_volume", "max_volume")


class SpeakerConfig:
    def __init__(self, path: str | None = None) -> None:
        self._path = Path(path or SPEAKERS_FILE)
        self._cfg: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        try:
            data = json.loads(self._path.read_text())
        except (OSError, ValueError):
            return {}
        return {str(k): self._clean(v) for k, v in data.items() if str(k).isdigit() and isinstance(v, dict)}

    @staticmethod
    def _vol(v) -> int | None:
        if v in (None, "", False):
            return None
        try:
            return max(0, min(100, int(v)))
        except (TypeError, ValueError):
            raise SpotifyError("Lautstärke muss eine Zahl von 0 bis 100 sein.", 400) from None

    @classmethod
    def _clean(cls, v: dict) -> dict:
        alias = str(v.get("alias") or "").strip()[:60]
        out = {"alias": alias or None, "hidden": bool(v.get("hidden")),
               "start_volume": cls._vol(v.get("start_volume")), "max_volume": cls._vol(v.get("max_volume"))}
        if out["start_volume"] is not None and out["max_volume"] is not None:
            out["start_volume"] = min(out["start_volume"], out["max_volume"])
        return out

    def get(self, oid: str) -> dict:
        return dict(self._cfg.get(str(oid)) or self._clean({}))

    def set(self, oid: str, values: dict) -> dict:
        oid = str(oid)
        if not oid.isdigit():
            raise SpotifyError("Ungültige Lautsprecher-ID.", 400)
        merged = {**self.get(oid), **{k: v for k, v in values.items() if k in FIELDS}}
        clean = self._clean(merged)
        if clean == self._clean({}):
            self._cfg.pop(oid, None)
        else:
            self._cfg[oid] = clean
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._cfg, ensure_ascii=False, indent=1))
        tmp.replace(self._path)
        return clean

    def apply(self, outputs: list[dict], include_hidden: bool = False) -> list[dict]:
        """OwnTone outputs → speakers with display name and settings."""
        result = []
        for o in outputs:
            cfg = self.get(o["id"])
            if cfg["hidden"] and not include_hidden:
                continue
            result.append({**o, "device_name": o["name"], "name": cfg["alias"] or o["name"], **cfg})
        return sorted(result, key=lambda s: s["name"].lower())

    def clamp(self, oid: str, volume: int | None) -> int | None:
        if volume is None:
            return None
        cap = self.get(oid)["max_volume"]
        return min(int(volume), cap) if cap is not None else int(volume)
