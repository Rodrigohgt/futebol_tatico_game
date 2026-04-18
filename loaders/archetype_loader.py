"""Carrega arquétipos de jogador a partir de data/archetypes.json."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Archetype:
    """Arquétipo de jogador carregado do JSON."""
    key: str
    label: str
    description: str
    allowed_positions: tuple[str, ...]
    base_stats: dict[str, int]
    trait_affinity: tuple[str, ...]


class ArchetypeLoader:
    """Cache singleton de arquétipos."""

    _cache: dict[str, Archetype] = {}
    _DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "archetypes.json"

    @classmethod
    def load(cls) -> dict[str, Archetype]:
        if cls._cache:
            return cls._cache
        with open(cls._DATA_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        for key, data in raw.items():
            cls._cache[key] = Archetype(
                key=key,
                label=data["label"],
                description=data.get("description", ""),
                allowed_positions=tuple(data["allowed_positions"]),
                base_stats=data["base_stats"],
                trait_affinity=tuple(data.get("trait_affinity", [])),
            )
        return cls._cache

    @classmethod
    def get(cls, key: str) -> Archetype | None:
        if not cls._cache:
            cls.load()
        return cls._cache.get(key)

    @classmethod
    def all_keys(cls) -> list[str]:
        if not cls._cache:
            cls.load()
        return list(cls._cache.keys())

    @classmethod
    def for_position(cls, position: str) -> list[Archetype]:
        if not cls._cache:
            cls.load()
        return [a for a in cls._cache.values() if position in a.allowed_positions]
