"""JSON Developer watch face generator.

Run:  python3 json-developer/generator/json_face.py
Writes json-developer/src/main/res/{raw/watchface.xml, values*/strings.xml, xml/watch_face_info.xml}
and src/main/AndroidManifest.xml.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared/scripts"))

from wffgen.core import (  # noqa: E402
    AMPM, BATTERY, BATTERY_FRAC, CANVAS, CENTER, DATE_FORMATS, DEVICE_STATUS, MINUTE, SECOND,
    STEP_FRAC, STEP_GOAL, STEPS, WEATHER_COND, WEATHER_OK, Run, Strings, ambient_alpha, ambient_hide,
    arc_ring, background, bool_cfg, cfg_color, circle_half_width, complication_slot, condition,
    date_run, date_options, date_tree, heart, decl_bool, decl_color, decl_list, flavor, group, list_cfg,
    temperature, text, text_bar, time_formats, time_tree, time_tree_no_seconds, vline, watch_face, wrap,
)
from wffgen.module import LayoutCheck, write_module  # noqa: E402
from wffgen.palettes import ACCENTS, BACKGROUNDS, PALETTES  # noqa: E402

MODULE = ROOT / "json-developer"
REG, BOLD, LIGHT = "jetbrains_mono_regular", "jetbrains_mono_bold", "jetbrains_mono_light"
HEART = heart('"null"')  # JSON-native empty value when there is no reading
EM = 0.6  # JetBrains Mono advance width in em

KEY = cfg_color("key_color")
STR = cfg_color("value_color", 0)
NUM = cfg_color("value_color", 1)
TIME = cfg_color("time_color")
PUNCT = cfg_color("punct_color")

X_BRACE = 88
X_KEY = 114
X_GUTTER_RIGHT = 80
EXT1_Y, EXT2_Y = 322, 349  # complication slots are fixed in WFF v2, every layout reserves these rows

s = Strings()
check = LayoutCheck(EM)

# --------------------------------------------------------------------------- layouts

LAYOUTS = {
    # name: time center/base size, brace rows, row font size and indicator rows (top y)
    "minimal": dict(open=112, key=144, time_c=222, time_size=96, row=22, close=330,
                    rows=[("date", 288)]),
    "compact": dict(open=92, key=120, time_c=190, time_size=86, row=22, close=344,
                    rows=[("date", 250), ("battery", 279), ("steps", 308)]),
    "balanced": dict(open=84, key=108, time_c=166, time_size=78, row=22, close=364,
                     rows=[("date", 222), ("battery", 250), ("steps", 278), ("heart", 306), ("status", 334)]),
    "full": dict(open=80, key=80, time_c=136, time_size=62, row=20, close=376,
                 rows=[("date", 178), ("battery", 205), ("steps", 232), ("heart", 259), ("weather", 286),
                       ("ext1", EXT1_Y), ("ext2", EXT2_Y)]),
    "info": dict(open=80, key=80, time_c=124, time_size=50, row=20, close=376,
                 rows=[("date", 160), ("battery", 186), ("steps", 212), ("heart", 238), ("weather", 264),
                       ("status", 290), ("ext1", EXT1_Y), ("ext2", EXT2_Y)]),
}
CLOCK_SIZES = [("s", 0.82), ("m", 1.0), ("l", 1.12), ("xl", 1.24)]


def row_box(y: float, size: float, x: float = X_KEY) -> tuple[float, float, float, float]:
    """Text box for an indicator row, clipped to the circle so long values ellipsize."""
    h = round(size * 1.35)
    half = min(circle_half_width(y + h * 0.2, 12), circle_half_width(y + h * 0.8, 12))
    return x, y, round(CENTER + half - x), h


# --------------------------------------------------------------------------- run helpers

def key(name: str, size: float) -> list[Run]:
    return [Run(f'"{name}"', color=KEY, size=size), Run(": ", color=PUNCT, size=size)]


def comma(size: float) -> Run:
    return Run(",", color=PUNCT, size=size)


def line(y: float, size: float, runs: list[Run], chars: int, where: str, x: float = X_KEY):
    bx, by, bw, bh = row_box(y, size, x)
    check.line(where, bx, by, bh, chars, size)
    return text(bx, by, bw, bh, runs, ellipsis=True)


# --------------------------------------------------------------------------- indicator rows

def date_row(y: float, size: float, last: bool) -> object:
    def render(d):
        runs = key("date", size) + [date_run(d, STR, size, before='"', after='"')]
        if not last:
            runs.append(comma(size))
        return line(y, size, runs, 10 + d.sample_chars, f"date {d.id} @y{y}")
    return date_tree(render)


def battery_row(y: float, size: float) -> object:
    bar_full, bar_empty = text_bar(BATTERY_FRAC, 10, "█", "░")
    return list_cfg("battery_style", {
        "percent": line(y, size, key("battery", size) + [
            Run('"%s', [BATTERY], color=STR, size=size), Run('%"', color=STR, size=size), comma(size)],
            18, f"battery% @y{y}"),
        "bar": line(y, size, key("battery", size) + [
            Run('"', color=STR, size=size), Run("%s", [bar_full], color=NUM, size=size),
            Run("%s", [bar_empty], color=PUNCT, size=size), Run('"', color=STR, size=size), comma(size)],
            24, f"battery bar @y{y}"),
        "ring": line(y, size, key("battery", size) + [Run("%s", [BATTERY], color=NUM, size=size), comma(size)],
                     15, f"battery ring @y{y}"),
        "icon": line(y, size, [Run(" ", color=NUM, size=size, image="ic_battery")] + key("battery", size) + [
            Run("%s", [BATTERY], color=NUM, size=size), comma(size)], 17, f"battery icon @y{y}"),
    })


def steps_row(y: float, size: float) -> object:
    bar_full, bar_empty = text_bar(STEP_FRAC, 10, "█", "░")
    return list_cfg("steps_style", {
        "count": line(y, size, key("steps", size) + [Run("%s", [STEPS], color=NUM, size=size), comma(size)],
                      15, f"steps @y{y}"),
        "goal": line(y, size, key("steps", size) + [
            Run('"%s/%s"', [STEPS, STEP_GOAL], color=STR, size=size), comma(size)], 22, f"steps goal @y{y}"),
        "bar": line(y, size, key("steps", size) + [
            Run('"', color=STR, size=size), Run("%s", [bar_full], color=NUM, size=size),
            Run("%s", [bar_empty], color=PUNCT, size=size), Run('"', color=STR, size=size), comma(size)],
            22, f"steps bar @y{y}"),
        "ring": line(y, size, key("steps", size) + [Run("%s", [STEPS], color=NUM, size=size), comma(size)],
                     15, f"steps ring @y{y}"),
        "icon": line(y, size, [Run(" ", color=NUM, size=size, image="ic_steps")] + key("steps", size) + [
            Run("%s", [STEPS], color=NUM, size=size), comma(size)], 17, f"steps icon @y{y}"),
    })


def heart_row(y: float, size: float) -> object:
    return list_cfg("heart_style", {
        "value": line(y, size, key("heartRate", size) + [Run("%s", [HEART], color=NUM, size=size), comma(size)],
                      17, f"heart @y{y}"),
        "icon": line(y, size, [Run(" ", color=NUM, size=size, image="ic_heart")] + key("bpm", size) + [
            Run("%s", [HEART], color=NUM, size=size), comma(size)], 13, f"heart icon @y{y}"),
        "compact": line(y, size, key("hr", size) + [Run("%s", [HEART], color=NUM, size=size), comma(size)],
                        10, f"heart compact @y{y}"),
    })


def weather_row(y: float, size: float) -> object:
    def by_unit(make):
        return list_cfg("weather_unit", {u: make(*temperature(u)) for u in ("auto", "c", "f")})

    def available(style):
        if style == "full":
            return by_unit(lambda t, u: line(y, size, key("weather", size) + [
                Run('"%s°%s %s"', [t, u, WEATHER_COND], color=STR, size=size), comma(size)],
                28, f"weather full @y{y}"))
        if style == "temp":
            return by_unit(lambda t, u: line(y, size, key("temp", size) + [
                Run("%s", [t], color=NUM, size=size), Run('"°%s"', [u], color=STR, size=size), comma(size)],
                14, f"weather temp @y{y}"))
        if style == "icon":
            return by_unit(lambda t, u: line(y, size, [Run(" ", color=NUM, size=size, image="ic_weather")] +
                                             key("temp", size) + [
                Run("%s", [t], color=NUM, size=size), Run('"°%s"', [u], color=STR, size=size), comma(size)],
                16, f"weather icon @y{y}"))
        return line(y, size, key("sky", size) + [Run('"%s"', [WEATHER_COND], color=STR, size=size), comma(size)],
                    22, f"weather sky @y{y}")

    def unavailable(name):
        # Honest empty state: no weather source/data -> JSON null, never a made-up value.
        return line(y, size, key(name, size) + [Run("null", color=KEY, size=size), comma(size)],
                    17, f"weather null @y{y}")

    names = {"full": "weather", "temp": "temp", "icon": "temp", "condition": "sky"}
    return list_cfg("weather_style", {
        st: condition([(WEATHER_OK, available(st))], default=unavailable(nm)) for st, nm in names.items()
    })


def status_row(y: float, size: float) -> object:
    return bool_cfg("show_status", line(y, size, key("status", size) + [
        Run('"%s"', [DEVICE_STATUS], color=STR, size=size)], 20, f"status @y{y}"))


ROW_BUILDERS = {"battery": battery_row, "steps": steps_row, "heart": heart_row,
                "weather": weather_row, "status": status_row}


# --------------------------------------------------------------------------- hero clock

def time_fit(size: float, secs: bool, ampm: bool, max_w: float) -> float:
    width_em = EM * (5 + 2 * 0.6 + (3 * 0.42 if secs else 0) + (3 * 0.34 if ampm else 0))
    return min(size, max_w / width_em)


def clock(layout: dict, factor: float, name: str) -> object:
    cy = layout["time_c"]

    def render(hour: str, secs: bool, ampm: bool):
        max_w = 2 * circle_half_width(cy, 18)
        sz = round(time_fit(layout["time_size"] * factor, secs, ampm, max_w), 1)
        runs = [Run('"', color=STR, size=round(sz * 0.6, 1), family=REG),
                Run("%s:%s", [hour, MINUTE], color=TIME, size=sz, family=BOLD)]
        if secs:
            runs.append(Run(":%s", [SECOND], color=TIME, size=round(sz * 0.42, 1), family=REG))
        if ampm:
            runs.append(Run(" %s", [AMPM], color=TIME, size=round(sz * 0.34, 1), family=REG))
        runs.append(Run('"', color=STR, size=round(sz * 0.6, 1), family=REG))
        h = round(sz * 1.3)
        return text(0, round(cy - sz * 0.66), CANVAS, h, runs, align="CENTER", name=f"time_{name}")

    return time_tree(render)


# --------------------------------------------------------------------------- decoration (braces, gutter, guides)

def decoration(name: str, layout: dict) -> object:
    size = layout["row"]
    rows_y = [layout["key"]] + [y for _, y in layout["rows"]]
    lines_y = sorted(set([layout["open"]] + rows_y + [layout["close"]]))

    def brace(y, ch):
        return text(X_BRACE, y, 40, round(size * 1.35), [Run(ch, color=PUNCT, size=size)])

    def time_key():
        return text(X_KEY, layout["key"], 200, round(size * 1.35), key("time", size))

    def gutter():
        nums = []
        for i, y in enumerate(lines_y, start=1):
            gsize = size * 0.72
            label = str(i)
            check.line(f"gutter {name} line {i}", X_GUTTER_RIGHT - len(label) * gsize * EM, y + 3,
                       round(gsize * 1.35), len(label), gsize)
            nums.append(text(X_GUTTER_RIGHT - 30, y + 3, 30, round(gsize * 1.35),
                             [Run(label, color=PUNCT, size=gsize, family=LIGHT)], align="END", alpha=150))
        return nums

    def guide():
        return vline(X_BRACE + 6, layout["open"] + size * 1.4, layout["close"] - 2, PUNCT, 1, dash="2 4")

    base = [brace(layout["open"], "{"), brace(layout["close"], "}"), time_key()]
    return list_cfg("json_style", {
        "pretty": wrap(*base),
        "numbered": wrap(*base, *gutter()),
        "guides": wrap(*base, guide()),
        "bare": wrap(time_key()),
    })


# --------------------------------------------------------------------------- layout assembly

def layout_body(name: str, layout: dict) -> object:
    size = layout["row"]
    nodes = [decoration(name, layout)]
    nodes.append(list_cfg("clock_size", {sid: clock(layout, f, f"{name}_{sid}") for sid, f in CLOCK_SIZES}))
    data_rows = [r for r in layout["rows"] if not r[0].startswith("ext")]
    for i, (ind, y) in enumerate(layout["rows"]):
        if ind == "date":
            nodes.append(date_row(y, size, last=(i == len(layout["rows"]) - 1)))
        elif ind in ROW_BUILDERS:
            nodes.append(ROW_BUILDERS[ind](y, size))
    del data_rows
    return group(f"layout_{name}", nodes)


def rings() -> object:
    track = "#33FFFFFF"
    return group("rings", [
        list_cfg("battery_style", {"ring": arc_ring("battery_ring", CENTER, CENTER, 458, 220, 100,
                                                    BATTERY_FRAC, NUM, track, 7)}),
        list_cfg("steps_style", {"ring": arc_ring("steps_ring", CENTER, CENTER, 458, 140, 100,
                                                  STEP_FRAC, STR, track, 7, direction="COUNTER_CLOCKWISE")}),
    ])


# --------------------------------------------------------------------------- always-on display

def ambient() -> object:
    def aod_time(hour: str, _secs: bool, ampm: bool):
        sz = 84 if not ampm else 72
        runs = [Run('"', color=PUNCT, size=sz * 0.55, family=LIGHT),
                Run("%s:%s", [hour, MINUTE], color=TIME, size=sz, family=LIGHT)]
        if ampm:
            runs.append(Run(" %s", [AMPM], color=TIME, size=sz * 0.32, family=LIGHT))
        runs.append(Run('"', color=PUNCT, size=sz * 0.55, family=LIGHT))
        return text(0, 178, CANVAS, 110, runs, align="CENTER", name="aod_time")

    def aod_key():
        return text(0, 146, CANVAS, 30, [Run('"time":', color=PUNCT, size=20, family=LIGHT)], align="CENTER")

    def aod_date():
        return list_cfg("date_format", {
            d.id: text(0, 290, CANVAS, 30, [date_run(d, PUNCT, 20, LIGHT, '"', '"')], align="CENTER")
            for d in DATE_FORMATS if d.template})

    def aod_stats():
        return text(0, 324, CANVAS, 28, [
            Run("%s", [BATTERY], color=PUNCT, size=18, family=LIGHT), Run("% · ", color=PUNCT, size=18, family=LIGHT),
            Run("%s", [STEPS], color=PUNCT, size=18, family=LIGHT)], align="CENTER")

    clock_node = time_tree_no_seconds(aod_time)
    return group("ambient", [list_cfg("aod_mode", {
        "time": wrap(aod_key(), clock_node),
        "time_date": wrap(aod_key(), time_tree_no_seconds(aod_time), aod_date()),
        "full": wrap(aod_key(), time_tree_no_seconds(aod_time), aod_date(), aod_stats()),
    })], alpha=0, variants=[ambient_alpha(200)])


# --------------------------------------------------------------------------- complications

def complications() -> list:
    def render(slot: str, title_fallback: str, size: float = 20):
        def body(text_expr: str) -> object:
            title = f'[COMPLICATION.TITLE] != null ? [COMPLICATION.TITLE] : "{title_fallback}"'
            runs = [Run('"%s"', [title], color=KEY, size=size), Run(": ", color=PUNCT, size=size),
                    Run('"%s"', [text_expr], color=STR, size=size), Run(",", color=PUNCT, size=size)]
            t = text(0, 0, 300, 27, runs, ellipsis=True)
            return group(f"{slot}_content", [bool_cfg("show_ext", list_cfg("layout", {
                "full": t, "info": t}))], w=300, h=27)
        return {
            "SHORT_TEXT": body("[COMPLICATION.TEXT]"),
            "LONG_TEXT": body("[COMPLICATION.TEXT]"),
            "RANGED_VALUE": body("[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : [COMPLICATION.RANGED_VALUE_VALUE]"),
        }

    slots = []
    for slot, y, label, fallback, provider in (
            ("ext1", EXT1_Y, s("slot_ext1", "Data line 1 (e.g. calories)", "Linha 1 (ex.: calorias)"), "ext1",
             "SUNRISE_SUNSET"),
            ("ext2", EXT2_Y, s("slot_ext2", "Data line 2 (e.g. distance)", "Linha 2 (ex.: distância)"), "ext2",
             "UNREAD_NOTIFICATION_COUNT")):
        bx, by, bw, bh = row_box(y, 20)
        bw = min(bw, 300)
        slots.append(complication_slot(slot, label, bx, by, bw, bh, render(slot, fallback),
                                       default_provider=provider, default_type="SHORT_TEXT"))
    return slots


# --------------------------------------------------------------------------- user configurations

def palette_colors(attr: str) -> list[tuple[str, str, list[str]]]:
    return [(p.id, s(f"pal_{p.id}", p.en, p.pt), [getattr(p, a) for a in attr.split("+")]) for p in PALETTES]


def user_configurations() -> list:
    layouts = [
        ("minimal", s("opt_layout_minimal", "Minimal: time + date", "Minimalista: hora + data")),
        ("compact", s("opt_layout_compact", "Compact", "Compacto")),
        ("balanced", s("opt_layout_balanced", "Balanced", "Equilibrado")),
        ("full", s("opt_layout_full", "Full: all data + complications", "Completo: tudo + complicações")),
        ("info", s("opt_layout_info", "Informative: dense", "Informativo: denso")),
    ]
    cfgs = [
        decl_list("layout", s("cfg_layout", "Layout", "Layout"), "balanced", layouts),
        decl_list("json_style", s("cfg_json_style", "JSON style", "Estilo do JSON"), "pretty", [
            ("pretty", s("opt_style_pretty", "Pretty printed", "Formatado")),
            ("numbered", s("opt_style_numbered", "Line numbers", "Números de linha")),
            ("guides", s("opt_style_guides", "Indent guides", "Guias de indentação")),
            ("bare", s("opt_style_bare", "Bare (no braces)", "Sem chaves")),
        ]),
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
        decl_bool("show_status", s("cfg_show_status", "Device status line", "Linha de status"), True),
        decl_bool("show_ext", s("cfg_show_ext", "Complication lines", "Linhas de complicações"), True),
        decl_color("key_color", s("cfg_key_color", "Key color", "Cor das chaves"), "vscode", palette_colors("key")),
        decl_color("value_color", s("cfg_value_color", "Value colors", "Cor dos valores"), "vscode",
                   palette_colors("string+number")),
        decl_color("time_color", s("cfg_time_color", "Clock color", "Cor do relógio"), "white",
                   [(a, s(f"acc_{a}", en, pt), [c]) for a, en, pt, c in ACCENTS]),
        decl_color("punct_color", s("cfg_punct_color", "Braces & punctuation", "Chaves e pontuação"), "vscode",
                   palette_colors("punct")),
        decl_color("bg_color", s("cfg_bg_color", "Background", "Fundo"), "black",
                   [(b, s(f"bg_{b}", en, pt), [c]) for b, en, pt, c in BACKGROUNDS]),
        decl_list("aod_mode", s("cfg_aod", "Always-on display", "Tela sempre ativa"), "time_date", [
            ("time", s("opt_aod_time", "Time only", "Somente hora")),
            ("time_date", s("opt_aod_time_date", "Time + date", "Hora + data")),
            ("full", s("opt_aod_full", "Time, date, battery, steps", "Hora, data, bateria, passos"))]),
    ]
    flavors = E_flavors()
    return cfgs + [flavors]


def E_flavors():
    from wffgen.xml import E
    common_slots = {"ext1": ("SUNRISE_SUNSET", "SHORT_TEXT"), "ext2": ("UNREAD_NOTIFICATION_COUNT", "SHORT_TEXT")}
    return E("Flavors", [
        flavor("clean_json", s("flv_clean", "Clean JSON (Minimal)", "Clean JSON (Minimalista)"), {
            "layout": "minimal", "json_style": "pretty", "clock_size": "l", "date_format": "wd_d_mmm",
            "key_color": "mono", "value_color": "mono", "time_color": "white", "punct_color": "mono",
            "bg_color": "black", "aod_mode": "time_date"}),
        flavor("developer", s("flv_developer", "Developer", "Developer"), {
            "layout": "balanced", "json_style": "numbered", "clock_size": "m", "battery_style": "percent",
            "steps_style": "count", "heart_style": "value", "show_status": "TRUE",
            "key_color": "vscode", "value_color": "vscode", "time_color": "white", "punct_color": "vscode",
            "bg_color": "black"}),
        flavor("full_json", s("flv_full", "Full JSON (Full Stats)", "Full JSON (Completo)"), {
            "layout": "info", "json_style": "guides", "battery_style": "ring", "steps_style": "ring",
            "heart_style": "value", "weather_style": "full", "show_status": "TRUE", "show_ext": "TRUE",
            "key_color": "dracula", "value_color": "dracula", "time_color": "purple", "punct_color": "dracula",
            "bg_color": "black", "aod_mode": "full"}, common_slots),
        flavor("amoled", s("flv_amoled", "AMOLED (battery saver)", "AMOLED (economia)"), {
            "layout": "compact", "json_style": "bare", "show_seconds": "FALSE", "battery_style": "percent",
            "steps_style": "count", "key_color": "mono", "value_color": "mono", "time_color": "white",
            "punct_color": "mono", "bg_color": "black", "aod_mode": "time"}),
    ], defaultValue="developer")


# --------------------------------------------------------------------------- main

def build():
    s("watch_face_name", "JSON Developer", "JSON Developer")
    active = group("active", [
        background(cfg_color("bg_color")),
        list_cfg("layout", {name: layout_body(name, lay) for name, lay in LAYOUTS.items()}),
        rings(),
    ], variants=[ambient_hide()])
    face = watch_face(user_configurations(), [active, ambient(), *complications()],
                      metadata={"CLOCK_TYPE": "DIGITAL", "PREVIEW_TIME": "14:35:42"})
    write_module(MODULE, face, s, "json-developer/generator/json_face.py",
                 "JSON Developer - DevTime Watch Faces. GENERATED FILE: edit json-developer/generator/json_face.py")
    if check.problems:
        print("layout warnings:")
        for p in check.problems:
            print("  " + p)
    print(f"wrote {MODULE / 'src/main/res/raw/watchface.xml'}")


if __name__ == "__main__":
    build()
