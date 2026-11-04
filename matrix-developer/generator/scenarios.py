"""Configuration scenarios rendered by scripts/capture.py (tests + store screenshots)."""

SCENARIOS = {
    # Presets (match the Flavors in matrix_face.py)
    "classic": {"config": {"layout": "balanced", "rain_density": "medium", "glyph_style": "binary"}, "ambient": True},
    "dark": {"config": {"layout": "balanced", "rain_density": "high", "glyph_style": "hex", "primary": "dark_green",
                        "accent": "green", "intensity": "faint", "glow": "none", "decorations": "FALSE"}},
    "minimal": {"config": {"layout": "minimal", "rain_density": "low", "intensity": "low", "decorations": "FALSE",
                           "clock_size": "l"}, "ambient": True},
    "full_digital": {"config": {"layout": "info", "rain_density": "high", "glyph_style": "symbols",
                                "primary": "phosphor", "accent": "mint", "intensity": "low", "glow": "strong",
                                "battery_style": "ring", "steps_style": "ring", "aod_mode": "full"}, "ambient": True},
    "amoled_green": {"config": {"layout": "compact", "rain_density": "off", "glow": "none", "decorations": "FALSE",
                                "aod_mode": "time"}, "ambient": True},
    # Feature coverage
    "cyan_full_bars": {"config": {"layout": "full", "primary": "cyan", "accent": "cyan", "glow": "cyan",
                                  "battery_style": "bar", "steps_style": "goal", "weather_style": "icon",
                                  "glyph_style": "digits"}},
    "amber_24h_sec": {"config": {"primary": "amber", "accent": "yellow", "glow": "amber", "time_format": "h24",
                                 "show_seconds": "TRUE", "date_format": "full", "intensity": "high"}},
    "red_icons": {"config": {"layout": "full", "primary": "red", "accent": "red", "battery_style": "icon",
                             "steps_style": "icon", "heart_style": "compact", "weather_style": "temp",
                             "intensity": "max"}},
}

# Shipped defaults (used for res/drawable/preview.png)
SCENARIOS["default"] = {"config": {}, "ambient": True}
