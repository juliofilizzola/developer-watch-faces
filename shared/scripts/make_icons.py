#!/usr/bin/env python3
"""Draws the DevTime icon set with Pillow.

- Indicator glyphs (white on transparent, tinted at runtime by InlineImage color /
  PartImage tintColor): ic_battery, ic_steps, ic_heart, ic_weather, ic_flame, ic_pin,
  and wx_0..wx_15 condition icons indexed by [WEATHER.CONDITION].
- Product launcher icons (ic_launcher.png per module and 512px store icon).

Usage: python3 shared/scripts/make_icons.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1].parent
SS = 4  # supersampling factor
WHITE = (255, 255, 255, 255)


def canvas(px: int):
    img = Image.new("RGBA", (px * SS, px * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img), SS


def finish(img: Image.Image, px: int) -> Image.Image:
    return img.resize((px, px), Image.LANCZOS)


def battery(px=48):
    img, d, k = canvas(px)
    w = px * k
    d.rounded_rectangle([w * .12, w * .28, w * .80, w * .72], radius=w * .08, outline=WHITE, width=int(w * .07))
    d.rectangle([w * .82, w * .40, w * .90, w * .60], fill=WHITE)
    d.rectangle([w * .22, w * .38, w * .58, w * .62], fill=WHITE)
    return finish(img, px)


def steps(px=48):
    img, d, k = canvas(px)
    w = px * k
    for ox, oy in ((.18, .12), (.52, .40)):
        d.ellipse([w * ox, w * oy, w * (ox + .26), w * (oy + .38)], fill=WHITE)
        d.ellipse([w * (ox + .04), w * (oy + .41), w * (ox + .22), w * (oy + .55)], fill=WHITE)
    return finish(img, px)


def heart(px=48):
    img, d, k = canvas(px)
    w = px * k
    pts = []
    for i in range(200):
        t = 2 * math.pi * i / 200
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((w / 2 + x * w / 38, w * .46 - y * w / 38))
    d.polygon(pts, fill=WHITE)
    return finish(img, px)


def cloud(d, w, ox=0.0, oy=0.0, scale=1.0, fill=WHITE):
    def e(x0, y0, x1, y1):
        d.ellipse([w * (ox + x0 * scale), w * (oy + y0 * scale), w * (ox + x1 * scale), w * (oy + y1 * scale)], fill=fill)
    e(.10, .42, .46, .78)
    e(.30, .26, .70, .66)
    e(.52, .40, .90, .78)
    d.rectangle([w * (ox + .28 * scale), w * (oy + .55 * scale), w * (ox + .72 * scale), w * (oy + .78 * scale)], fill=fill)


def sun(d, w, cx=.5, cy=.5, r=.18, rays=True):
    d.ellipse([w * (cx - r), w * (cy - r), w * (cx + r), w * (cy + r)], fill=WHITE)
    if rays:
        for i in range(8):
            a = i * math.pi / 4
            d.line([w * (cx + math.cos(a) * r * 1.45), w * (cy + math.sin(a) * r * 1.45),
                    w * (cx + math.cos(a) * r * 2.1), w * (cy + math.sin(a) * r * 2.1)], fill=WHITE, width=int(w * .06))


def drops(d, w, n=3, snow=False, y0=.80):
    for i in range(n):
        x = .26 + i * (.48 / max(n - 1, 1))
        if snow:
            d.ellipse([w * (x - .04), w * (y0 + .02), w * (x + .04), w * (y0 + .10)], fill=WHITE)
        else:
            d.line([w * x, w * y0, w * (x - .05), w * (y0 + .14)], fill=WHITE, width=int(w * .05))


def weather_icon(cond: int, px=48):
    img, d, k = canvas(px)
    w = px * k
    if cond in (1, 8):          # clear / sunny
        sun(d, w)
    elif cond == 2:             # cloudy
        cloud(d, w, oy=-.05)
    elif cond in (3, 13):       # fog / mist
        for i, y in enumerate((.36, .52, .68)):
            d.line([w * (.14 + i * .04), w * y, w * (.86 - i * .04), w * y], fill=WHITE, width=int(w * .07))
    elif cond in (4, 6, 12):    # rain variants
        cloud(d, w, oy=-.16)
        drops(d, w, 3 if cond != 4 else 4)
    elif cond in (5, 7, 11):    # snow variants
        cloud(d, w, oy=-.16)
        drops(d, w, 3 if cond != 5 else 4, snow=True)
    elif cond == 9:             # thunderstorm
        cloud(d, w, oy=-.18)
        d.polygon([(w * .52, w * .58), (w * .36, w * .82), (w * .50, w * .80), (w * .42, w * .98),
                   (w * .66, w * .70), (w * .52, w * .72)], fill=WHITE)
    elif cond == 10:            # sleet
        cloud(d, w, oy=-.16)
        drops(d, w, 2)
        d.ellipse([w * .46, w * .84, w * .54, w * .92], fill=WHITE)
    elif cond == 14:            # partly cloudy
        sun(d, w, .36, .36, .14)
        cloud(d, w, ox=.08, oy=.08, scale=.9)
    elif cond == 15:            # windy
        for y, l in ((.34, .70), (.52, .86), (.70, .60)):
            d.arc([w * (l - .22), w * (y - .14), w * (l + .02), w * (y + .02)], 270, 90, fill=WHITE, width=int(w * .06))
            d.line([w * .10, w * (y + .01), w * (l - .10), w * (y + .01)], fill=WHITE, width=int(w * .06))
    else:                       # unknown
        cloud(d, w, oy=-.05)
        d.ellipse([w * .44, w * .44, w * .56, w * .56], fill=(0, 0, 0, 0))
    return finish(img, px)


def generic_weather(px=48):
    img, d, k = canvas(px)
    w = px * k
    sun(d, w, .38, .34, .13)
    cloud(d, w, ox=.06, oy=.10, scale=.9)
    return finish(img, px)


def flame(px=48):
    img, d, k = canvas(px)
    w = px * k
    d.polygon([(w * .5, w * .06), (w * .78, w * .52), (w * .72, w * .82), (w * .5, w * .94),
               (w * .28, w * .82), (w * .22, w * .52), (w * .38, w * .34), (w * .42, w * .52)], fill=WHITE)
    return finish(img, px)


def pin(px=48):
    img, d, k = canvas(px)
    w = px * k
    d.ellipse([w * .24, w * .08, w * .76, w * .60], fill=WHITE)
    d.polygon([(w * .28, w * .46), (w * .72, w * .46), (w * .5, w * .94)], fill=WHITE)
    d.ellipse([w * .41, w * .25, w * .59, w * .43], fill=(0, 0, 0, 0))
    return finish(img, px)


# --------------------------------------------------------------------------- product icons

FONT = ROOT / "json-developer/src/main/res/font/jetbrains_mono_bold.ttf"
PRODUCTS = {
    "json-developer": dict(glyph="{ }", fg=(156, 220, 254), accent=(206, 145, 120)),
    "code-developer": dict(glyph="</>", fg=(86, 156, 214), accent=(220, 220, 170)),
    "matrix-developer": dict(glyph="01", fg=(0, 255, 65), accent=(0, 140, 40)),
}


def product_icon(product: str, px: int, square: bool = False) -> Image.Image:
    """Round launcher icon, or a full-bleed square for Google Play (Play applies its own mask)."""
    cfg = PRODUCTS[product]
    k = 4
    w = px * k
    img = Image.new("RGBA", (w, w), (8, 10, 14, 255) if square else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, w - 1, w - 1], fill=(8, 10, 14, 255))
    d.ellipse([w * .03, w * .03, w * .97, w * .97], outline=cfg["accent"] + (255,), width=int(w * .025))
    if product == "matrix-developer":
        f = ImageFont.truetype(str(FONT), int(w * .085))
        for col in range(9):
            for row in range(10):
                if (col * 7 + row * 3) % 4 == 0:
                    continue
                x = w * (.14 + col * .085)
                y = w * (.08 + row * .09)
                if (x - w / 2) ** 2 + (y - w / 2) ** 2 > (w * .40) ** 2:
                    continue
                a = int(18 + 70 * (row / 10))
                d.text((x, y), "01"[(col + row) % 2], font=f, fill=(0, 255, 65, a))
    f = ImageFont.truetype(str(FONT), int(w * (.34 if len(cfg["glyph"]) > 2 else .40)))
    box = d.textbbox((0, 0), cfg["glyph"], font=f)
    tx = (w - (box[2] - box[0])) / 2 - box[0]
    ty = (w - (box[3] - box[1])) / 2 - box[1]
    d.text((tx, ty), cfg["glyph"], font=f, fill=cfg["fg"] + (255,))
    return img.resize((px, px), Image.LANCZOS)


def main():
    glyphs = {"ic_battery": battery(), "ic_steps": steps(), "ic_heart": heart(), "ic_weather": generic_weather(),
              "ic_flame": flame(), "ic_pin": pin()}
    glyphs.update({f"wx_{i}": weather_icon(i) for i in range(16)})
    for product in PRODUCTS:
        drawable = ROOT / product / "src/main/res/drawable"
        drawable.mkdir(parents=True, exist_ok=True)
        for name, img in glyphs.items():
            img.save(drawable / f"{name}.png")
        product_icon(product, 192).save(drawable / "ic_launcher.png")
        store = ROOT / "store-assets" / product / "icon"
        store.mkdir(parents=True, exist_ok=True)
        product_icon(product, 512, square=True).convert("RGB").save(store / "icon-512.png")
    print("icons written")


if __name__ == "__main__":
    main()
