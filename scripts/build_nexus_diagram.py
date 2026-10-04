"""Render the looping NEXUS diagram used in the GitHub profile README.

Requires Pillow. The GIF is self-contained so it animates in GitHub Markdown.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "nexus-pipeline.gif"
WIDTH, HEIGHT, SCALE = 960, 360, 2
FRAMES, DURATION_MS = 48, 90

FONT_FILE = Path("/System/Library/Fonts/Avenir Next.ttc")
if not FONT_FILE.exists():
    FONT_FILE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

BG = (20, 28, 31)
PANEL = (30, 42, 44)
PANEL_ACTIVE = (43, 52, 49)
EDGE = (61, 79, 76)
TEXT = (246, 247, 239)
MUTED = (165, 184, 176)
CORAL = (241, 127, 100)
PALE_CORAL = (255, 180, 153)

STAGES = [
    ("01 / INPUT", "Sources", "Postgres · APIs", "Source events"),
    ("02 / CDC", "Capture", "Debezium · Kafka", "Ordered changes"),
    ("03 / MODEL", "Lakehouse", "Databricks · Delta", "Bronze / Silver / Gold"),
    ("04 / TRUST", "Validate", "Contracts · SCD2", "Quality and history"),
    ("05 / SERVE", "Delivery", "Snowflake · SQL", "Client datasets"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILE), size * SCALE, index=0 if bold else 7)


def box(values: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(value * SCALE) for value in values)


def text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str,
         size: int, fill: tuple[int, int, int], bold: bool = False) -> None:
    draw.text((xy[0] * SCALE, xy[1] * SCALE), value,
              font=font(size, bold), fill=fill, anchor="lt")


def blend(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def render(frame_number: int) -> Image.Image:
    progress = frame_number / FRAMES
    pulse_x = 104 + 752 * progress
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)

    # Quiet grid and the same coral thread language as the NEXUS portfolio.
    for x in range(24, WIDTH, 64):
        draw.line(box((x, 0, x, HEIGHT)), fill=(27, 37, 39), width=SCALE)
    for y in range(20, HEIGHT, 64):
        draw.line(box((0, y, WIDTH, y)), fill=(27, 37, 39), width=SCALE)
    points = [(round(x * SCALE), round((112 + 7 * math.sin(x / 92)) * SCALE))
              for x in range(0, WIDTH + 1, 6)]
    draw.line(points, fill=(72, 55, 52), width=2 * SCALE, joint="curve")

    text(draw, (27, 20), "NEXUS", 42, TEXT, True)
    draw.ellipse(box((189, 58, 198, 67)), fill=CORAL)
    text(draw, (27, 75), "DATA PLATFORM IN MOTION", 13, PALE_CORAL, True)
    text(draw, (570, 30), "from source change to trusted decision", 18, TEXT)
    text(draw, (817, 73), "BY VIM", 12, MUTED, True)

    lefts = [25 + 188 * index for index in range(5)]
    centers = [left + 79 for left in lefts]

    # Connectors remain visible between cards even when animation is paused.
    for index in range(4):
        start, end = lefts[index] + 158, lefts[index + 1]
        draw.line(box((start + 1, 207, end - 7, 207)), fill=(99, 113, 105), width=2 * SCALE)
        draw.polygon([(round((end - 6) * SCALE), 207 * SCALE),
                      (round((end - 12) * SCALE), 203 * SCALE),
                      (round((end - 12) * SCALE), 211 * SCALE)], fill=CORAL)

    for index, (eyebrow, title, tech, purpose) in enumerate(STAGES):
        left, center = lefts[index], centers[index]
        intensity = max(0.0, 1.0 - abs(pulse_x - center) / 118)
        panel = blend(PANEL, PANEL_ACTIVE, intensity)
        border = blend(EDGE, CORAL, intensity)
        draw.rounded_rectangle(box((left, 137, left + 158, 278)), radius=15 * SCALE,
                               fill=panel, outline=border, width=2 * SCALE)
        text(draw, (left + 15, 151), eyebrow, 11, blend(MUTED, PALE_CORAL, intensity), True)
        draw.ellipse(box((left + 15, 177, left + 28, 190)), fill=blend(EDGE, CORAL, intensity))
        text(draw, (left + 15, 197), title, 23, TEXT, True)
        text(draw, (left + 15, 231), tech, 14, PALE_CORAL if intensity > .55 else MUTED)
        text(draw, (left + 15, 253), purpose, 11, MUTED)

    draw.line(box((centers[0], 308, centers[-1], 308)), fill=(76, 91, 85), width=3 * SCALE)
    draw.line(box((centers[0], 308, pulse_x, 308)), fill=CORAL, width=3 * SCALE)
    for center in centers:
        draw.line(box((center, 279, center, 307)), fill=(66, 83, 78), width=2 * SCALE)
        draw.ellipse(box((center - 5, 303, center + 5, 313)), fill=CORAL if pulse_x >= center else EDGE)

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for radius, alpha in [(25, 16), (17, 35), (10, 80), (5, 255)]:
        glow_draw.ellipse(box((pulse_x - radius, 308 - radius,
                               pulse_x + radius, 308 + radius)),
                          fill=(*PALE_CORAL, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(image)
    text(draw, (26, 334), "REPLAY SAFE", 11, MUTED, True)
    text(draw, (376, 334), "TRACEABLE  ·  TESTED  ·  TENANT SAFE", 11, MUTED, True)
    text(draw, (822, 334), "PUBLISH", 11, PALE_CORAL, True)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [render(index) for index in range(FRAMES)]
    palette = frames[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(OUTPUT, save_all=True, append_images=indexed[1:], loop=0,
                    duration=DURATION_MS, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes, {FRAMES} frames)")


if __name__ == "__main__":
    main()
