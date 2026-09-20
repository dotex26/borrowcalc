#!/usr/bin/env python3
"""Generate real favicon files.

A data-URI favicon looks tidy but is unreliable: browsers probe /favicon.ico
directly, independently of any <link> tag, and a 404 there makes Chrome fall
back to the generic globe. Real files at stable URLs are what actually work,
and they cache well enough that the extra request is irrelevant.

The mark is the simplified one - percent sign only. At 16x16 the calculator
body and keypad turn to mush, so the favicon keeps just the element people can
actually recognise in a crowded tab bar.
"""
import math
from PIL import Image, ImageDraw

NAVY = (18, 40, 75, 255)
EMERALD = (15, 169, 104, 255)

# Drawn at 8x then downsampled: PIL has no anti-aliasing on shape primitives,
# so supersampling is what keeps the circles and the rotated bar clean.
SS = 8


def rot_rect(cx, cy, w, h, deg):
    """Corners of a rectangle rotated about its centre.

    Image coordinates put y downwards, so a positive angle here tilts the top
    of a vertical bar to the right - which is the direction a '/' slash runs.
    """
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        pts.append((cx + dx * ca - dy * sa, cy + dx * sa + dy * ca))
    return pts


def draw_mark(size):
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = s / 64.0  # design grid is 64x64, same as the SVG

    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=12 * u, fill=NAVY)
    d.ellipse([24 * u - 5 * u, 24 * u - 5 * u, 24 * u + 5 * u, 24 * u + 5 * u], fill=EMERALD)
    d.ellipse([40 * u - 5 * u, 40 * u - 5 * u, 40 * u + 5 * u, 40 * u + 5 * u], fill=EMERALD)
    d.polygon(rot_rect(32 * u, 32 * u, 5 * u, 36 * u, 35), fill=EMERALD)

    return img.resize((size, size), Image.LANCZOS)


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#12284B"/>
<g fill="#0FA968">
<circle cx="24" cy="24" r="5"/>
<circle cx="40" cy="40" r="5"/>
<rect x="29.5" y="14" width="5" height="36" rx="2.5" transform="rotate(35 32 32)"/>
</g>
</svg>
"""


def generate(out_dir):
    import os
    os.makedirs(out_dir, exist_ok=True)
    written = []

    # Multi-resolution .ico: Windows and older browsers pick the size they need.
    ico = os.path.join(out_dir, "favicon.ico")
    draw_mark(48).save(ico, format="ICO",
                       sizes=[(16, 16), (32, 32), (48, 48)])
    written.append(("favicon.ico", os.path.getsize(ico)))

    # Modern browsers prefer the SVG and scale it to any density.
    svg = os.path.join(out_dir, "favicon.svg")
    with open(svg, "w", encoding="utf-8", newline="\n") as f:
        f.write(SVG)
    written.append(("favicon.svg", os.path.getsize(svg)))

    # iOS home-screen icon. iOS ignores SVG and ICO, and renders a screenshot
    # of the page if this is missing.
    ati = os.path.join(out_dir, "apple-touch-icon.png")
    draw_mark(180).save(ati, format="PNG", optimize=True)
    written.append(("apple-touch-icon.png", os.path.getsize(ati)))

    png = os.path.join(out_dir, "icon-512.png")
    draw_mark(512).save(png, format="PNG", optimize=True)
    written.append(("icon-512.png", os.path.getsize(png)))

    return written


if __name__ == "__main__":
    import os
    for name, size in generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")):
        print("  %-22s %6d bytes" % (name, size))
