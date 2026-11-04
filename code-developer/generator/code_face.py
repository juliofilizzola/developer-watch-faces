"""Code Developer watch face generator (Go / JavaScript editor style).

Run:  python3 code-developer/generator/code_face.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared/scripts"))

from wffgen.core import (  # noqa: E402
    AMPM, BATTERY, BATTERY_FRAC, CANVAS, CENTER, DATE_FORMATS, MINUTE, SECOND, STEP_FRAC, STEP_GOAL, STEPS,
    WEATHER_COND, WEATHER_OK, Run, Strings, ambient_alpha, ambient_hide, arc_ring, background, bool_cfg,
    cfg_color, circle_half_width, complication_slot, condition, date_options, date_run, date_tree, decl_bool,
    decl_color, decl_list, flavor, group, heart, list_cfg, rect, temperature, text, text_bar, time_formats,
    time_tree, time_tree_no_seconds, watch_face, wrap,
)
from wffgen.module import LayoutCheck, write_module  # noqa: E402
from wffgen.palettes import ACCENTS, BACKGROUNDS, PALETTES  # noqa: E402
from wffgen.xml import E  # noqa: E402

MODULE = ROOT / "code-developer"
REG, BOLD, LIGHT = "jetbrains_mono_regular", "jetbrains_mono_bold", "jetbrains_mono_light"
EM = 0.6

# syntax palette indexes (a ColorOption holds at most 5 colors)
KW, IDENT, STR, NUM, PUNCT = (cfg_color("syntax", i) for i in range(5))
COMMENT = PUNCT
FUNC = KW
CLOCK = cfg_color("clock_color")
HEART = heart('"--"')
STATUS = '[BATTERY_CHARGING_STATUS] ? "charging" : ([BATTERY_IS_LOW] ? "low_power" : "coding")'

X_CODE = 104          # first column of code (after the gutter)
INDENT = 2            # spaces
KEY_COLS = 9          # gofmt / eslint(key-spacing: align value) value column: "Battery: "
X_GUTTER_RIGHT = 92
HERO_INLINE_X = 148   # dense layouts: hero starts right after the "Time:" key
EXT1_Y, EXT2_Y = 316, 343

s = Strings()
check = LayoutCheck(EM)

# hero time: center y and base font size per layout (independent of language and text size)
LAYOUTS = {
    "minimal": dict(hero_c=224, hero=94, rows=["date"], key_line=True),
    "compact": dict(hero_c=196, hero=84, rows=["date", "battery", "steps"], key_line=True),
    "balanced": dict(hero_c=166, hero=74, rows=["date", "battery", "steps", "heart", "status"], key_line=True),
    "full": dict(hero_c=132, hero=58, rows=["date", "battery", "steps", "heart", "weather"], key_line=False,
                 ext=True),
    "info": dict(hero_c=124, hero=50, rows=["date", "battery", "steps", "heart", "weather", "status"],
                 key_line=False, ext=True),
}
# (font size, line step) per text size; dense layouts use their own smaller set
TEXT_SIZES = {"s": (18, 23), "m": (20, 27), "l": (22, 31)}
DENSE_TEXT_SIZES = {"s": (15, 21), "m": (16, 23), "l": (17, 24)}
CLOCK_SIZES = [("s", 0.82), ("m", 1.0), ("l", 1.12), ("xl", 1.24)]

# Row keys per language. Go renders a gofmt-aligned struct literal (dev := Dev{ Battery: 85, }),
# JavaScript an object literal (const dev = { battery: 85, };). Keys have the same length in both
# languages, so the value column (and every value variant) is shared and only keys differ.
KEYS = {
    "go": {"time": "Time:", "date": "Date:", "battery": "Battery:", "steps": "Steps:", "heart": "BPM:",
           "weather": "Weather:", "status": "Status:"},
    "js": {"time": "time:", "date": "date:", "battery": "battery:", "steps": "steps:", "heart": "bpm:",
           "weather": "weather:", "status": "status:"},
}
HEADER = {"go": [("dev", "IDENT"), (" := ", "PUNCT"), ("Dev", "KW"), ("{", "PUNCT")],
          "js": [("const ", "KW"), ("dev", "IDENT"), (" = {", "PUNCT")]}
CLOSE = {"go": "}", "js": "};"}
NIL = {"go": "nil", "js": "null"}


def tok(color_name: str) -> str:
    return {"IDENT": IDENT, "PUNCT": PUNCT, "KW": KW}[color_name]


# --------------------------------------------------------------------------- geometry

def row_box(y, size, x):
    h = round(size * 1.35)
    half = min(circle_half_width(y + h * 0.2, 12), circle_half_width(y + h * 0.8, 12))
    return x, y, max(40, round(CENTER + half - x)), h


def line(y, size, runs, chars, where, x):
    bx, by, bw, bh = row_box(y, size, x)
    check.line(where, bx, by, bh, chars, size)
    return text(bx, by, bw, bh, runs, ellipsis=True)


def geometry(lay: dict, ts: str):
    """Returns (header_y, key_y, rows_y[], close_y, size, step)."""
    size, step = (DENSE_TEXT_SIZES if lay.get("ext") else TEXT_SIZES)[ts]
    hero_c, hero = lay["hero_c"], lay["hero"]
    hero_top = hero_c - hero * 0.62
    hero_bottom = hero_c + hero * 0.50
    if lay["key_line"]:
        key_y = hero_top - step + 4
        header_y = key_y - step
    else:
        key_y = None
        header_y = hero_top - step + 2
    rows_y = [hero_bottom + 6 + i * step for i in range(len(lay["rows"]))]
    close_y = EXT2_Y + 27 if lay.get("ext") else (rows_y[-1] + step if rows_y else hero_bottom + 6)
    return header_y, key_y, rows_y, close_y, size, step


def x_key(size):
    return X_CODE + INDENT * size * EM


def x_val(size):
    return x_key(size) + KEY_COLS * size * EM


# --------------------------------------------------------------------------- value cells (language independent)

def c(size):
    return Run(",", color=PUNCT, size=size)


def val(y, size, runs, chars, where):
    return line(y, size, runs, chars, where, x_val(size))


def date_val(y, size):
    return date_tree(lambda d: val(y, size, [date_run(d, STR, size, before='"', after='"'), c(size)],
                                   d.sample_chars + 3, f"date {d.id}"))


def battery_val(y, size):
    full, empty = text_bar(BATTERY_FRAC, 8, "█", "░")
    return list_cfg("battery_style", {
        "percent": val(y, size, [Run("%s", [BATTERY], color=NUM, size=size), c(size),
                                 Run(" // %", color=COMMENT, size=size)], 9, "battery"),
        "bar": val(y, size, [Run('"', color=STR, size=size), Run("%s", [full], color=NUM, size=size),
                             Run("%s", [empty], color=COMMENT, size=size), Run('"', color=STR, size=size), c(size)],
                   11, "battery bar"),
        "ring": val(y, size, [Run("%s", [BATTERY], color=NUM, size=size), c(size)], 4, "battery ring"),
        "icon": val(y, size, [Run(" ", color=NUM, size=size, image="ic_battery"),
                              Run("%s", [BATTERY], color=NUM, size=size), c(size)], 6, "battery icon"),
    })


def steps_val(y, size):
    full, empty = text_bar(STEP_FRAC, 8, "█", "░")
    return list_cfg("steps_style", {
        "count": val(y, size, [Run("%s", [STEPS], color=NUM, size=size), c(size)], 6, "steps"),
        "goal": val(y, size, [Run("%s", [STEPS], color=NUM, size=size), c(size),
                              Run(" // /%s", [STEP_GOAL], color=COMMENT, size=size)], 15, "steps goal"),
        "bar": val(y, size, [Run('"', color=STR, size=size), Run("%s", [full], color=NUM, size=size),
                             Run("%s", [empty], color=COMMENT, size=size), Run('"', color=STR, size=size), c(size)],
                   11, "steps bar"),
        "ring": val(y, size, [Run("%s", [STEPS], color=NUM, size=size), c(size)], 6, "steps ring"),
        "icon": val(y, size, [Run(" ", color=NUM, size=size, image="ic_steps"),
                              Run("%s", [STEPS], color=NUM, size=size), c(size)], 8, "steps icon"),
    })


def heart_val(y, size):
    return list_cfg("heart_style", {
        "value": val(y, size, [Run("%s", [HEART], color=NUM, size=size), c(size)], 4, "heart"),
        "icon": val(y, size, [Run(" ", color=NUM, size=size, image="ic_heart"),
                              Run("%s", [HEART], color=NUM, size=size), c(size)], 6, "heart icon"),
        "compact": val(y, size, [Run("%s", [HEART], color=NUM, size=size), c(size),
                                 Run(" // bpm", color=COMMENT, size=size)], 11, "heart compact"),
    })


def weather_val(y, size):
    def by_unit(make):
        return list_cfg("weather_unit", {u: make(*temperature(u)) for u in ("auto", "c", "f")})

    def available(style):
        if style == "full":
            return by_unit(lambda t, u: val(y, size, [Run('"%s°%s %s"', [t, u, WEATHER_COND], color=STR, size=size),
                                                      c(size)], 16, "weather"))
        if style in ("temp", "icon"):
            icon = [Run(" ", color=NUM, size=size, image="ic_weather")] if style == "icon" else []
            return by_unit(lambda t, u: val(y, size, icon + [Run("%s", [t], color=NUM, size=size), c(size),
                                                             Run(" // °%s", [u], color=COMMENT, size=size)],
                                            10, "temp"))
        return val(y, size, [Run('"%s"', [WEATHER_COND], color=STR, size=size), c(size)], 14, "sky")

    # No weather data: the language's null literal (rendered by the key layer, see body()).
    return list_cfg("weather_style", {st: condition([(WEATHER_OK, available(st))])
                                      for st in ("full", "temp", "icon", "condition")})


def status_val(y, size):
    return val(y, size, [Run('"%s"', [STATUS], color=STR, size=size), c(size)], 12, "status")


VALUES = {"date": date_val, "battery": battery_val, "steps": steps_val, "heart": heart_val,
          "weather": weather_val, "status": status_val}
HIDEABLE = {"battery": "battery_style", "steps": "steps_style", "heart": "heart_style", "weather": "weather_style"}


# --------------------------------------------------------------------------- hero clock

def clock(lay: dict, factor: float, name: str):
    cy = lay["hero_c"]

    # Dense layouts write `Time: "14:35"` on one line: the hero starts after the key instead of centered.
    inline = not lay["key_line"]
    x0 = HERO_INLINE_X if inline else 0

    def render(hour, secs, ampm):
        half = circle_half_width(cy, 18)
        max_w = (CENTER + half - x0) if inline else 2 * half
        width_em = EM * (5 + 2 * 0.6 + (3 * 0.42 if secs else 0) + (3 * 0.34 if ampm else 0))
        sz = min(lay["hero"] * factor, max_w / width_em)
        runs = [Run('"', color=STR, size=sz * 0.6), Run("%s:%s", [hour, MINUTE], color=CLOCK, size=sz, family=BOLD)]
        if secs:
            runs.append(Run(":%s", [SECOND], color=CLOCK, size=sz * 0.42))
        if ampm:
            runs.append(Run(" %s", [AMPM], color=CLOCK, size=sz * 0.34))
        runs.append(Run('"', color=STR, size=sz * 0.6))
        if inline:
            return text(x0, cy - sz * 0.66, CANVAS - x0, sz * 1.3, runs, name=f"time_{name}")
        return text(0, cy - sz * 0.66, CANVAS, sz * 1.3, runs, align="CENTER", name=f"time_{name}")

    return time_tree(render)


# --------------------------------------------------------------------------- body per (layout, text size)

def keys_layer(lang: str, name: str, lay: dict, ts: str):
    header_y, key_y, rows_y, close_y, size, _ = geometry(lay, ts)
    nodes = [line(header_y, size, [Run(t, color=tok(cn), size=size) for t, cn in HEADER[lang]],
                  13, f"{lang} {name} header", X_CODE)]
    if key_y is not None:
        nodes.append(line(key_y, size, [Run(KEYS[lang]["time"], color=IDENT, size=size)], 5, "time key", x_key(size)))
    else:
        nodes.append(text(X_CODE - 4, lay["hero_c"] - size * 0.7, 80, size * 1.35,
                          [Run(KEYS[lang]["time"], color=COMMENT, size=size * 0.85)]))
    for ind, y in zip(lay["rows"], rows_y):
        nodes.append(line(y, size, [Run(KEYS[lang][ind], color=IDENT, size=size)], 8, f"key {ind}", x_key(size)))
        if ind == "weather":
            # without weather data the value becomes the language's null literal
            nodes.append(condition([(WEATHER_OK, group(f"wx_ok_{lang}", []))],
                                   default=val(y, size, [Run(NIL[lang], color=KW, size=size), c(size)], 5, "nil")))
    nodes.append(line(close_y, size, [Run(CLOSE[lang], color=PUNCT, size=size)], 2, "close", X_CODE))
    return wrap(*nodes)


def gutter(name: str, lay: dict, ts: str):
    header_y, key_y, rows_y, close_y, size, _ = geometry(lay, ts)
    numbered = [header_y] + ([key_y] if key_y is not None else []) + [lay["hero_c"] - size * 0.6] + rows_y
    if lay.get("ext"):
        numbered += [EXT1_Y, EXT2_Y]
    numbered.append(close_y)
    gsize = round(size * 0.75)
    nums = []
    hero_index = 3 if key_y is not None else 2
    for i, y in enumerate(numbered, start=1):
        label = str(i)
        if i == hero_index and key_y is not None:
            continue  # centered hero line: its number would collide with the opening quote
        check.line(f"gutter {name} {ts} {i}", X_GUTTER_RIGHT - len(label) * gsize * EM, y + 3,
                   gsize * 1.35, len(label), gsize)
        nums.append(text(X_GUTTER_RIGHT - 34, y + 3, 34, gsize * 1.35,
                         [Run(label, color=COMMENT, size=gsize, family=LIGHT)], align="END"))
    return bool_cfg("line_numbers", wrap(*nums))


def masks(lay: dict, ts: str):
    """Hidden indicators: cover the (always drawn) key with the background color.

    Keys are language specific; masking them once is far cheaper than repeating every key inside
    each visible style option (WFF v2 ListConfiguration has no 'else' branch).
    """
    _, _, rows_y, _, size, _ = geometry(lay, ts)
    out = []
    for ind, y in zip(lay["rows"], rows_y):
        if ind in HIDEABLE:
            out.append(list_cfg(HIDEABLE[ind], {"hidden": rect(x_key(size) - 2, y, KEY_COLS * size * EM + 4,
                                                               round(size * 1.35), cfg_color("bg_color"))}))
    return out


def body(name: str, lay: dict, ts: str):
    _, _, rows_y, _, size, _ = geometry(lay, ts)
    values = [VALUES[ind](y, size) for ind, y in zip(lay["rows"], rows_y)]
    keys = list_cfg("language", {lang: keys_layer(lang, name, lay, ts) for lang in ("go", "js")})
    return group(f"{name}_{ts}", [keys, *masks(lay, ts), *values, gutter(name, lay, ts)])


def layout_tree():
    return list_cfg("layout", {
        name: wrap(list_cfg("text_size", {ts: body(name, lay, ts) for ts in TEXT_SIZES}),
                   list_cfg("clock_size", {sid: clock(lay, f, f"{name}_{sid}") for sid, f in CLOCK_SIZES}))
        for name, lay in LAYOUTS.items()})


def editor_chrome():
    """Static editor decorations: a tab label on top and a status bar at the bottom (active mode only)."""
    tab = list_cfg("language", {
        "go": text(0, 30, CANVAS, 24, [Run("main.go", color=COMMENT, size=15)], align="CENTER"),
        "js": text(0, 30, CANVAS, 24, [Run("dev.js", color=COMMENT, size=15)], align="CENTER"),
    })
    status = text(0, 408, CANVAS, 22, [Run("-- NORMAL --", color=FUNC, size=13)], align="CENTER")
    return bool_cfg("show_chrome", wrap(tab, status))


def rings():
    track = "#33FFFFFF"
    return group("rings", [
        list_cfg("battery_style", {"ring": arc_ring("battery_ring", CENTER, CENTER, 458, 220, 100,
                                                    BATTERY_FRAC, NUM, track, 7)}),
        list_cfg("steps_style", {"ring": arc_ring("steps_ring", CENTER, CENTER, 458, 140, 100,
                                                  STEP_FRAC, STR, track, 7, direction="COUNTER_CLOCKWISE")}),
    ])


# --------------------------------------------------------------------------- AOD

def ambient():
    def aod_time(hour, _secs, ampm):
        sz = 80 if not ampm else 70
        runs = [Run('"', color=COMMENT, size=sz * 0.55, family=LIGHT),
                Run("%s:%s", [hour, MINUTE], color=CLOCK, size=sz, family=LIGHT)]
        if ampm:
            runs.append(Run(" %s", [AMPM], color=CLOCK, size=sz * 0.32, family=LIGHT))
        runs.append(Run('"', color=COMMENT, size=sz * 0.55, family=LIGHT))
        return text(0, 182, CANVAS, 106, runs, align="CENTER")

    def key():
        return list_cfg("language", {
            "go": text(0, 148, CANVAS, 30, [Run("Time:", color=COMMENT, size=20, family=LIGHT)], align="CENTER"),
            "js": text(0, 148, CANVAS, 30, [Run("time:", color=COMMENT, size=20, family=LIGHT)], align="CENTER"),
        })

    def date():
        return list_cfg("date_format", {d.id: text(0, 290, CANVAS, 30, [date_run(d, COMMENT, 20, LIGHT, '"', '"')],
                                                   align="CENTER") for d in DATE_FORMATS if d.template})

    def stats():
        return text(0, 324, CANVAS, 28, [Run("// %s", [BATTERY], color=COMMENT, size=18, family=LIGHT),
                                         Run("% · ", color=COMMENT, size=18, family=LIGHT),
                                         Run("%s", [STEPS], color=COMMENT, size=18, family=LIGHT)], align="CENTER")

    return group("ambient", [list_cfg("aod_mode", {
        "time": wrap(key(), time_tree_no_seconds(aod_time)),
        "time_date": wrap(key(), time_tree_no_seconds(aod_time), date()),
        "full": wrap(key(), time_tree_no_seconds(aod_time), date(), stats()),
    })], alpha=0, variants=[ambient_alpha(200)])


# --------------------------------------------------------------------------- complications

def complications():
    size = 16

    def render(slot, fallback):
        def content(text_expr):
            title = f'[COMPLICATION.TITLE] != null ? [COMPLICATION.TITLE] : "{fallback}"'
            runs = [Run("%s", [title], color=IDENT, size=size), Run(": ", color=PUNCT, size=size),
                    Run('"%s"', [text_expr], color=STR, size=size), Run(",", color=PUNCT, size=size)]
            t = text(0, 0, 290, 24, runs, ellipsis=True)
            return group(f"{slot}_content", [bool_cfg("show_ext", list_cfg("layout", {"full": t, "info": t}))],
                         w=290, h=24)

        return {"SHORT_TEXT": content("[COMPLICATION.TEXT]"), "LONG_TEXT": content("[COMPLICATION.TEXT]"),
                "RANGED_VALUE": content("[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : "
                                        "[COMPLICATION.RANGED_VALUE_VALUE]")}

    slots = []
    for slot, y, label, provider in (
            ("ext1", EXT1_Y, s("slot_ext1", "Code line 1 (e.g. calories)", "Linha 1 (ex.: calorias)"), "SUNRISE_SUNSET"),
            ("ext2", EXT2_Y, s("slot_ext2", "Code line 2 (e.g. distance)", "Linha 2 (ex.: distância)"),
             "UNREAD_NOTIFICATION_COUNT")):
        slots.append(complication_slot(slot, label, x_key(size), y, 290, 24, render(slot, slot),
                                       default_provider=provider, default_type="SHORT_TEXT"))
    return slots


# --------------------------------------------------------------------------- configurations

def user_configurations():
    syntax = [(p.id, s(f"pal_{p.id}", p.en, p.pt),
               [p.keyword, p.key, p.string, p.number, p.punct]) for p in PALETTES]
    cfgs = [
        decl_list("language", s("cfg_language", "Language", "Linguagem"), "go", [
            ("go", s("opt_lang_go", "Go", "Go")), ("js", s("opt_lang_js", "JavaScript", "JavaScript"))]),
        decl_list("layout", s("cfg_layout", "Layout / code density", "Layout / densidade"), "balanced", [
            ("minimal", s("opt_layout_minimal", "Minimal: time + date", "Minimalista: hora + data")),
            ("compact", s("opt_layout_compact", "Compact", "Compacto")),
            ("balanced", s("opt_layout_balanced", "Balanced", "Equilibrado")),
            ("full", s("opt_layout_full", "Full: all data + complications", "Completo: tudo + complicações")),
            ("info", s("opt_layout_info", "Informative: dense", "Informativo: denso"))]),
        decl_color("syntax", s("cfg_syntax", "Syntax theme", "Tema de sintaxe"), "vscode", syntax),
        decl_list("time_format", s("cfg_time_format", "Time format", "Formato da hora"), "system", time_formats(s)),
        decl_bool("show_seconds", s("cfg_show_seconds", "Show seconds", "Mostrar segundos"), False),
        decl_list("clock_size", s("cfg_clock_size", "Clock size", "Tamanho do relógio"), "m", [
            ("s", s("opt_size_s", "Small", "Pequeno")), ("m", s("opt_size_m", "Medium", "Médio")),
            ("l", s("opt_size_l", "Large", "Grande")), ("xl", s("opt_size_xl", "Extra large", "Extra grande"))]),
        decl_list("text_size", s("cfg_text_size", "Code text size & spacing", "Tamanho e espaçamento do código"), "m", [
            ("s", s("opt_text_s", "Small · tight", "Pequeno · justo")),
            ("m", s("opt_text_m", "Medium · normal", "Médio · normal")),
            ("l", s("opt_text_l", "Large · relaxed", "Grande · espaçado"))]),
        decl_bool("line_numbers", s("cfg_line_numbers", "Line numbers", "Numeração de linhas"), True),
        decl_list("date_format", s("cfg_date_format", "Date format", "Formato da data"), "wd_d_mmm", date_options(s)),
        decl_list("battery_style", s("cfg_battery", "Battery", "Bateria"), "percent", [
            ("percent", s("opt_bat_percent", "Percentage", "Percentual")),
            ("bar", s("opt_bat_bar", "Progress bar", "Barra de progresso")),
            ("ring", s("opt_bat_ring", "Circular ring", "Anel circular")),
            ("icon", s("opt_bat_icon", "Icon + value", "Ícone + valor")),
            ("hidden", s("opt_hidden", "Hidden", "Oculto"))]),
        decl_list("steps_style", s("cfg_steps", "Steps", "Passos"), "count", [
            ("count", s("opt_steps_count", "Step count", "Número de passos")),
            ("goal", s("opt_steps_goal", "Steps / goal", "Passos / meta")),
            ("bar", s("opt_steps_bar", "Goal progress bar", "Barra da meta")),
            ("ring", s("opt_steps_ring", "Circular ring", "Anel circular")),
            ("icon", s("opt_steps_icon", "Icon + count", "Ícone + quantidade")),
            ("hidden", s("opt_hidden", "Hidden", "Oculto"))]),
        decl_list("heart_style", s("cfg_heart", "Heart rate", "Frequência cardíaca"), "value", [
            ("value", s("opt_hr_value", "Numeric value", "Valor numérico")),
            ("icon", s("opt_hr_icon", "Icon + value", "Ícone + valor")),
            ("compact", s("opt_hr_compact", "Compact", "Compacto")),
            ("hidden", s("opt_hidden", "Hidden", "Oculto"))]),
        decl_list("weather_style", s("cfg_weather", "Weather", "Clima"), "full", [
            ("full", s("opt_wx_full", "Temperature + condition", "Temperatura + condição")),
            ("temp", s("opt_wx_temp", "Temperature", "Temperatura")),
            ("icon", s("opt_wx_icon", "Icon + temperature", "Ícone + temperatura")),
            ("condition", s("opt_wx_condition", "Condition", "Condição")),
            ("hidden", s("opt_hidden", "Hidden", "Oculto"))]),
        decl_list("weather_unit", s("cfg_weather_unit", "Temperature unit", "Unidade de temperatura"), "auto", [
            ("auto", s("opt_unit_auto", "Device setting", "Padrão do aparelho")),
            ("c", s("opt_unit_c", "Celsius", "Celsius")), ("f", s("opt_unit_f", "Fahrenheit", "Fahrenheit"))]),
        decl_bool("show_ext", s("cfg_show_ext", "Complication lines", "Linhas de complicações"), True),
        decl_bool("show_chrome", s("cfg_show_chrome", "Editor tab & status bar", "Aba e barra de status"), True),
        decl_color("clock_color", s("cfg_clock_color", "Clock color", "Cor do relógio"), "white",
                   [(a, s(f"acc_{a}", en, pt), [c]) for a, en, pt, c in ACCENTS]),
        decl_color("bg_color", s("cfg_bg_color", "Background", "Fundo"), "black",
                   [(b, s(f"bg_{b}", en, pt), [c]) for b, en, pt, c in BACKGROUNDS]),
        decl_list("aod_mode", s("cfg_aod", "Always-on display", "Tela sempre ativa"), "time_date", [
            ("time", s("opt_aod_time", "Time only", "Somente hora")),
            ("time_date", s("opt_aod_time_date", "Time + date", "Hora + data")),
            ("full", s("opt_aod_full", "Time, date, battery, steps", "Hora, data, bateria, passos"))]),
    ]
    slots = {"ext1": ("SUNRISE_SUNSET", "SHORT_TEXT"), "ext2": ("UNREAD_NOTIFICATION_COUNT", "SHORT_TEXT")}
    flavors = E("Flavors", [
        flavor("go_dev", s("flv_go", "Go Developer", "Go Developer"), {
            "language": "go", "layout": "balanced", "syntax": "vscode", "clock_color": "cyan",
            "line_numbers": "TRUE", "show_chrome": "TRUE", "bg_color": "black"}),
        flavor("js_dev", s("flv_js", "JavaScript Developer", "JavaScript Developer"), {
            "language": "js", "layout": "balanced", "syntax": "onedark", "clock_color": "yellow",
            "line_numbers": "TRUE", "show_chrome": "TRUE", "bg_color": "black"}),
        flavor("vscode_dark", s("flv_vscode", "VS Code Dark", "VS Code Dark"), {
            "language": "js", "layout": "full", "syntax": "vscode", "clock_color": "white", "bg_color": "editor",
            "line_numbers": "TRUE", "battery_style": "bar", "steps_style": "bar"}, slots),
        flavor("terminal", s("flv_terminal", "Terminal", "Terminal"), {
            "language": "go", "layout": "compact", "syntax": "terminal", "clock_color": "green",
            "line_numbers": "FALSE", "show_chrome": "TRUE", "bg_color": "black", "text_size": "l"}),
        flavor("minimal_code", s("flv_minimal", "Minimal Code", "Minimal Code"), {
            "language": "go", "layout": "minimal", "syntax": "mono", "clock_color": "white",
            "line_numbers": "FALSE", "show_chrome": "FALSE", "clock_size": "l"}),
        flavor("full_stats", s("flv_full", "Full Stats", "Completo"), {
            "language": "go", "layout": "info", "syntax": "dracula", "clock_color": "purple",
            "battery_style": "ring", "steps_style": "ring", "aod_mode": "full", "show_ext": "TRUE"}, slots),
        flavor("amoled", s("flv_amoled", "AMOLED (battery saver)", "AMOLED (economia)"), {
            "language": "go", "layout": "compact", "syntax": "mono", "clock_color": "white", "bg_color": "black",
            "line_numbers": "FALSE", "show_chrome": "FALSE", "show_seconds": "FALSE", "aod_mode": "time"}),
    ], defaultValue="go_dev")
    return cfgs + [flavors]


def build():
    s("watch_face_name", "Code Developer", "Code Developer")
    active = group("active", [background(cfg_color("bg_color")), editor_chrome(), layout_tree(), rings()],
                   variants=[ambient_hide()])
    face = watch_face(user_configurations(), [active, ambient(), *complications()],
                      metadata={"CLOCK_TYPE": "DIGITAL", "PREVIEW_TIME": "14:35:42"})
    write_module(MODULE, face, s, "code-developer/generator/code_face.py",
                 "Code Developer - DevTime Watch Faces. GENERATED FILE: edit code-developer/generator/code_face.py")
    if check.problems:
        print("layout warnings:")
        for p in sorted(set(check.problems)):
            print("  " + p)
    print(f"wrote {MODULE / 'src/main/res/raw/watchface.xml'}")


if __name__ == "__main__":
    build()
