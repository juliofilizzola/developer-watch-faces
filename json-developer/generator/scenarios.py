"""Configuration scenarios rendered by scripts/capture.py (tests + store screenshots)."""

SCENARIOS = {
    # Presets (match the Flavors in json_face.py)
    "developer": {"config": {"layout": "balanced", "json_style": "numbered"}, "ambient": True},
    "clean_json": {"config": {"layout": "minimal", "clock_size": "l", "key_color": "mono", "value_color": "mono",
                              "punct_color": "mono"}, "ambient": True},
    "full_json": {"config": {"layout": "info", "json_style": "guides", "battery_style": "ring",
                             "steps_style": "ring", "key_color": "dracula", "value_color": "dracula",
                             "time_color": "purple", "punct_color": "dracula", "aod_mode": "full"}, "ambient": True},
    "amoled": {"config": {"layout": "compact", "json_style": "bare", "key_color": "mono", "value_color": "mono",
                          "punct_color": "mono", "aod_mode": "time"}, "ambient": True},
    # Feature coverage
    "h24_seconds": {"config": {"time_format": "h24", "show_seconds": "TRUE", "date_format": "dmy"}},
    "h12_ampm_iso": {"config": {"time_format": "h12_ampm", "date_format": "iso", "layout": "compact"}},
    "bars_full": {"config": {"layout": "full", "battery_style": "bar", "steps_style": "bar", "weather_style": "temp",
                             "date_format": "full", "key_color": "monokai", "value_color": "monokai"}},
    "icons": {"config": {"layout": "full", "battery_style": "icon", "steps_style": "icon", "heart_style": "icon",
                         "weather_style": "icon", "key_color": "nord", "value_color": "nord", "punct_color": "nord"}},
    "goal_compact": {"config": {"layout": "info", "steps_style": "goal", "heart_style": "compact",
                                "weather_style": "condition", "date_format": "wd_full", "bg_color": "midnight",
                                "key_color": "github", "value_color": "github"}},
    "size_xl": {"config": {"layout": "minimal", "clock_size": "xl", "time_color": "cyan", "date_format": "d_mmm"}},
    "size_s": {"config": {"layout": "balanced", "clock_size": "s", "time_color": "yellow",
                          "key_color": "gruvbox", "value_color": "gruvbox"}},
}

# Regression scenarios for options that render nothing (hidden / FALSE)
SCENARIOS.update({
    "status_off": {"config": {"show_status": "FALSE"}},
    "battery_hidden": {"config": {"battery_style": "hidden"}},
})

# Shipped defaults (used for res/drawable/preview.png)
SCENARIOS["default"] = {"config": {}, "ambient": True}
