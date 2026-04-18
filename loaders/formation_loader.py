"""Carrega formações táticas a partir de data/formations.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from domain.value_objects import FormationSlot


@dataclass(frozen=True)
class Formation:
    """Formação tática carregada do JSON."""
    key: str
    label: str
    description: str
    slots: tuple[FormationSlot, ...]


class FormationLoader:
    """Cache singleton de formações."""

    _cache: dict[str, Formation] = {}
    _DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "formations.json"

    @classmethod
    def load(cls) -> dict[str, Formation]:
        if cls._cache:
            return cls._cache
        with open(cls._DATA_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        for key, data in raw.items():
            slots = tuple(
                FormationSlot(
                    position=s["position"],
                    x_meters=s["x"],
                    y_meters=s["y"],
                )
                for s in data["slots"]
            )
            cls._cache[key] = Formation(
                key=key,
                label=data["label"],
                description=data.get("description", ""),
                slots=slots,
            )
        return cls._cache

    @classmethod
    def get(cls, key: str) -> Formation | None:
        if not cls._cache:
            cls.load()
        return cls._cache.get(key)

    @classmethod
    def all_keys(cls) -> list[str]:
        if not cls._cache:
            cls.load()
        return list(cls._cache.keys())
