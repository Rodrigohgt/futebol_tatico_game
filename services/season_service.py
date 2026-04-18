"""Serviço de temporada — calendário, classificação, progressão de rodadas."""

from __future__ import annotations

import itertools
import random

from domain.enums import SeasonStatus, MatchStatus
from domain.season import Season, MatchFixture, Standing
from domain.team import TeamDomain
from repositories.season_repo import SeasonRepository
from repositories.match_repo import MatchRepository


class SeasonService:
    """Orquestra a criação e evolução de temporadas."""

    def __init__(self, season_repo: SeasonRepository, match_repo: MatchRepository):
        self._seasons = season_repo
        self._matches = match_repo

    def create_season(self, label: str, teams: list[TeamDomain]) -> Season:
        """Cria uma temporada com calendário round-robin completo."""
        season = Season(label=label, status=SeasonStatus.ACTIVE)
        season_id = self._seasons.insert(season)
        season.id = season_id

        # Gera fixtures round-robin (ida e volta)
        fixtures = self._generate_round_robin(season_id, teams)
        for f in fixtures:
            fid = self._matches.insert(f)
            f.id = fid
        season.fixtures = fixtures

        # Inicializa standings
        for team in teams:
            standing = Standing(team_id=team.id, team_name=team.name)
            self._seasons.upsert_standing(season_id, standing)
        season.standings = self._seasons.get_standings(season_id)

        self._seasons.commit()
        return season

    def update_standings_after_match(self, season_id: int,
                                     home_id: int, away_id: int,
                                     home_score: int, away_score: int):
        """Atualiza a classificação após uma partida."""
        standings = {s.team_id: s for s in self._seasons.get_standings(season_id)}

        for team_id, gf, ga in [
            (home_id, home_score, away_score),
            (away_id, away_score, home_score),
        ]:
            s = standings.get(team_id)
            if not s:
                s = Standing(team_id=team_id)

            new_s = Standing(
                team_id=s.team_id,
                team_name=s.team_name,
                played=s.played + 1,
                won=s.won + (1 if gf > ga else 0),
                drawn=s.drawn + (1 if gf == ga else 0),
                lost=s.lost + (1 if gf < ga else 0),
                goals_for=s.goals_for + gf,
                goals_against=s.goals_against + ga,
            )
            self._seasons.upsert_standing(season_id, new_s)

        self._seasons.commit()

    def check_season_end(self, season_id: int) -> bool:
        """Verifica se a temporada acabou (todas as partidas jogadas)."""
        season = self._seasons.find_by_id(season_id)
        if season and season.is_finished:
            self._seasons.finish(season_id)
            self._seasons.commit()
            return True
        return False

    def _generate_round_robin(self, season_id: int,
                               teams: list[TeamDomain]) -> list[MatchFixture]:
        """Gera um calendário round-robin de ida e volta."""
        team_ids = [t.id for t in teams]
        n = len(team_ids)

        if n % 2 != 0:
            team_ids.append(-1)  # bye
            n += 1

        fixtures = []
        match_day = 1

        # Ida
        ids = list(team_ids)
        for _ in range(n - 1):
            for i in range(n // 2):
                home = ids[i]
                away = ids[n - 1 - i]
                if home == -1 or away == -1:
                    continue
                fixtures.append(MatchFixture(
                    season_id=season_id,
                    home_id=home,
                    away_id=away,
                    match_day=match_day,
                ))
            match_day += 1
            # Rotaciona mantendo o primeiro fixo
            ids = [ids[0]] + [ids[-1]] + ids[1:-1]

        # Volta (inverte mando)
        first_half = list(fixtures)
        for f in first_half:
            fixtures.append(MatchFixture(
                season_id=season_id,
                home_id=f.away_id,
                away_id=f.home_id,
                match_day=match_day,
            ))
            match_day += 1

        return fixtures
