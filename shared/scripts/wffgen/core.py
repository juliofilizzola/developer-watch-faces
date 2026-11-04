"""Watch Face Format building blocks shared by the DevTime generators.

Everything emitted here is restricted to WFF v2 elements and attributes that exist in
the vendored XSD (shared/wff-spec/2). Each face generator composes these helpers and
writes a standalone res/raw/watchface.xml into its own module: the packages never
depend on each other at runtime.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from .xml import Cdata, E, Node

CANVAS = 480
CENTER = CANVAS / 2

_ids = itertools.count(1)


def uid(prefix: str) -> str:
    return f"{prefix}{next(_ids)}"


# --------------------------------------------------------------------------- strings

class Strings:
    """Collects user-facing labels so they land in values/ and values-pt-rBR/ strings.xml."""

    def __init__(self):
        self.items: dict[str, tuple[str, str]] = {}

    def __call__(self, key: str, en: str, pt: str | None = None) -> str:
        prev = self.items.get(key)
        if prev and prev != (en, pt or en):
            raise ValueError(f"string '{key}' defined twice with different text")
        self.items[key] = (en, pt or en)
        return key

    def xml(self, lang: int) -> str:
        def esc(s: str) -> str:
            return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                     .replace("'", "\\'").replace('"', '\\"'))
        rows = "".join(f'    <string name="{k}">{esc(v[lang])}</string>\n' for k, v in self.items.items())
        return f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n{rows}</resources>\n'


# --------------------------------------------------------------------------- variants

def ambient_hide() -> Node:
    return E("Variant", mode="AMBIENT", target="alpha", value="0")


def ambient_alpha(value: int) -> Node:
    return E("Variant", mode="AMBIENT", target="alpha", value=str(value))


# --------------------------------------------------------------------------- text

@dataclass
class Run:
    """One colored span of a Text line. `text` is a printf-like template when params are given."""
    text: str = ""
    params: list[str] = field(default_factory=list)
    color: str = "#FFFFFFFF"
    size: float = 24
    family: str = "jetbrains_mono_regular"
    upper: bool = False
    letter_spacing: float | None = None
    image: str | None = None
    glow: str | None = None


def font(run: Run) -> Node:
    children: list = []
    if run.image:
        side = round(run.size * 0.85)
        children.append(E("InlineImage", resource=run.image, color=run.color, width=side, height=side))
    if run.params:
        tpl = E("Template", [Cdata(run.text)] + [E("Parameter", expression=p) for p in run.params])
        children.append(E("Upper", [tpl]) if run.upper else tpl)
    elif run.text:
        children.append(run.text.upper() if run.upper else run.text)
    if run.glow:
        # OutGlow is a decoration wrapper around the formatted content.
        children = [E("OutGlow", children, color=run.glow, radius="6")]
    # The runtime parses Font size as an integer (fractional sizes log "fail to parseInt").
    return E("Font", children, family=run.family, size=round(run.size), color=run.color,
             letterSpacing=run.letter_spacing)


def text(x, y, w, h, runs: list[Run], align: str = "START", name: str | None = None,
         variants: list[Node] | None = None, alpha: int | None = None,
         ellipsis: bool = False) -> Node:
    return E("PartText", [*(variants or []),
                          E("Text", [font(r) for r in runs if r is not None], align=align,
                            ellipsis=True if ellipsis else None)],
             x=round(x), y=round(y), width=round(w), height=round(h), name=name, alpha=alpha)


def group(name: str, children, x=0, y=0, w=CANVAS, h=CANVAS, alpha: int | None = None,
          variants: list[Node] | None = None, scale: float | None = None,
          pivot: tuple[float, float] | None = None) -> Node:
    return E("Group", [*(variants or []), *[c for c in children if c is not None]],
             name=name, x=round(x), y=round(y), width=round(w), height=round(h), alpha=alpha,
             scaleX=scale, scaleY=scale,
             pivotX=pivot[0] if pivot else None, pivotY=pivot[1] if pivot else None)


# --------------------------------------------------------------------------- configuration in scene

_CONFIG_TAGS = {"ListConfiguration", "BooleanConfiguration"}


def option_child(node: Node) -> Node:
    """Options/Compare/Default cannot hold a configuration directly: wrap it in a Group."""
    if node.tag in _CONFIG_TAGS:
        return group(uid("opt_"), [node])
    return node


def list_cfg(cfg_id: str, options: dict[str, Node | None]) -> Node | None:
    opts = [E("ListOption", [option_child(child)], id=k) for k, child in options.items() if child is not None]
    return E("ListConfiguration", opts, id=cfg_id) if opts else None


def bool_cfg(cfg_id: str, on: Node | None, off: Node | None = None) -> Node | None:
    opts = []
    if on is not None:
        opts.append(E("BooleanOption", [option_child(on)], id="TRUE"))
    if off is not None:
        opts.append(E("BooleanOption", [option_child(off)], id="FALSE"))
    return E("BooleanConfiguration", opts, id=cfg_id) if opts else None


def condition(cases: list[tuple[str, Node]], default: Node | None = None) -> Node:
    names = [uid("expr_") for _ in cases]
    exprs = E("Expressions", [E("Expression", [Cdata(c)], name=n) for n, (c, _) in zip(names, cases)])
    compares = [E("Compare", [option_child(child)], expression=n) for n, (_, child) in zip(names, cases)]
    return E("Condition", [exprs, *compares,
                           E("Default", [option_child(default)]) if default is not None else None])


def wrap(*nodes) -> Node:
    """Configuration options hold exactly one child: wrap several nodes in a full-canvas group."""
    items = [n for n in nodes if n is not None]
    if len(items) == 1 and items[0].tag == "Group":
        return items[0]
    return group(uid("g"), items)


# --------------------------------------------------------------------------- configuration declarations

def _default(cfg_id: str, default: str) -> str:
    """WFF_DEFAULTS="layout=full,battery_style=ring" overrides defaults for screenshot/test builds."""
    import os
    for pair in filter(None, os.environ.get("WFF_DEFAULTS", "").split(",")):
        k, _, v = pair.partition("=")
        if k.strip() == cfg_id:
            return v.strip()
    return default


def decl_list(cfg_id: str, label: str, default: str, options: list[tuple[str, str]]) -> Node:
    default = _default(cfg_id, default)
    return E("ListConfiguration",
             [E("ListOption", id=o, displayName=l, screenReaderText=l) for o, l in options],
             id=cfg_id, displayName=label, screenReaderText=label, defaultValue=default)


def decl_bool(cfg_id: str, label: str, default: bool) -> Node:
    return E("BooleanConfiguration", id=cfg_id, displayName=label, screenReaderText=label,
             defaultValue=_default(cfg_id, "TRUE" if default else "FALSE"))


def decl_color(cfg_id: str, label: str, default: str, options: list[tuple[str, str, list[str]]]) -> Node:
    default = _default(cfg_id, default)
    return E("ColorConfiguration",
             [E("ColorOption", id=o, displayName=l, screenReaderText=l, colors=" ".join(cs))
              for o, l, cs in options],
             id=cfg_id, displayName=label, screenReaderText=label, defaultValue=default)


def cfg_color(cfg_id: str, index: int = 0) -> str:
    return f"[CONFIGURATION.{cfg_id}.{index}]"


def flavor(fid: str, label: str, config: dict[str, str], slots: dict[str, tuple[str, str]] | None = None) -> Node:
    kids = [E("Configuration", id=k, optionId=v) for k, v in config.items()]
    for slot_id, (provider, ptype) in (slots or {}).items():
        kids.append(E("ComplicationSlot",
                      [E("DefaultProviderPolicy", defaultSystemProvider=provider,
                         defaultSystemProviderType=ptype)], slotId=slot_id))
    return E("Flavor", kids, id=fid, displayName=label, screenReaderText=label)


# --------------------------------------------------------------------------- time

H24 = "[HOUR_0_23_Z]"
H12 = "[HOUR_1_12_Z]"
MINUTE = "[MINUTE_Z]"
SECOND = "[SECOND_Z]"
AMPM = "[AMPM_STRING]"


def time_formats(s: Strings) -> list[tuple[str, str]]:
    return [
        ("system", s("opt_time_system", "Follow phone setting", "Seguir o celular")),
        ("h24", s("opt_time_24", "24 hours (14:35)", "24 horas (14:35)")),
        ("h12", s("opt_time_12", "12 hours (02:35)", "12 horas (02:35)")),
        ("h12_ampm", s("opt_time_12_ampm", "12 hours + AM/PM", "12 horas + AM/PM")),
    ]


def time_tree(render) -> Node:
    """Expands the time_format x show_seconds matrix.

    render(hour_expr, show_seconds, show_ampm) -> Node
    """
    def secs(hour: str, ampm: bool) -> Node:
        return bool_cfg("show_seconds", render(hour, True, ampm), render(hour, False, ampm))

    return list_cfg("time_format", {
        "system": condition([("[IS_24_HOUR_MODE]", secs(H24, False))], default=secs(H12, True)),
        "h24": secs(H24, False),
        "h12": secs(H12, False),
        "h12_ampm": secs(H12, True),
    })


def time_tree_no_seconds(render) -> Node:
    """Ambient variant: same hour logic, never shows seconds."""
    return list_cfg("time_format", {
        "system": condition([("[IS_24_HOUR_MODE]", render(H24, False, False))], default=render(H12, False, True)),
        "h24": render(H24, False, False),
        "h12": render(H12, False, False),
        "h12_ampm": render(H12, False, True),
    })


# --------------------------------------------------------------------------- date

@dataclass(frozen=True)
class DateFormat:
    id: str
    label_en: str
    label_pt: str
    template: str | None
    params: tuple[str, ...] = ()
    upper: bool = False

    @property
    def sample_chars(self) -> int:
        return {"dmy": 10, "mdy": 10, "dmy_dash": 10, "iso": 10, "d_mmm": 6, "mmm_d": 6,
                "wd_d_mmm": 11, "wd_short": 6, "wd_full": 9, "full": 16}.get(self.id, 10)


# Dates are composed from raw sources instead of icuText(): icuText() re-orders fields to the
# device locale (on a US device "dd MMM" renders as "NOV 04"), which would break explicit formats.
# Month/day names (MONTH_S, MONTH_F, DAY_OF_WEEK_*) are still localized by the device language.
_D, _M, _Y = "[DAY_Z]", "[MONTH_Z]", "[YEAR]"
DATE_FORMATS = [
    DateFormat("dmy", "DD/MM/YYYY", "DD/MM/AAAA", "%s/%s/%s", (_D, _M, _Y)),
    DateFormat("mdy", "MM/DD/YYYY", "MM/DD/AAAA", "%s/%s/%s", (_M, _D, _Y)),
    DateFormat("dmy_dash", "DD-MM-YYYY", "DD-MM-AAAA", "%s-%s-%s", (_D, _M, _Y)),
    DateFormat("iso", "YYYY-MM-DD", "AAAA-MM-DD", "%s-%s-%s", (_Y, _M, _D)),
    DateFormat("d_mmm", "DD MMM (04 NOV)", "DD MMM (04 NOV)", "%s %s", (_D, "[MONTH_S]"), True),
    DateFormat("mmm_d", "MMM DD (NOV 04)", "MMM DD (NOV 04)", "%s %s", ("[MONTH_S]", _D), True),
    DateFormat("wd_d_mmm", "Weekday + date (WED, 04 NOV)", "Dia + data (QUA, 04 NOV)", "%s, %s %s",
               ("[DAY_OF_WEEK_S]", _D, "[MONTH_S]"), True),
    DateFormat("wd_short", "Short weekday (WED 04)", "Dia abreviado (QUA 04)", "%s %s",
               ("[DAY_OF_WEEK_S]", _D), True),
    DateFormat("wd_full", "Weekday (Wednesday)", "Dia da semana (quarta-feira)", "%s", ("[DAY_OF_WEEK_F]",)),
    DateFormat("full", "Full date (04 NOVEMBER 2026)", "Data completa (04 NOVEMBRO 2026)", "%s %s %s",
               (_D, "[MONTH_F]", _Y), True),
    DateFormat("hidden", "Hidden", "Oculta", None),
]


def date_options(s: Strings) -> list[tuple[str, str]]:
    return [(d.id, s(f"opt_date_{d.id}", d.label_en, d.label_pt)) for d in DATE_FORMATS]


def date_run(d: DateFormat, color: str, size: float, family: str = "jetbrains_mono_regular",
             before: str = "", after: str = "") -> Run:
    return Run(before + d.template + after, list(d.params), color=color, size=size, family=family, upper=d.upper)


def date_tree(render) -> Node | None:
    """render(date: DateFormat) -> Node ; the 'hidden' option renders nothing."""
    return list_cfg("date_format", {d.id: (render(d) if d.template else None) for d in DATE_FORMATS})


# --------------------------------------------------------------------------- data sources

BATTERY = "[BATTERY_PERCENT]"
BATTERY_FRAC = "clamp([BATTERY_PERCENT] / 100, 0, 1)"
STEPS = "[STEP_COUNT]"
STEP_GOAL = "[STEP_GOAL]"
# Division by zero evaluates to 0 in WFF, so a missing goal yields an empty bar.
STEP_FRAC = "clamp([STEP_COUNT] / [STEP_GOAL], 0, 1)"
def heart(missing: str = '"--"') -> str:
    """Heart rate value; `missing` is shown when the sensor has no reading (never a fake value)."""
    return f'[HEART_RATE] != null ? ([HEART_RATE] > 0 ? [HEART_RATE] : {missing}) : {missing}'


HEART = heart()
HAS_HEART = "[HEART_RATE] != null && [HEART_RATE] > 0"
WEATHER_OK = "[WEATHER.IS_AVAILABLE] && ![WEATHER.IS_ERROR]"
WEATHER_COND = "[WEATHER.CONDITION_NAME]"
DEVICE_STATUS = ('[BATTERY_CHARGING_STATUS] ? "charging" : '
                 '([BATTERY_IS_LOW] ? "low_power" : "running")')


def temperature(unit: str) -> tuple[str, str]:
    """(value expression, unit expression) for unit in auto|c|f.

    WEATHER.TEMPERATURE comes in the unit the user picked on the device
    (WEATHER.TEMPERATURE_UNIT == 1 means Celsius); c/f convert when needed.
    """
    t = "[WEATHER.TEMPERATURE]"
    is_c = "[WEATHER.TEMPERATURE_UNIT] == 1"
    if unit == "c":
        return f"{is_c} ? {t} : round(({t} - 32) * 5 / 9)", '"C"'
    if unit == "f":
        return f"{is_c} ? round({t} * 9 / 5 + 32) : {t}", '"F"'
    return t, f'{is_c} ? "C" : "F"'


def text_bar(frac: str, cells: int, full: str, empty: str) -> tuple[str, str]:
    """Two expressions producing a dynamic text progress bar (filled part, empty part)."""
    filled = f"round({cells} * {frac})"
    return (f'subText("{full * cells}", 0, {filled})',
            f'subText("{empty * cells}", 0, {cells} - {filled})')


# --------------------------------------------------------------------------- shapes

def arc_ring(name: str, cx: float, cy: float, diameter: float, start: float, sweep: float,
             frac: str, color: str, track: str, thickness: float = 8,
             direction: str = "CLOCKWISE") -> Node:
    """Progress arc: a dim track plus a value arc whose end angle follows `frac` (0..1)."""
    sign = 1 if direction == "CLOCKWISE" else -1
    end = start + sign * sweep
    track_arc = E("Arc", [E("Stroke", color=track, thickness=thickness, cap="ROUND")],
                  centerX=cx, centerY=cy, width=diameter, height=diameter,
                  startAngle=start, endAngle=end, direction=direction)
    value_arc = E("Arc", [E("Stroke", color=color, thickness=thickness, cap="ROUND"),
                          E("Transform", target="endAngle",
                            value=f"{start} + {sign * sweep} * {frac}")],
                  centerX=cx, centerY=cy, width=diameter, height=diameter,
                  startAngle=start, endAngle=start, direction=direction)
    return E("PartDraw", [track_arc, value_arc], x=0, y=0, width=CANVAS, height=CANVAS, name=name)


def rect(x, y, w, h, color: str, name: str | None = None, radius: float | None = None) -> Node:
    if radius:
        shape = E("RoundRectangle", [E("Fill", color=color)], x=0, y=0, width=w, height=h,
                  cornerRadiusX=radius, cornerRadiusY=radius)
    else:
        shape = E("Rectangle", [E("Fill", color=color)], x=0, y=0, width=w, height=h)
    return E("PartDraw", [shape], x=round(x), y=round(y), width=round(w), height=round(h), name=name)


def hline(x1, y, x2, color: str, thickness: float = 1, dash: str | None = None) -> Node:
    return E("PartDraw", [E("Line", [E("Stroke", color=color, thickness=thickness, dashIntervals=dash)],
                            startX=0, startY=thickness, endX=x2 - x1, endY=thickness)],
             x=round(x1), y=round(y - thickness), width=round(x2 - x1), height=round(thickness * 2))


def vline(x, y1, y2, color: str, thickness: float = 1, dash: str | None = None) -> Node:
    return E("PartDraw", [E("Line", [E("Stroke", color=color, thickness=thickness, dashIntervals=dash)],
                            startX=thickness, startY=0, endX=thickness, endY=y2 - y1)],
             x=round(x - thickness), y=round(y1), width=round(thickness * 2), height=round(y2 - y1))


def background(color: str) -> Node:
    """Full-screen background; always hidden in ambient so AOD stays pure black."""
    return E("PartDraw", [ambient_hide(),
                          E("Rectangle", [E("Fill", color=color)], x=0, y=0, width=CANVAS, height=CANVAS)],
             x=0, y=0, width=CANVAS, height=CANVAS, name="background")


# --------------------------------------------------------------------------- complications

def complication_slot(slot_id: str, label: str, x, y, w, h, renders: dict[str, Node],
                      default_provider: str, default_type: str, hide_in_ambient: bool = True) -> Node:
    types = " ".join(list(renders.keys()) + ["EMPTY"])
    kids = [
        E("DefaultProviderPolicy", defaultSystemProvider=default_provider, defaultSystemProviderType=default_type),
        E("BoundingBox", x=0, y=0, width=w, height=h),
    ]
    kids += [E("Complication", [r], type=t) for t, r in renders.items()]
    if hide_in_ambient:
        kids.append(ambient_hide())
    return E("ComplicationSlot", kids, slotId=slot_id, name=slot_id, displayName=label,
             supportedTypes=types, x=round(x), y=round(y), width=round(w), height=round(h),
             isCustomizable=True)


# --------------------------------------------------------------------------- document

def watch_face(user_configs: list[Node], scene_children: list[Node], bitmap_fonts: Node | None = None,
               metadata: dict[str, str] | None = None) -> Node:
    meta = [E("Metadata", key=k, value=v) for k, v in (metadata or {}).items()]
    return E("WatchFace", [
        *meta,
        E("UserConfigurations", user_configs),
        bitmap_fonts,
        E("Scene", [c for c in scene_children if c is not None], backgroundColor="#FF000000"),
    ], width=CANVAS, height=CANVAS, clipShape="CIRCLE")


def circle_half_width(y: float, margin: float = 14) -> float:
    """Half the usable chord at height y on the 480 circle (for layout checks)."""
    dy = abs(y - CENTER)
    r = CENTER - margin
    return 0.0 if dy >= r else (r * r - dy * dy) ** 0.5
