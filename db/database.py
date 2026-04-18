"""Gerenciador de banco de dados — inicialização e acesso centralizado.

Ponto único de entrada para criar conexões e aplicar schema.
"""

from __future__ import annotations

from pathlib import Path

from repositories.base import BaseRepository
from repositories.player_repo import PlayerRepository
from repositories.team_repo import TeamRepository
from repositories.match_repo import MatchRepository
from repositories.season_repo import SeasonRepository
from repositories.stats_repo import StatsRepository


DB_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = DB_DIR / "football_tactics.db"


class DatabaseManager:
    """Fachada para acesso a todos os repositórios."""

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._ensure_dir()
        self._init_schema()

    def _ensure_dir(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        base = BaseRepository(self.db_path)
        base.init_schema()
        base.commit()
        base.close()

    @property
    def players(self) -> PlayerRepository:
        return PlayerRepository(self.db_path)

    @property
    def teams(self) -> TeamRepository:
        return TeamRepository(self.db_path)

    @property
    def matches(self) -> MatchRepository:
        return MatchRepository(self.db_path)

    @property
    def seasons(self) -> SeasonRepository:
        return SeasonRepository(self.db_path)

    @property
    def stats(self) -> StatsRepository:
        return StatsRepository(self.db_path)
