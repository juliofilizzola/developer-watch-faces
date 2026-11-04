"""DevTime design system: editor color palettes shared by the collection.

Colors are #AARRGGBB. Every palette is AMOLED-safe (no large bright fills) and meets
>= 4.5:1 contrast for text against pure black. See shared/design-system/README.md.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    id: str
    en: str
    pt: str
    key: str        # JSON keys / identifiers
    string: str     # string literals
    number: str     # numeric literals
    keyword: str    # language keywords (func, const, package)
    func: str       # function / type names
    comment: str    # comments, gutter, secondary text
    punct: str      # braces, colons, commas
    time: str       # hero clock


PALETTES = [
    Palette("vscode", "VS Code Dark+", "VS Code Dark+", "#FF9CDCFE", "#FFCE9178", "#FFB5CEA8",
            "#FF569CD6", "#FFDCDCAA", "#FF6A9955", "#FFA0A0A0", "#FFFFFFFF"),
    Palette("dracula", "Dracula", "Dracula", "#FF8BE9FD", "#FFF1FA8C", "#FFBD93F9",
            "#FFFF79C6", "#FF50FA7B", "#FF7A88B8", "#FFC0C0D0", "#FFF8F8F2"),
    Palette("monokai", "Monokai", "Monokai", "#FF66D9EF", "#FFE6DB74", "#FFAE81FF",
            "#FFF92672", "#FFA6E22E", "#FF8F8A75", "#FFC8C8C2", "#FFF8F8F2"),
    Palette("onedark", "One Dark", "One Dark", "#FFE06C75", "#FF98C379", "#FFD19A66",
            "#FFC678DD", "#FF61AFEF", "#FF7F848E", "#FFABB2BF", "#FFFFFFFF"),
    Palette("github", "GitHub Dark", "GitHub Dark", "#FF79C0FF", "#FFA5D6FF", "#FF79C0FF",
            "#FFFF7B72", "#FFD2A8FF", "#FF8B949E", "#FFC9D1D9", "#FFF0F6FC"),
    Palette("nord", "Nord", "Nord", "#FF88C0D0", "#FFA3BE8C", "#FFB48EAD",
            "#FF81A1C1", "#FF8FBCBB", "#FF7B88A1", "#FFD8DEE9", "#FFECEFF4"),
    Palette("solarized", "Solarized", "Solarized", "#FF268BD2", "#FF2AA198", "#FFD33682",
            "#FF859900", "#FFB58900", "#FF839496", "#FF93A1A1", "#FFFDF6E3"),
    Palette("gruvbox", "Gruvbox", "Gruvbox", "#FF83A598", "#FFB8BB26", "#FFD3869B",
            "#FFFB4934", "#FFFABD2F", "#FFA89984", "#FFD5C4A1", "#FFFBF1C7"),
    Palette("terminal", "Terminal Green", "Terminal verde", "#FF39FF14", "#FFB6FFB0", "#FF7CFC00",
            "#FF00E676", "#FFCCFF90", "#FF2E8B57", "#FF66BB6A", "#FF39FF14"),
    Palette("amber", "Amber CRT", "Âmbar CRT", "#FFFFB000", "#FFFFD27F", "#FFFFC14D",
            "#FFFF8C00", "#FFFFE0A3", "#FFB07A1F", "#FFCC8E35", "#FFFFB000"),
    Palette("mono", "Monochrome", "Monocromático", "#FFE0E0E0", "#FFFFFFFF", "#FFFFFFFF",
            "#FFBDBDBD", "#FFF5F5F5", "#FF8A8A8A", "#FF9E9E9E", "#FFFFFFFF"),
]

PALETTE_BY_ID = {p.id: p for p in PALETTES}

# Single accent colors offered for the hero clock and highlights.
ACCENTS = [
    ("white", "White", "Branco", "#FFFFFFFF"),
    ("cyan", "Cyan", "Ciano", "#FF4FC3F7"),
    ("blue", "Blue", "Azul", "#FF569CD6"),
    ("green", "Green", "Verde", "#FF4EE07B"),
    ("matrix", "Matrix green", "Verde matrix", "#FF00FF41"),
    ("yellow", "Yellow", "Amarelo", "#FFFFD54F"),
    ("orange", "Orange", "Laranja", "#FFFF9E40"),
    ("pink", "Pink", "Rosa", "#FFFF79C6"),
    ("purple", "Purple", "Roxo", "#FFBD93F9"),
    ("red", "Red", "Vermelho", "#FFFF5370"),
]

BACKGROUNDS = [
    ("black", "AMOLED black", "Preto AMOLED", "#FF000000"),
    ("graphite", "Graphite", "Grafite", "#FF101010"),
    ("editor", "Editor gray", "Cinza editor", "#FF1E1E1E"),
    ("midnight", "Midnight blue", "Azul meia-noite", "#FF0D1117"),
    ("deep_green", "Deep green", "Verde profundo", "#FF00110A"),
]
