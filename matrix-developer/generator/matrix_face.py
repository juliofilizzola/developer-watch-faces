"""Matrix Developer watch face generator (digital rain + terminal readout).

Run:  python3 matrix-developer/generator/matrix_face.py

Rendering notes (validated on the Wear OS 5 runtime, see docs/WFF_LIMITATIONS.md):
- Rain columns are PartText boxes one glyph wide with maxLines: the runtime wraps every glyph onto its
  own line. Gaps use NO-BREAK SPACE so they keep their cell.
- Columns shift one cell per minute through subText() offsets driven by [MINUTE]. There is no
  continuous animation: the face redraws once per minute unless seconds are enabled.
- Group tintColor multiplies: rain glyphs are drawn in a gray level (intensity) and tinted with the
  chosen hue, so hue x intensity needs no duplicated subtrees.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared/scripts"))

from wffgen.core import (  # noqa: E402
    AMPM, BATTERY, BATTERY_FRAC, CANVAS, CENTER, DATE_FORMATS, MINUTE, SECOND, STEP_FRAC, STEP_GOAL, STEPS,
    WEATHER_COND, WEATHER_OK, Run, Strings, ambient_alpha, ambient_hide, arc_ring, bool_cfg, cfg_color,
    circle_half_width, complication_slot, condition, date_options, date_run, date_tree, decl_bool, decl_color,
    decl_list, flavor, group, heart, list_cfg, temperature, text, text_bar, time_formats, time_tree,
    time_tree_no_seconds, watch_face, wrap,
)
from wffgen.module import LayoutCheck, write_module  # noqa: E402
from wffgen.xml import E  # noqa: E402

MODULE = ROOT / "matrix-developer"
TECH = "share_tech_mono"
MONO = "jetbrains_mono_regular"
MONO_LIGHT = "jetbrains_mono_light"
EM = 0.5  # Share Tech Mono advance width in em
NBSP = " "

MAIN = cfg_color("primary", 0)     # clock, values
DIM = cfg_color("primary", 1)      # labels, punctuation
HEAD = cfg_color("accent", 0)      # rain heads, highlights
TRAIL = cfg_color("intensity", 0)  # gray level, tinted by primary
GLOW = cfg_color("glow", 0)
HEART = heart('"--"')

EXT1_Y, EXT2_Y = 336, 362

s = Strings()
check = LayoutCheck(EM)

LAYOUTS = {
    "minimal": dict(clock_c=214, clock=112, date=282, rows=[]),
    "compact": dict(clock_c=196, clock=100, date=256, rows=[("battery", 294), ("steps", 322)]),
    "balanced": dict(clock_c=178, clock=92, date=232, rows=[("battery", 268), ("steps", 296), ("heart", 324)]),
    "full": dict(clock_c=146, clock=76, date=192, rows=[("battery", 222), ("steps", 248), ("heart", 274),
                                                          ("weather", 300)], ext=True),
    "info": dict(clock_c=128, clock=64, date=170, rows=[("battery", 198), ("steps", 222), ("heart", 246),
                                                          ("weather", 270), ("status", 294)], ext=True),
}
ROW_SIZE = {"minimal": 24, "compact": 23, "balanced": 22, "full": 20, "info": 19}
CLOCK_SIZES = [("s", 0.82), ("m", 1.0), ("l", 1.12), ("xl", 1.22)]

GLYPHS = {
    "binary": "01",
    "hex": "0123456789ABCDEF",
    "digits": "0123456789",
    "symbols": "+-*/=<>{}[]#$%&@|~^;:",
}
DENSITY_COLUMNS = {"low": 8, "medium": 13, "high": 19}


# --------------------------------------------------------------------------- digital rain

RAIN_SIZE = 18
RAIN_LINE = 23.4          # measured line height of an 18px wrapped column
RAIN_ROWS = 21
RAIN_LEN = 64             # cells per column loop


def column_strings(rng: random.Random, glyphs: str) -> tuple[str, str]:
    """(trail, heads) strings of RAIN_LEN cells; heads keep only the last glyph of each run."""
    cells = []
    while len(cells) < RAIN_LEN:
        gap = rng.randint(2, 9)
        run = rng.randint(4, 13)
        cells += [None] * gap
        cells += [rng.choice(glyphs) for _ in range(run)]
    cells = cells[:RAIN_LEN]
    trail = "".join(c if c else NBSP for c in cells)
    heads = "".join(c if c and (i + 1 == len(cells) or cells[i + 1] is None) else NBSP
                    for i, c in enumerate(cells))
    return trail, heads


def rain(glyph_style: str, density: str) -> object:
    n = DENSITY_COLUMNS[density]
    rng = random.Random(f"{glyph_style}-{density}")
    spacing = CANVAS / n
    cols = []
    for i in range(n):
        trail, heads = column_strings(rng, GLYPHS[glyph_style])
        speed = rng.choice((1, 1, 2))
        phase = rng.randrange(RAIN_LEN)
        # Falling one cell per minute: window start moves backwards through the doubled loop.
        off = f"({RAIN_LEN} - (([MINUTE] * {speed} + {phase}) % {RAIN_LEN})) % {RAIN_LEN}"
        x = round(i * spacing + (spacing - 14) / 2)
        y = round(CENTER - RAIN_ROWS * RAIN_LINE / 2)
        h = round(RAIN_ROWS * RAIN_LINE)
        for layer, src, color, fam in (("t", trail, TRAIL, MONO_LIGHT), ("h", heads, "#FFFFFFFF", MONO)):
            expr = f'subText("{src * 2}", {off}, {off} + {RAIN_ROWS})'
            t = text(x, y, 14, h, [Run("%s", [expr], color=color, size=RAIN_SIZE, family=fam)], align="CENTER")
            t.children[-1].attrs["maxLines"] = RAIN_ROWS + 1
            cols.append((layer, t))
    trails = group(f"rain_trail_{glyph_style}_{density}", [t for layer, t in cols if layer == "t"])
    trails.attrs["tintColor"] = MAIN
    heads = group(f"rain_heads_{glyph_style}_{density}", [t for layer, t in cols if layer == "h"])
    heads.attrs["tintColor"] = HEAD
    return wrap(trails, heads)


def rain_tree() -> object:
    return list_cfg("rain_density", {
        d: list_cfg("glyph_style", {g: rain(g, d) for g in GLYPHS}) for d in DENSITY_COLUMNS
    })


# --------------------------------------------------------------------------- panel + decorations

def panel(name: str, lay: dict) -> object:
    top = lay["clock_c"] - lay["clock"] * 0.62
    last = (EXT2_Y + 24) if lay.get("ext") else ((lay["rows"][-1][1] + 30) if lay["rows"] else lay["date"] + 34)
    bottom = last + 8
    half = min(circle_half_width(top, 20), circle_half_width(bottom, 20), 190)
    x0, x1 = CENTER - half, CENTER + half
    w, h = x1 - x0, bottom - top
    body = E("PartDraw", [E("RoundRectangle", [E("Fill", color="#C8000000")], x=0, y=0, width=round(w),
                            height=round(h), cornerRadiusX=18, cornerRadiusY=18)],
             x=round(x0), y=round(top), width=round(w), height=round(h), name=f"panel_{name}")
    arm = 22
    corners = []
    for cx, cy, dx, dy in ((x0, top, 1, 1), (x1, top, -1, 1), (x0, bottom, 1, -1), (x1, bottom, -1, -1)):
        corners.append(E("Line", [E("Stroke", color=DIM, thickness=2, cap="ROUND")],
                         startX=round(cx), startY=round(cy), endX=round(cx + dx * arm), endY=round(cy)))
        corners.append(E("Line", [E("Stroke", color=DIM, thickness=2, cap="ROUND")],
                         startX=round(cx), startY=round(cy), endX=round(cx), endY=round(cy + dy * arm)))
    brackets = E("PartDraw", corners, x=0, y=0, width=CANVAS, height=CANVAS, name=f"brackets_{name}")
    label = text(0, round(top) - 26, CANVAS, 22, [Run("DEVTIME://MATRIX", color=DIM, size=14, family=TECH,
                                                        letter_spacing=0.2)], align="CENTER")
    return wrap(body, bool_cfg("decorations", wrap(brackets, label)))


# --------------------------------------------------------------------------- readout rows

def row(y, size, runs, chars, where):
    h = round(size * 1.35)
    check.line(where, 0, y, h, chars, size, align="CENTER", box_w=CANVAS)
    return text(0, y, CANVAS, h, runs, align="CENTER", ellipsis=True)


def label(name, size):
    # One run: a space at the boundary between two runs can be dropped by the runtime.
    return [Run(f"> {name} ", color=DIM, size=size, family=TECH)]


def battery_row(y, size):
    full, empty = text_bar(BATTERY_FRAC, 10, "█", "░")
    return list_cfg("battery_style", {
        "percent": row(y, size, label("BAT", size) + [Run("%s", [BATTERY], color=MAIN, size=size, family=TECH),
                                                       Run("%", color=MAIN, size=size, family=TECH)], 10, "bat"),
        "bar": row(y, size, label("BAT", size) + [Run("%s", [full], color=MAIN, size=size, family=MONO),
                                                   Run("%s", [empty], color=DIM, size=size, family=MONO)], 16, "bat bar"),
        "ring": row(y, size, label("BAT", size) + [Run("%s", [BATTERY], color=MAIN, size=size, family=TECH),
                                                    Run("%", color=MAIN, size=size, family=TECH)], 10, "bat ring"),
        "icon": row(y, size, [Run(" ", color=MAIN, size=size, image="ic_battery", family=TECH),
                              Run("%s", [BATTERY], color=MAIN, size=size, family=TECH),
                              Run("%", color=MAIN, size=size, family=TECH)], 6, "bat icon"),
    })


def steps_row(y, size):
    full, empty = text_bar(STEP_FRAC, 10, "█", "░")
    return list_cfg("steps_style", {
        "count": row(y, size, label("STP", size) + [Run("%s", [STEPS], color=MAIN, size=size, family=TECH)],
                     11, "stp"),
        "goal": row(y, size, label("STP", size) + [Run("%s", [STEPS], color=MAIN, size=size, family=TECH),
                                                    Run("/%s", [STEP_GOAL], color=DIM, size=size, family=TECH)],
                    17, "stp goal"),
        "bar": row(y, size, label("STP", size) + [Run("%s", [full], color=MAIN, size=size, family=MONO),
                                                   Run("%s", [empty], color=DIM, size=size, family=MONO)], 16, "stp bar"),
        "ring": row(y, size, label("STP", size) + [Run("%s", [STEPS], color=MAIN, size=size, family=TECH)],
                    11, "stp ring"),
        "icon": row(y, size, [Run(" ", color=MAIN, size=size, image="ic_steps", family=TECH),
                              Run("%s", [STEPS], color=MAIN, size=size, family=TECH)], 7, "stp icon"),
    })


def heart_row(y, size):
    return list_cfg("heart_style", {
        "value": row(y, size, label("HRT", size) + [Run("%s", [HEART], color=MAIN, size=size, family=TECH),
                                                     Run(" BPM", color=DIM, size=size, family=TECH)], 12, "hrt"),
        "icon": row(y, size, [Run(" ", color=MAIN, size=size, image="ic_heart", family=TECH),
                              Run("%s", [HEART], color=MAIN, size=size, family=TECH)], 6, "hrt icon"),
        "compact": row(y, size, [Run("♥ ", color=HEAD, size=size, family=TECH),
                                 Run("%s", [HEART], color=MAIN, size=size, family=TECH)], 6, "hrt compact"),
    })


def weather_row(y, size):
    def by_unit(make):
        return list_cfg("weather_unit", {u: make(*temperature(u)) for u in ("auto", "c", "f")})

    def ok(style):
        if style == "full":
            return by_unit(lambda t, u: row(y, size, label("TMP", size) + [
                Run("%s°%s ", [t, u], color=MAIN, size=size, family=TECH),
                Run("%s", [WEATHER_COND], color=DIM, size=size, family=TECH, upper=True)], 22, "tmp full"))
        if style == "temp":
            return by_unit(lambda t, u: row(y, size, label("TMP", size) + [
                Run("%s°%s", [t, u], color=MAIN, size=size, family=TECH)], 10, "tmp"))
        if style == "icon":
            icon = E("PartText", [E("Text", [E("BitmapFont", [E("Template", ["%s", E(
                "Parameter", expression="[WEATHER.CONDITION] <= 15 ? [WEATHER.CONDITION] : 0")])],
                family="wx_icons", size=round(size * 1.1))])], x=round(CENTER - 70), y=y, width=34,
                height=round(size * 1.35))
            icon_g = group("wx_icon", [icon])
            icon_g.attrs["tintColor"] = MAIN
            return wrap(icon_g, by_unit(lambda t, u: text(round(CENTER - 34), y, 160, round(size * 1.35), [
                Run("%s°%s", [t, u], color=MAIN, size=size, family=TECH)])))
        return row(y, size, label("SKY", size) + [Run("%s", [WEATHER_COND], color=MAIN, size=size, family=TECH,
                                                      upper=True)], 18, "sky")

    no_signal = row(y, size, label("TMP", size) + [Run("NO SIGNAL", color=DIM, size=size, family=TECH)], 15, "wx none")
    return list_cfg("weather_style", {st: condition([(WEATHER_OK, ok(st))], default=no_signal)
                                      for st in ("full", "temp", "icon", "condition")})


def status_row(y, size):
    status = '[BATTERY_CHARGING_STATUS] ? "CHARGING" : ([BATTERY_IS_LOW] ? "LOW POWER" : "ONLINE")'
    return row(y, size, label("SYS", size) + [Run("%s", [status], color=MAIN, size=size, family=TECH)], 15, "sys")


ROWS = {"battery": battery_row, "steps": steps_row, "heart": heart_row, "weather": weather_row,
        "status": status_row}


# --------------------------------------------------------------------------- clock

def clock(lay: dict, factor: float, name: str):
    cy = lay["clock_c"]

    def render(hour, secs, ampm):
        max_w = 2 * circle_half_width(cy, 22)
        width_em = EM * (5 + (3 * 0.45 if secs else 0) + (3 * 0.36 if ampm else 0))
        sz = min(lay["clock"] * factor, max_w / width_em)
        runs = [Run("%s:%s", [hour, MINUTE], color=MAIN, size=sz, family=TECH, glow=GLOW)]
        if secs:
            runs.append(Run(":%s", [SECOND], color=MAIN, size=sz * 0.45, family=TECH, glow=GLOW))
        if ampm:
            runs.append(Run(" %s", [AMPM], color=DIM, size=sz * 0.36, family=TECH))
        return text(0, cy - sz * 0.62, CANVAS, sz * 1.25, runs, align="CENTER", name=f"time_{name}")

    return time_tree(render)


def date_line(lay: dict, size: float):
    return date_tree(lambda d: row(lay["date"], size, [
        Run("[ ", color=DIM, size=size, family=TECH), date_run(d, HEAD, size, TECH),
        Run(" ]", color=DIM, size=size, family=TECH)], d.sample_chars + 4, f"date {d.id}"))


def layout_body(name: str, lay: dict):
    size = ROW_SIZE[name]
    nodes = [panel(name, lay),
             list_cfg("clock_size", {sid: clock(lay, f, f"{name}_{sid}") for sid, f in CLOCK_SIZES}),
             date_line(lay, size)]
    for ind, y in lay["rows"]:
        nodes.append(ROWS[ind](y, size))
    return group(f"layout_{name}", nodes)


def rings():
    track = "#2200FF41"
    return group("rings", [
        list_cfg("battery_style", {"ring": arc_ring("battery_ring", CENTER, CENTER, 456, 220, 100,
                                                    BATTERY_FRAC, MAIN, track, 6)}),
        list_cfg("steps_style", {"ring": arc_ring("steps_ring", CENTER, CENTER, 456, 140, 100,
                                                  STEP_FRAC, HEAD, track, 6, direction="COUNTER_CLOCKWISE")}),
    ])


# --------------------------------------------------------------------------- AOD

def ambient():
    def aod_time(hour, _secs, ampm):
        sz = 96 if not ampm else 84
        runs = [Run("%s:%s", [hour, MINUTE], color=DIM, size=sz, family=TECH)]
        if ampm:
            runs.append(Run(" %s", [AMPM], color=DIM, size=sz * 0.34, family=TECH))
        return text(0, 240 - sz * 0.66, CANVAS, sz * 1.25, runs, align="CENTER")

    def date():
        return date_tree(lambda d: text(0, 300, CANVAS, 30, [date_run(d, DIM, 20, TECH)], align="CENTER"))

    def stats():
        return text(0, 334, CANVAS, 26, [Run("BAT %s", [BATTERY], color=DIM, size=17, family=TECH),
                                         Run("%  STP ", color=DIM, size=17, family=TECH),
                                         Run("%s", [STEPS], color=DIM, size=17, family=TECH)], align="CENTER")

    return group("ambient", [list_cfg("aod_mode", {
        "time": wrap(time_tree_no_seconds(aod_time)),
        "time_date": wrap(time_tree_no_seconds(aod_time), date()),
        "full": wrap(time_tree_no_seconds(aod_time), date(), stats()),
    })], alpha=0, variants=[ambient_alpha(210)])


# --------------------------------------------------------------------------- complications

def complications():
    size = 17

    def render(slot):
        def content(text_expr):
            title = f'[COMPLICATION.TITLE] != null ? [COMPLICATION.TITLE] : "{slot.upper()}"'
            t = text(0, 0, 260, 24, [Run("> %s ", [title], color=DIM, size=size, family=TECH, upper=True),
                                     Run("%s", [text_expr], color=MAIN, size=size, family=TECH)],
                     align="CENTER", ellipsis=True)
            return group(f"{slot}_content", [bool_cfg("show_ext", list_cfg("layout", {"full": t, "info": t}))],
                         w=260, h=24)
        return {"SHORT_TEXT": content("[COMPLICATION.TEXT]"), "LONG_TEXT": content("[COMPLICATION.TEXT]"),
                "RANGED_VALUE": content("[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : "
                                        "[COMPLICATION.RANGED_VALUE_VALUE]")}

    out = []
    for slot, y, label_, provider in (
            ("ext1", EXT1_Y, s("slot_ext1", "Readout 1 (e.g. calories)", "Leitura 1 (ex.: calorias)"), "SUNRISE_SUNSET"),
            ("ext2", EXT2_Y, s("slot_ext2", "Readout 2 (e.g. distance)", "Leitura 2 (ex.: distância)"),
             "UNREAD_NOTIFICATION_COUNT")):
        out.append(complication_slot(slot, label_, CENTER - 130, y, 260, 24, render(slot),
                                     default_provider=provider, default_type="SHORT_TEXT"))
    return out


def bitmap_fonts():
    chars = []
    for i in range(16):
        tag = "Character" if i < 10 else "Word"
        chars.append(E(tag, name=str(i), resource=f"wx_{i}", width=48, height=48))
    return E("BitmapFonts", [E("BitmapFont", chars, name="wx_icons")])


# --------------------------------------------------------------------------- configurations

PRIMARY = [  # (id, en, pt, main, dim)
    ("classic", "Classic green", "Verde clássico", "#FF00FF41", "#FF00A82B"),
    ("phosphor", "Phosphor", "Fósforo", "#FF33FF66", "#FF1F9E40"),
    ("emerald", "Emerald", "Esmeralda", "#FF00E68A", "#FF00995C"),
    ("lime", "Lime", "Lima", "#FFA6FF00", "#FF6E9E00"),
    ("mint", "Mint", "Menta", "#FF7DFFB0", "#FF4C9E6C"),
    ("dark_green", "Dark green", "Verde escuro", "#FF00C032", "#FF006B1C"),
    ("cyan", "Cyber cyan", "Ciano cyber", "#FF00E5FF", "#FF00899A"),
    ("amber", "Amber", "Âmbar", "#FFFFB000", "#FFA66F00"),
    ("red", "Red pill", "Vermelho", "#FFFF3B3B", "#FFA32424"),
    ("purple", "Purple", "Roxo", "#FFB388FF", "#FF7056A3"),
    ("white", "Ghost white", "Branco", "#FFF0F0F0", "#FF8A8A8A"),
]
ACCENT = [
    ("white", "White heads", "Cabeças brancas", "#FFE8FFE8"),
    ("mint", "Mint", "Menta", "#FFB6FFD0"),
    ("green", "Bright green", "Verde vivo", "#FF5BFF7A"),
    ("cyan", "Cyan", "Ciano", "#FF7DF9FF"),
    ("yellow", "Yellow", "Amarelo", "#FFFFF176"),
    ("red", "Red", "Vermelho", "#FFFF6E6E"),
]
INTENSITY = [
    ("faint", "Faint", "Discreta", "#FF2A2A2A"),
    ("low", "Low", "Baixa", "#FF454545"),
    ("medium", "Medium", "Média", "#FF707070"),
    ("high", "High", "Alta", "#FFA8A8A8"),
    ("max", "Maximum", "Máxima", "#FFFFFFFF"),
]
GLOW_OPTS = [
    ("none", "No glow", "Sem brilho", "#00000000"),
    ("soft", "Soft green glow", "Brilho verde suave", "#6600FF41"),
    ("strong", "Strong green glow", "Brilho verde forte", "#CC00FF41"),
    ("cyan", "Cyan glow", "Brilho ciano", "#9900E5FF"),
    ("amber", "Amber glow", "Brilho âmbar", "#99FFB000"),
    ("white", "White glow", "Brilho branco", "#88FFFFFF"),
]


def user_configurations():
    hidden = ("hidden", s("opt_hidden", "Hidden", "Oculto"))
    cfgs = [
        decl_list("layout", s("cfg_layout", "Layout", "Layout"), "balanced", [
            ("minimal", s("opt_layout_minimal", "Minimal: time + date", "Minimalista: hora + data")),
            ("compact", s("opt_layout_compact", "Compact", "Compacto")),
            ("balanced", s("opt_layout_balanced", "Balanced", "Equilibrado")),
            ("full", s("opt_layout_full", "Full: all data + complications", "Completo: tudo + complicações")),
            ("info", s("opt_layout_info", "Informative: dense", "Informativo: denso"))]),
        decl_list("rain_density", s("cfg_rain_density", "Rain density", "Densidade da chuva"), "medium", [
            ("off", s("opt_rain_off", "Off", "Desligada")), ("low", s("opt_rain_low", "Low", "Baixa")),
            ("medium", s("opt_rain_medium", "Medium", "Média")), ("high", s("opt_rain_high", "High", "Alta"))]),
        decl_list("glyph_style", s("cfg_glyph_style", "Characters", "Caracteres"), "binary", [
            ("binary", s("opt_glyph_binary", "Binary 0/1", "Binário 0/1")),
            ("hex", s("opt_glyph_hex", "Hexadecimal", "Hexadecimal")),
            ("digits", s("opt_glyph_digits", "Digits", "Dígitos")),
            ("symbols", s("opt_glyph_symbols", "Code symbols", "Símbolos de código"))]),
        decl_color("primary", s("cfg_primary", "Main color", "Cor principal"), "classic",
                   [(i, s(f"pri_{i}", en, pt), [m, d]) for i, en, pt, m, d in PRIMARY]),
        decl_color("accent", s("cfg_accent", "Highlight color", "Cor de destaque"), "white",
                   [(i, s(f"acc_{i}", en, pt), [c]) for i, en, pt, c in ACCENT]),
        decl_color("intensity", s("cfg_intensity", "Visual intensity", "Intensidade visual"), "medium",
                   [(i, s(f"int_{i}", en, pt), [c]) for i, en, pt, c in INTENSITY]),
        decl_color("glow", s("cfg_glow", "Clock glow", "Brilho do relógio"), "soft",
                   [(i, s(f"glow_{i}", en, pt), [c]) for i, en, pt, c in GLOW_OPTS]),
        decl_bool("decorations", s("cfg_decorations", "Decorative frame", "Moldura decorativa"), True),
        decl_list("time_format", s("cfg_time_format", "Time format", "Formato da hora"), "system", time_formats(s)),
        decl_bool("show_seconds", s("cfg_show_seconds", "Show seconds", "Mostrar segundos"), False),
        decl_list("clock_size", s("cfg_clock_size", "Clock size", "Tamanho do relógio"), "m", [
            ("s", s("opt_size_s", "Small", "Pequeno")), ("m", s("opt_size_m", "Medium", "Médio")),
            ("l", s("opt_size_l", "Large", "Grande")), ("xl", s("opt_size_xl", "Extra large", "Extra grande"))]),
        decl_list("date_format", s("cfg_date_format", "Date format", "Formato da data"), "wd_d_mmm", date_options(s)),
        decl_list("battery_style", s("cfg_battery", "Battery", "Bateria"), "percent", [
            ("percent", s("opt_bat_percent", "Percentage", "Percentual")),
            ("bar", s("opt_bat_bar", "Progress bar", "Barra de progresso")),
            ("ring", s("opt_bat_ring", "Circular ring", "Anel circular")),
            ("icon", s("opt_bat_icon", "Icon + value", "Ícone + valor")), hidden]),
        decl_list("steps_style", s("cfg_steps", "Steps", "Passos"), "count", [
            ("count", s("opt_steps_count", "Step count", "Número de passos")),
            ("goal", s("opt_steps_goal", "Steps / goal", "Passos / meta")),
            ("bar", s("opt_steps_bar", "Goal progress bar", "Barra da meta")),
            ("ring", s("opt_steps_ring", "Circular ring", "Anel circular")),
            ("icon", s("opt_steps_icon", "Icon + count", "Ícone + quantidade")), hidden]),
        decl_list("heart_style", s("cfg_heart", "Heart rate", "Frequência cardíaca"), "value", [
            ("value", s("opt_hr_value", "Numeric value", "Valor numérico")),
            ("icon", s("opt_hr_icon", "Icon + value", "Ícone + valor")),
            ("compact", s("opt_hr_compact", "Compact", "Compacto")), hidden]),
        decl_list("weather_style", s("cfg_weather", "Weather", "Clima"), "full", [
            ("full", s("opt_wx_full", "Temperature + condition", "Temperatura + condição")),
            ("temp", s("opt_wx_temp", "Temperature", "Temperatura")),
            ("icon", s("opt_wx_icon", "Condition icon + temperature", "Ícone da condição + temperatura")),
            ("condition", s("opt_wx_condition", "Condition", "Condição")), hidden]),
        decl_list("weather_unit", s("cfg_weather_unit", "Temperature unit", "Unidade de temperatura"), "auto", [
            ("auto", s("opt_unit_auto", "Device setting", "Padrão do aparelho")),
            ("c", s("opt_unit_c", "Celsius", "Celsius")), ("f", s("opt_unit_f", "Fahrenheit", "Fahrenheit"))]),
        decl_bool("show_ext", s("cfg_show_ext", "Complication readouts", "Leituras de complicações"), True),
        decl_list("aod_mode", s("cfg_aod", "Always-on display", "Tela sempre ativa"), "time_date", [
            ("time", s("opt_aod_time", "Time only", "Somente hora")),
            ("time_date", s("opt_aod_time_date", "Time + date", "Hora + data")),
            ("full", s("opt_aod_full", "Time, date, battery, steps", "Hora, data, bateria, passos"))]),
    ]
    slots = {"ext1": ("SUNRISE_SUNSET", "SHORT_TEXT"), "ext2": ("UNREAD_NOTIFICATION_COUNT", "SHORT_TEXT")}
    flavors = E("Flavors", [
        flavor("classic", s("flv_classic", "Classic Matrix", "Matrix clássico"), {
            "layout": "balanced", "rain_density": "medium", "glyph_style": "binary", "primary": "classic",
            "accent": "white", "intensity": "medium", "glow": "soft", "decorations": "TRUE"}),
        flavor("dark", s("flv_dark", "Dark Matrix", "Matrix escuro"), {
            "layout": "balanced", "rain_density": "high", "glyph_style": "hex", "primary": "dark_green",
            "accent": "green", "intensity": "faint", "glow": "none", "decorations": "FALSE"}),
        flavor("minimal", s("flv_minimal", "Minimal Matrix", "Matrix minimalista"), {
            "layout": "minimal", "rain_density": "low", "glyph_style": "binary", "primary": "classic",
            "intensity": "low", "glow": "soft", "decorations": "FALSE", "clock_size": "l"}),
        flavor("full_digital", s("flv_full", "Full Digital (Full Stats)", "Full Digital (Completo)"), {
            "layout": "info", "rain_density": "high", "glyph_style": "symbols", "primary": "phosphor",
            "accent": "mint", "intensity": "low", "glow": "strong", "battery_style": "ring",
            "steps_style": "ring", "show_ext": "TRUE", "aod_mode": "full"}, slots),
        flavor("amoled_green", s("flv_amoled", "AMOLED Green (battery saver)", "AMOLED Verde (economia)"), {
            "layout": "compact", "rain_density": "off", "primary": "classic", "glow": "none",
            "decorations": "FALSE", "show_seconds": "FALSE", "aod_mode": "time"}),
    ], defaultValue="classic")
    return cfgs + [flavors]


def build():
    s("watch_face_name", "Matrix Developer", "Matrix Developer")
    active = group("active", [
        rain_tree(),
        list_cfg("layout", {name: layout_body(name, lay) for name, lay in LAYOUTS.items()}),
        rings(),
    ], variants=[ambient_hide()])
    face = watch_face(user_configurations(), [active, ambient(), *complications()], bitmap_fonts=bitmap_fonts(),
                      metadata={"CLOCK_TYPE": "DIGITAL", "PREVIEW_TIME": "14:35:42"})
    write_module(MODULE, face, s, "matrix-developer/generator/matrix_face.py",
                 "Matrix Developer - DevTime Watch Faces. GENERATED FILE: edit matrix-developer/generator/matrix_face.py")
    if check.problems:
        print("layout warnings:")
        for p in sorted(set(check.problems)):
            print("  " + p)
    print(f"wrote {MODULE / 'src/main/res/raw/watchface.xml'}")


if __name__ == "__main__":
    build()
