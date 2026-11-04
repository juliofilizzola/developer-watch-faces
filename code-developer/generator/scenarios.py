"""Configuration scenarios rendered by scripts/capture.py (tests + store screenshots)."""

SCENARIOS = {
    # Presets (match the Flavors in code_face.py)
    "go_dev": {"config": {"language": "go", "layout": "balanced", "syntax": "vscode", "clock_color": "cyan"},
               "ambient": True},
    "js_dev": {"config": {"language": "js", "layout": "balanced", "syntax": "onedark", "clock_color": "yellow"},
               "ambient": True},
    "vscode_dark": {"config": {"language": "js", "layout": "full", "syntax": "vscode", "bg_color": "editor",
                               "battery_style": "bar", "steps_style": "bar"}},
    "terminal": {"config": {"language": "go", "layout": "compact", "syntax": "terminal", "clock_color": "green",
                            "line_numbers": "FALSE", "text_size": "l"}},
    "minimal_code": {"config": {"language": "go", "layout": "minimal", "syntax": "mono", "line_numbers": "FALSE",
                                "show_chrome": "FALSE", "clock_size": "l"}, "ambient": True},
    "full_stats": {"config": {"language": "go", "layout": "info", "syntax": "dracula", "clock_color": "purple",
                              "battery_style": "ring", "steps_style": "ring", "aod_mode": "full"}, "ambient": True},
    # Feature coverage
    "js_24h_seconds": {"config": {"language": "js", "time_format": "h24", "show_seconds": "TRUE",
                                  "date_format": "iso", "syntax": "monokai", "text_size": "s"}},
    "go_hidden": {"config": {"language": "go", "layout": "balanced", "battery_style": "hidden",
                             "heart_style": "compact", "steps_style": "goal", "syntax": "nord"}},
    "js_icons": {"config": {"language": "js", "layout": "full", "battery_style": "icon", "steps_style": "icon",
                            "heart_style": "icon", "weather_style": "icon", "syntax": "github",
                            "bg_color": "midnight"}},
}

# Isolation tests
SCENARIOS.update({
    "t_github": {"config": {"syntax": "github"}},
    "t_bat_hidden": {"config": {"battery_style": "hidden"}},
    "t_nolines": {"config": {"line_numbers": "FALSE"}},
})

# Shipped defaults (used for res/drawable/preview.png)
SCENARIOS["default"] = {"config": {}, "ambient": True}
