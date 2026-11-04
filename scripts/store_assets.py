#!/usr/bin/env python3
"""Builds the Google Play assets from real runtime captures (reports/screens, see scripts/capture.py).

store-assets/<face>/
  screenshots/      OFFICIAL: unmodified 480x480 captures of the WFF runtime (1:1, no device frame)
  feature-graphic/  1024x500 promotional banner (composited from real captures)
  promotional/      marketing images, always prefixed promo-* (never upload as screenshots)
  icon/             512x512 store icon (written by shared/scripts/make_icons.py)

Usage: python3 scripts/store_assets.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "reports/screens"
OUT = ROOT / "store-assets"
FONT_BOLD = ROOT / "json-developer/src/main/res/font/jetbrains_mono_bold.ttf"
FONT_REG = ROOT / "json-developer/src/main/res/font/jetbrains_mono_regular.ttf"

# Official screenshots per product, in store order: (capture name, caption used only in docs)
SCREENSHOTS = {
    "json-developer": [
        ("developer", "Developer preset"), ("full_json", "Full JSON with rings"), ("clean_json", "Clean JSON"),
        ("bars_full", "Progress bars + full date"), ("icons", "Icons + Nord palette"),
        ("h24_seconds", "24h with seconds"), ("developer-aod", "Always-on display"),
        ("full_json-aod", "Always-on with stats")],
    "code-developer": [
        ("go_dev", "Go Developer"), ("js_dev", "JavaScript Developer"), ("vscode_dark", "VS Code Dark"),
        ("terminal", "Terminal"), ("full_stats", "Full Stats with rings"), ("minimal_code", "Minimal Code"),
        ("go_dev-aod", "Always-on display"), ("full_stats-aod", "Always-on with stats")],
    "matrix-developer": [
        ("classic", "Classic Matrix"), ("full_digital", "Full Digital"), ("dark", "Dark Matrix"),
        ("minimal", "Minimal Matrix"), ("cyan_full_bars", "Cyber cyan + bars"), ("amber_24h_sec", "Amber 24h"),
        ("classic-aod", "Always-on display"), ("full_digital-aod", "Always-on with stats")],
}
BRAND = {
    "json-developer": dict(name="JSON Developer", tagline="Your day, pretty-printed.", accent=(156, 220, 254),
                           hero=["developer", "full_json", "clean_json"]),
    "code-developer": dict(name="Code Developer", tagline="Go or JavaScript. Time compiles.", accent=(86, 156, 214),
                           hero=["go_dev", "js_dev", "full_stats"]),
    "matrix-developer": dict(name="Matrix Developer", tagline="Digital rain. Real data.", accent=(0, 255, 65),
                             hero=["classic", "full_digital", "cyan_full_bars"]),
}


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size)


def round_shot(name: str, product: str, size: int) -> Image.Image:
    img = Image.open(SHOTS / product / f"{name}.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def bezel(img: Image.Image, accent) -> Image.Image:
    """Thin accent ring + soft glow around a round capture (promotional styling only)."""
    pad = 14
    size = img.width + pad * 2
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([4, 4, size - 5, size - 5], outline=accent + (120,), width=6)
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(out).ellipse([pad - 3, pad - 3, size - pad + 2, size - pad + 2], fill=(18, 18, 22, 255))
    out.alpha_composite(img, (pad, pad))
    ImageDraw.Draw(out).ellipse([pad - 3, pad - 3, size - pad + 2, size - pad + 2], outline=accent + (200,), width=2)
    return out


def backdrop(w: int, h: int, accent) -> Image.Image:
    bg = Image.new("RGBA", (w, h), (6, 8, 12, 255))
    texture = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(texture)
    f = font(14, bold=False)
    for y in range(0, h, 22):          # faint code texture, blended (not written) onto the background
        for x in range(0, w, 120):
            d.text((x + (y * 7) % 60, y), "0x{:04X}".format((x * 31 + y * 17) % 65535), font=f,
                   fill=accent + (22,))
    bg.alpha_composite(texture)
    vignette = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vignette).ellipse([-w * 0.2, -h * 0.6, w * 1.2, h * 1.6], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(80))
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    return Image.composite(bg, dark, vignette)


def feature_graphic(product: str) -> Image.Image:
    b = BRAND[product]
    img = backdrop(1024, 500, b["accent"])
    d = ImageDraw.Draw(img)
    d.text((50, 160), b["name"], font=font(44), fill=(245, 245, 245, 255))
    d.text((52, 225), b["tagline"], font=font(22, bold=False), fill=b["accent"] + (255,))
    d.text((52, 290), "Wear OS · Galaxy Watch · AMOLED", font=font(17, bold=False), fill=(150, 150, 160, 255))
    d.text((52, 318), "Always-on · presets · deep customization", font=font(17, bold=False),
           fill=(150, 150, 160, 255))
    big = bezel(round_shot(b["hero"][0], product, 290), b["accent"])
    small = bezel(round_shot(b["hero"][1], product, 168), b["accent"])
    img.alpha_composite(big, (508, 91))
    img.alpha_composite(small, (826, 166))
    return img.convert("RGB")


def promo_presets(product: str) -> Image.Image:
    """Preset comparison: every official screenshot with its caption."""
    b = BRAND[product]
    items = [i for i in SCREENSHOTS[product] if not i[0].endswith("-aod")][:6]
    w, h = 1600, 1000
    img = backdrop(w, h, b["accent"])
    d = ImageDraw.Draw(img)
    d.text((60, 40), f"{b['name']} · presets & customization", font=font(44), fill=(245, 245, 245, 255))
    for i, (name, caption) in enumerate(items):
        col, row = i % 3, i // 3
        x, y = 90 + col * 500, 150 + row * 420
        img.alpha_composite(bezel(round_shot(name, product, 320), b["accent"]), (x, y))
        d.text((x + 174, y + 365), caption, font=font(22, bold=False), fill=(210, 210, 220, 255), anchor="mm")
    return img.convert("RGB")


def promo_aod(product: str) -> Image.Image:
    b = BRAND[product]
    pairs = [i[0] for i in SCREENSHOTS[product] if i[0].endswith("-aod")]
    w, h = 1600, 900
    img = backdrop(w, h, b["accent"])
    d = ImageDraw.Draw(img)
    d.text((60, 40), "Active  →  Always-on display", font=font(44), fill=(245, 245, 245, 255))
    for i, aod in enumerate(pairs[:2]):
        active = aod.removesuffix("-aod")
        y = 150 + i * 360
        img.alpha_composite(bezel(round_shot(active, product, 320), b["accent"]), (260, y - 10))
        d.text((730, y + 150), "→", font=font(80), fill=b["accent"] + (255,), anchor="mm")
        img.alpha_composite(bezel(round_shot(aod, product, 320), (120, 120, 120)), (880, y - 10))
    d.text((60, h - 60), "AOD hides decoration and seconds, keeps the identity, stays mostly black.",
           font=font(22, bold=False), fill=(170, 170, 180, 255))
    return img.convert("RGB")


def collection() -> Image.Image:
    w, h = 1600, 900
    img = backdrop(w, h, (120, 200, 255))
    d = ImageDraw.Draw(img)
    d.text((w / 2, 90), "DevTime Watch Faces", font=font(64), fill=(245, 245, 245, 255), anchor="mm")
    d.text((w / 2, 160), "Three premium watch faces for developers", font=font(28, bold=False),
           fill=(170, 200, 230, 255), anchor="mm")
    for i, product in enumerate(BRAND):
        b = BRAND[product]
        x = 110 + i * 480
        img.alpha_composite(bezel(round_shot(b["hero"][0], product, 380), b["accent"]), (x, 250))
        d.text((x + 204, 690), b["name"], font=font(30), fill=b["accent"] + (255,), anchor="mm")
        d.text((x + 204, 735), b["tagline"], font=font(20, bold=False), fill=(190, 190, 200, 255), anchor="mm")
    return img.convert("RGB")


def indicators() -> Image.Image:
    """Indicator showcase: crops of the same real data rendered by each face."""
    w, h = 1600, 900
    img = backdrop(w, h, (120, 200, 255))
    d = ImageDraw.Draw(img)
    d.text((60, 40), "Real data, three dialects", font=font(48), fill=(245, 245, 245, 255))
    d.text((60, 110), "Battery · steps & goal · heart rate · weather · complications (calories, distance…)",
           font=font(22, bold=False), fill=(170, 170, 180, 255))
    for i, (product, shot) in enumerate((("json-developer", "icons"), ("code-developer", "full_stats"),
                                         ("matrix-developer", "full_digital"))):
        x = 80 + i * 500
        img.alpha_composite(bezel(round_shot(shot, product, 420), BRAND[product]["accent"]), (x, 200))
        d.text((x + 224, 690), BRAND[product]["name"], font=font(26), fill=BRAND[product]["accent"] + (255,),
               anchor="mm")
    d.text((60, h - 70), "Values come from the watch (WFF data sources / complications). No data → null, -- or NO SIGNAL.",
           font=font(20, bold=False), fill=(150, 150, 160, 255))
    return img.convert("RGB")


def main():
    missing = []
    for product, items in SCREENSHOTS.items():
        base = OUT / product
        shots = base / "screenshots"
        if shots.exists():
            shutil.rmtree(shots)
        shots.mkdir(parents=True)
        for i, (name, _) in enumerate(items, start=1):
            src = SHOTS / product / f"{name}.png"
            if not src.exists():
                missing.append(str(src))
                continue
            shutil.copy(src, shots / f"{i:02d}-{name}.png")
        (base / "feature-graphic").mkdir(parents=True, exist_ok=True)
        feature_graphic(product).save(base / "feature-graphic" / "feature-graphic-1024x500.png")
        promo = base / "promotional"
        promo.mkdir(parents=True, exist_ok=True)
        promo_presets(product).save(promo / "promo-presets.png")
        promo_aod(product).save(promo / "promo-always-on.png")
    shared = OUT / "collection"
    shared.mkdir(parents=True, exist_ok=True)
    collection().save(shared / "promo-collection.png")
    indicators().save(shared / "promo-indicators.png")
    if missing:
        print("missing captures (run ./build-all.sh screenshots):")
        print("\n".join("  " + m for m in missing))
        raise SystemExit(1)
    print("store assets written to", OUT)


if __name__ == "__main__":
    main()
