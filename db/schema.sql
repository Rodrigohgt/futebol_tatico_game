-- ═══════════════════════════════════════════════════════════
-- Football Tactics — Schema Principal
-- SQLite, WAL mode, foreign keys ON
-- ═══════════════════════════════════════════════════════════

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ═══ TIMES ═══
CREATE TABLE IF NOT EXISTS teams (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    short_name  TEXT    NOT NULL,
    color_hex   TEXT    NOT NULL DEFAULT '#CC3333',
    reputation  INTEGER NOT NULL DEFAULT 50,
    budget      INTEGER NOT NULL DEFAULT 0,
    formation   TEXT    NOT NULL DEFAULT '4-3-3',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ═══ JOGADORES ═══
CREATE TABLE IF NOT EXISTS players (
    id            INTEGER PRIMARY KEY,
    team_id       INTEGER REFERENCES teams(id),
    name          TEXT    NOT NULL,
    age           INTEGER NOT NULL,
    number        INTEGER NOT NULL DEFAULT 1,
    position      TEXT    NOT NULL,
    archetype     TEXT    NOT NULL DEFAULT '',
    foot          TEXT    NOT NULL DEFAULT 'right',
    status        TEXT    NOT NULL DEFAULT 'active',
    contract_end  INTEGER DEFAULT 0,
    market_value  INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS player_stats (
    player_id   INTEGER PRIMARY KEY REFERENCES players(id),
    finishing   INTEGER NOT NULL DEFAULT 50,
    passing     INTEGER NOT NULL DEFAULT 50,
    pace        INTEGER NOT NULL DEFAULT 50,
    dribbling   INTEGER NOT NULL DEFAULT 50,
    defending   INTEGER NOT NULL DEFAULT 50,
    heading     INTEGER NOT NULL DEFAULT 50,
    stamina     INTEGER NOT NULL DEFAULT 50,
    composure   INTEGER NOT NULL DEFAULT 50,
    positioning INTEGER NOT NULL DEFAULT 50,
    vision      INTEGER NOT NULL DEFAULT 50
);

CREATE TABLE IF NOT EXISTS player_traits (
    player_id  INTEGER NOT NULL REFERENCES players(id),
    trait_key  TEXT    NOT NULL,
    PRIMARY KEY (player_id, trait_key)
);

CREATE TABLE IF NOT EXISTS player_condition (
    player_id  INTEGER PRIMARY KEY REFERENCES players(id),
    fatigue    REAL    NOT NULL DEFAULT 100.0,
    morale     REAL    NOT NULL DEFAULT 70.0,
    form       REAL    NOT NULL DEFAULT 50.0,
    xp         INTEGER NOT NULL DEFAULT 0
);

-- ═══ TEMPORADAS ═══
CREATE TABLE IF NOT EXISTS seasons (
    id          INTEGER PRIMARY KEY,
    label       TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'active',
    started_at  TEXT,
    finished_at TEXT
);

-- ═══ PARTIDAS ═══
CREATE TABLE IF NOT EXISTS matches (
    id          INTEGER PRIMARY KEY,
    season_id   INTEGER NOT NULL REFERENCES seasons(id),
    home_id     INTEGER NOT NULL REFERENCES teams(id),
    away_id     INTEGER NOT NULL REFERENCES teams(id),
    home_score  INTEGER,
    away_score  INTEGER,
    status      TEXT    NOT NULL DEFAULT 'scheduled',
    match_day   INTEGER NOT NULL,
    played_at   TEXT
);

-- ═══ ESTATÍSTICAS POR PARTIDA POR JOGADOR ═══
CREATE TABLE IF NOT EXISTS match_player_stats (
    id          INTEGER PRIMARY KEY,
    match_id    INTEGER NOT NULL REFERENCES matches(id),
    player_id   INTEGER NOT NULL REFERENCES players(id),
    team_id     INTEGER NOT NULL REFERENCES teams(id),
    minutes     INTEGER NOT NULL DEFAULT 0,
    goals       INTEGER NOT NULL DEFAULT 0,
    assists     INTEGER NOT NULL DEFAULT 0,
    shots       INTEGER NOT NULL DEFAULT 0,
    passes_att  INTEGER NOT NULL DEFAULT 0,
    passes_cmp  INTEGER NOT NULL DEFAULT 0,
    tackles     INTEGER NOT NULL DEFAULT 0,
    fouls       INTEGER NOT NULL DEFAULT 0,
    saves       INTEGER NOT NULL DEFAULT 0,
    rating      REAL,
    UNIQUE(match_id, player_id)
);

-- ═══ CARTÕES ═══
CREATE TABLE IF NOT EXISTS cards (
    id         INTEGER PRIMARY KEY,
    match_id   INTEGER NOT NULL REFERENCES matches(id),
    player_id  INTEGER NOT NULL REFERENCES players(id),
    card_type  TEXT    NOT NULL,
    turn       INTEGER NOT NULL,
    reason     TEXT
);

-- ═══ LESÕES ═══
CREATE TABLE IF NOT EXISTS injuries (
    id            INTEGER PRIMARY KEY,
    player_id     INTEGER NOT NULL REFERENCES players(id),
    match_id      INTEGER REFERENCES matches(id),
    injury_type   TEXT    NOT NULL,
    severity      INTEGER NOT NULL,
    games_out     INTEGER NOT NULL DEFAULT 0,
    occurred_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    recovered_at  TEXT
);

-- ═══ EVENTOS DE PARTIDA ═══
CREATE TABLE IF NOT EXISTS match_events (
    id          INTEGER PRIMARY KEY,
    match_id    INTEGER NOT NULL REFERENCES matches(id),
    turn        INTEGER NOT NULL,
    event_type  TEXT    NOT NULL,
    actor_id    INTEGER REFERENCES players(id),
    target_id   INTEGER REFERENCES players(id),
    data_json   TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ═══ CLASSIFICAÇÃO ═══
CREATE TABLE IF NOT EXISTS standings (
    season_id  INTEGER NOT NULL REFERENCES seasons(id),
    team_id    INTEGER NOT NULL REFERENCES teams(id),
    played     INTEGER NOT NULL DEFAULT 0,
    won        INTEGER NOT NULL DEFAULT 0,
    drawn      INTEGER NOT NULL DEFAULT 0,
    lost       INTEGER NOT NULL DEFAULT 0,
    gf         INTEGER NOT NULL DEFAULT 0,
    ga         INTEGER NOT NULL DEFAULT 0,
    points     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (season_id, team_id)
);

-- ═══ ÍNDICES ═══
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_match_events_match ON match_events(match_id, turn);
CREATE INDEX IF NOT EXISTS idx_cards_player ON cards(player_id);
CREATE INDEX IF NOT EXISTS idx_injuries_player ON injuries(player_id);
CREATE INDEX IF NOT EXISTS idx_mps_match ON match_player_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season_id);
