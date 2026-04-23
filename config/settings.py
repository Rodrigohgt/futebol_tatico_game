"""Configurações globais do jogo.

Este arquivo contém APENAS constantes visuais / de display e parâmetros
de gameplay que ainda não migraram para data/match_params.json.
Os valores de gameplay marcados com [→ JSON] serão migrados futuramente.
"""

# ═══════════════════════════════════════════════════════════
#  DISPLAY
# ═══════════════════════════════════════════════════════════
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 790
WINDOW_TITLE = "Football Tactics"
FPS = 60

# ═══════════════════════════════════════════════════════════
#  LAYOUT — campo e HUD
# ═══════════════════════════════════════════════════════════
MARGIN_X = 80
MARGIN_Y = 50
HUD_BOTTOM_HEIGHT = 70

# ═══════════════════════════════════════════════════════════
#  CORES — campo
# ═══════════════════════════════════════════════════════════
GRASS_DARK = (50, 138, 50)
GRASS_LIGHT = (58, 140, 58)
GRASS_STRIPE_COUNT = 12
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOAL_POST_COLOR = (220, 220, 220)
GOAL_NET_COLOR = (200, 200, 200)

# ═══════════════════════════════════════════════════════════
#  CORES — HUD / botões
# ═══════════════════════════════════════════════════════════
HUD_BG = (18, 18, 28)
HUD_BORDER_COLOR = (60, 65, 80)
HUD_BORDER_WIDTH = 2

BUTTON_IDLE = (40, 40, 40)
BUTTON_HOVER = (60, 60, 60)
BUTTON_ACTIVE = (70, 130, 180)
BUTTON_TEXT = (255, 255, 255)
BUTTON_BORDER = (255, 255, 255)

BTN_FINISH_COLOR = (180, 50, 50)
BTN_FINISH_HOVER = (210, 70, 70)
BTN_PASS_BALL_COLOR = (50, 140, 80)
BTN_PASS_BALL_HOVER = (70, 170, 100)
BTN_PASS_BALL_ACTIVE = (30, 200, 80)
BTN_PASS_BALL_ACTIVE_HOVER = (50, 230, 100)
BTN_END_TURN_COLOR = (70, 130, 180)
BTN_END_TURN_HOVER = (90, 155, 210)
BTN_RESET_COLOR = (140, 60, 140)
BTN_RESET_HOVER = (170, 80, 170)

TURN_LABEL_COLOR = (255, 255, 255)
TURN_COUNTER_BG = (20, 20, 30, 200)

# ═══════════════════════════════════════════════════════════
#  CORES — seleção e indicadores
# ═══════════════════════════════════════════════════════════
SELECTION_COLOR = (255, 220, 50)
SELECTION_GLOW = (255, 255, 100, 80)
MOVED_INDICATOR_COLOR = (180, 180, 180, 120)

DIRECTION_ARROW_DISTANCE = 20
DIRECTION_ARROW_LENGTH = 10
DIRECTION_ARROW_HALF_BASE = 5
DIRECTION_ARROW_ALPHA = 200

PASS_PREVIEW_COLOR = (255, 255, 100, 200)

# ═══════════════════════════════════════════════════════════
#  CORES — popup / tooltip
# ═══════════════════════════════════════════════════════════
POPUP_BG = (20, 20, 30, 230)
POPUP_BORDER = (100, 140, 200)
POPUP_TEXT = (230, 230, 240)
POPUP_HEADER = (255, 255, 255)
POPUP_STAT_BAR_BG = (50, 50, 60)
POPUP_STAT_BAR_FILL = (80, 160, 220)
POPUP_HOVER_DELAY = 0.8

# ═══════════════════════════════════════════════════════════
#  CORES — times
# ═══════════════════════════════════════════════════════════
HOME_TEAM_COLOR = (180, 40, 50)
RIVAL_TEAM_COLOR = (40, 80, 180)

# ═══════════════════════════════════════════════════════════
#  VISUAL — jogador e bola (tamanhos em pixels)
# ═══════════════════════════════════════════════════════════
PLAYER_SPEED = 4.5
PLAYER_RADIUS = 14
PLAYER_BOUNDARY_PADDING = 4

BALL_RADIUS = 6
BALL_COLOR = (245, 245, 245)
BALL_BORDER_COLOR = (80, 80, 80)
BALL_DETAIL_COLOR = (140, 140, 140)

POWER_BAR_WIDTH = 22
POWER_BAR_HEIGHT = 140

# ═══════════════════════════════════════════════════════════
#  GAMEPLAY — parâmetros em runtime  [→ JSON: match_params]
# ═══════════════════════════════════════════════════════════
MAX_MOVE_METERS = 15.0

# ── Movimento por turno (estilo D&D — em metros) ──
BASE_MOVE_METERS = 5.0            # metros base de movimento por turno
PACE_METER_BONUS = 0.06           # metros extras por ponto de pace (pace 80 → +4.8m → ~9.8m total)
MOVE_EXHAUSTED_THRESHOLD = 0.3    # abaixo disso (metros) o jogador é considerado esgotado

BALL_FRICTION = 0.96
BALL_MIN_SPEED = 0.3
BALL_CARRY_OFFSET = 18
BALL_PICKUP_RADIUS = 22

BALL_PASS_SUCCESS_RATE = 0.80
BALL_PASS_ERROR_MAX = 0.35
BALL_FREE_PASSES_PER_TURN = 2
MOVES_PER_TURN = 2

PASS_CHARGE_SPEED = 0.012
PASS_MIN_SPEED = 3.0
PASS_MAX_SPEED = 12.0

# ═══════════════════════════════════════════════════════════
#  IA — budget e goleiro  [→ JSON: match_params]
# ═══════════════════════════════════════════════════════════
AI_MOVES_PER_TURN = 11
AI_PASSES_PER_TURN = 2

GK_ZONE_DEPTH = 14.0
GK_ZONE_WIDTH = 20.0
GK_ADVANCE_FACTOR = 0.85

# ═══════════════════════════════════════════════════════════
#  INTERCEPTAÇÃO — passes podem ser cortados em trânsito
# ═══════════════════════════════════════════════════════════
INTERCEPT_RADIUS = 25              # px — raio de detecção ao redor da bola
INTERCEPT_BASE_CHANCE = 0.25       # chance base de interceptar
INTERCEPT_DEFENDING_BONUS = 0.004  # bônus por ponto de defending (def 80 → +0.32 → ~57%)
INTERCEPT_MAX_CHANCE = 0.60        # teto de chance
INTERCEPT_COOLDOWN_FRAMES = 10     # frames de cooldown por jogador após falhar

# ═══════════════════════════════════════════════════════════
#  TACKLE — disputa física ao se aproximar do portador
# ═══════════════════════════════════════════════════════════
TACKLE_RADIUS = 22                 # px — distância para trigger de tackle
TACKLE_BASE_CHANCE = 0.20          # chance base
TACKLE_DEFENDING_BONUS = 0.005     # bônus por ponto de defending
TACKLE_DRIBBLING_PENALTY = 0.004   # penalidade por ponto de dribbling do portador
TACKLE_MAX_CHANCE = 0.55           # teto
TACKLE_FOUL_CHANCE = 0.15          # chance de falta ao falhar

# ═══════════════════════════════════════════════════════════
#  CONTRA-ATAQUE — ações imediatas da IA ao recuperar bola
# ═══════════════════════════════════════════════════════════
COUNTER_ATTACK_BUDGET = 2          # ações imediatas da IA ao roubar bola

# ═══════════════════════════════════════════════════════════
#  IA ANIMADA — delay entre ações para visibilidade
# ═══════════════════════════════════════════════════════════
AI_ACTION_DELAY_MS = 250           # ms entre cada ação da IA na fase de turno
AI_FAST_FORWARD_DELAY_MS = 50      # ms quando fast-forward está ativo

# ═══════════════════════════════════════════════════════════
#  PRESSING CONTEXTUAL — reações múltiplas em zona perigosa
# ═══════════════════════════════════════════════════════════
PRESSING_BOX_REACTIONS = 3         # rivais que reagem quando humano entra na área
PRESSING_HALF_ADVANCE_REACTIONS = 2  # zagueiros que recuam ao avançar com bola

# ═══════════════════════════════════════════════════════════
#  ÁRBITRO — influência na marcação de faltas e cartões
# ═══════════════════════════════════════════════════════════
REFEREE_DEFAULT_TIER = None        # None = aleatório entre tiers
REFEREE_YELLOW_TO_RED = 2          # amarelos para expulsão (segundo amarelo)
REFEREE_FOUL_STOP_FRAMES = 30     # frames que o jogo "congela" após falta marcada
REFEREE_CARD_STOP_FRAMES = 60     # frames que o jogo "congela" após cartão

# ═══════════════════════════════════════════════════════════
#  CAMPO DE VISÃO (FOV) — influência nos passes
# ═══════════════════════════════════════════════════════════
FOV_MIN_DEGREES = 90               # FOV mínimo possível (graus)
FOV_MAX_DEGREES = 120              # FOV máximo possível (graus)
FOV_DEFAULT_DEGREES = 100          # FOV base se não calculado por stats
FOV_VISION_BONUS_PER_POINT = 0.3   # graus extras por ponto de vision acima de 50
FOV_PASS_PENALTY_OUTSIDE = 0.20    # penalidade extra de accuracy fora do FOV (caso force passe)
