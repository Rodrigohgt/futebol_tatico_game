"""Modelo de domínio da temporada e calendário."""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.enums import SeasonStatus, MatchStatus


@dataclass
class MatchFixture:
    """Partida agendada no calendário."""
    id: int = 0
    season_id: int = 0
    home_id: int = 0
    away_id: int = 0
    match_day: int = 0
    home_score: int | None = None
    away_score: int | None = None
    status: MatchStatus = MatchStatus.SCHEDULED

    @property
    def is_played(self) -> bool:
        return self.status == MatchStatus.FINISHED

    @property
    def result_str(self) -> str:
        if not self.is_played:
            return "vs"
        return f"{self.home_score} - {self.away_score}"


@dataclass
class Standing:
    """Linha de classificação de um time."""
    team_id: int
    team_name: str = ""
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def points(self) -> int:
        return self.won * 3 + self.drawn

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


@dataclass
class Season:
    """Modelo completo de uma temporada."""
    id: int = 0
    label: str = ""
    status: SeasonStatus = SeasonStatus.ACTIVE
    fixtures: list[MatchFixture] = field(default_factory=list)
    standings: list[Standing] = field(default_factory=list)

    @property
    def current_match_day(self) -> int:
        played = [f for f in self.fixtures if f.is_played]
        if not played:
            return 1
        return max(f.match_day for f in played) + 1

    @property
    def is_finished(self) -> bool:
        return all(f.is_played for f in self.fixtures)

    def next_fixture(self, team_id: int) -> MatchFixture | None:
        upcoming = [
            f for f in self.fixtures
            if not f.is_played and (f.home_id == team_id or f.away_id == team_id)
        ]
        if not upcoming:
            return None
        return min(upcoming, key=lambda f: f.match_day)

    def sorted_standings(self) -> list[Standing]:
        return sorted(
            self.standings,
            key=lambda s: (s.points, s.goal_difference, s.goals_for),
            reverse=True,
        )
