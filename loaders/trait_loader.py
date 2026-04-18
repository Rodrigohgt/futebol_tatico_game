"""Carrega traits de jogadores a partir de data/traits.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Trait:
    """Trait de jogador carregada do JSON."""
    key: str
    label: str
    description: str
    stat_bonuses: dict[str, int]
    context_bonuses: dict[str, int]


class TraitLoader:
    """Cache singleton de traits."""

    _cache: dict[str, Trait] = {}
    _DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "traits.json"

    @classmethod
    def load(cls) -> dict[str, Trait]:
        if cls._cache:
            return cls._cache
        with open(cls._DATA_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        for key, data in raw.items():
            cls._cache[key] = Trait(
                key=key,
                label=data["label"],
                description=data.get("description", ""),
                stat_bonuses=data.get("stat_bonuses", {}),
                context_bonuses=data.get("context_bonuses", {}),
            )
        return cls._cache

    @classmethod
    def get(cls, key: str) -> Trait | None:
        if not cls._cache:
            cls.load()
        return cls._cache.get(key)

    @classmethod
    def stat_bonus_for(cls, trait_keys: list[str], stat: str) -> int:
        """Soma o bônus de stat de múltiplas traits."""
        if not cls._cache:
            cls.load()
        total = 0
        for key in trait_keys:
            trait = cls._cache.get(key)
            if trait:
                total += trait.stat_bonuses.get(stat, 0)
        return total

    @classmethod
    def context_bonus_for(cls, trait_keys: list[str], context: str) -> int:
        """Soma o bônus contextual de múltiplas traits."""
        if not cls._cache:
            cls.load()
        total = 0
        for key in trait_keys:
            trait = cls._cache.get(key)
            if trait:
                total += trait.context_bonuses.get(context, 0)
        return total
