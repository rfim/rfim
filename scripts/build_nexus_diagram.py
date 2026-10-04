"""Build the NEXUS profile GIF: valid rows publish; one exception is repaired.

The scene uses synthetic events. Requires Pillow. GitHub animates the GIF in the
profile README; the first frame is also a legible static architecture diagram.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "nexus-data-rescue.gif"
WIDTH, HEIGHT, SCALE = 960, 430, 2
FRAMES, DURATION_MS = 72, 90

FONT_FILE = Path("/System/Library/Fonts/Avenir Next.ttc")
if not FONT_FILE.exists():
    FONT_FILE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

BG = (20, 28, 31)
PANEL = (30, 42, 44)
PANEL_ACTIVE = (42, 54, 49)
EDGE = (61, 79, 76)
TEXT = (246, 247, 239)
MUTED = (165, 184, 176)
CORAL = (241, 127, 100)
PALE_CORAL = (255, 180, 153)
GREEN = (149, 220, 177)

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


def between(frame: int, start: int, end: int) -> float:
    return min(1.0, max(0.0, (frame - start) / (end - start)))


def ease(amount: float) -> float:
    return amount * amount * (3 - 2 * amount)


def record_positions(frame: int) -> list[tuple[float, float, str, tuple[int, int, int]]]:
    """Two valid rows continue; an invalid row branches, repairs, and replays."""
    result: list[tuple[float, float, str, tuple[int, int, int]]] = []
    if frame <= 48:
        result.append((104 + 752 * between(frame, 0, 45), 313, "A", GREEN))
    if 10 <= frame <= 65:
        result.append((104 + 752 * between(frame, 10, 62), 313, "B", GREEN))
    if frame >= 6:
        if frame <= 38:
            x, y = 104 + 564 * between(frame, 6, 38), 313
        elif frame <= 46:
            x, y = 668, 313 + 65 * ease(between(frame, 38, 46))
        elif frame <= 51:
            x, y = 668, 378
        elif frame <= 57:
            x, y = 668, 378 - 65 * ease(between(frame, 51, 57))
        else:
            x, y = 668 + 188 * between(frame, 57, 67), 313
        repaired = frame > 51
        result.append((x, y, "R" if repaired else "!", GREEN if repaired else CORAL))
    return result


def draw_record(image: Image.Image, x: float, y: float, name: str,
                color: tuple[int, int, int]) -> Image.Image:
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for radius, alpha in [(23, 16), (16, 35), (11, 75)]:
        glow_draw.ellipse(box((x - radius, y - radius, x + radius, y + radius)),
                          fill=(*color, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.ellipse(box((x - 10, y - 10, x + 10, y + 10)), fill=color,
                 outline=TEXT, width=SCALE)
    draw.text((x * SCALE, (y - 1) * SCALE), name, font=font(11, True),
              fill=BG, anchor="mm")
    return image


def render(frame: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)
    records = record_positions(frame)

    for x in range(24, WIDTH, 64):
        draw.line(box((x, 0, x, HEIGHT)), fill=(27, 37, 39), width=SCALE)
    for y in range(20, HEIGHT, 64):
        draw.line(box((0, y, WIDTH, y)), fill=(27, 37, 39), width=SCALE)
    thread = [(round(x * SCALE), round((112 + 7 * math.sin(x / 92)) * SCALE))
              for x in range(0, WIDTH + 1, 6)]
    draw.line(thread, fill=(72, 55, 52), width=2 * SCALE, joint="curve")

    text(draw, (27, 20), "NEXUS", 42, TEXT, True)
    draw.ellipse(box((189, 58, 198, 67)), fill=CORAL)
    text(draw, (27, 75), "ONE BAD ROW. NO BLOCKED BATCH.", 13, PALE_CORAL, True)
    text(draw, (603, 28), "from source change to trusted decision", 16, TEXT)
    draw.ellipse(box((758, 75, 767, 84)), fill=GREEN)
    text(draw, (773, 71), "VALID", 11, MUTED, True)
    draw.ellipse(box((843, 75, 852, 84)), fill=CORAL)
    text(draw, (858, 71), "EXCEPTION", 11, MUTED, True)

    lefts = [25 + 188 * index for index in range(5)]
    centers = [left + 79 for left in lefts]
    for index in range(4):
        start, end = lefts[index] + 158, lefts[index + 1]
        draw.line(box((start + 1, 207, end - 7, 207)), fill=(99, 113, 105), width=2 * SCALE)
        draw.polygon([(round((end - 6) * SCALE), 207 * SCALE),
                      (round((end - 12) * SCALE), 203 * SCALE),
                      (round((end - 12) * SCALE), 211 * SCALE)], fill=CORAL)

    for index, (eyebrow, title, tech, purpose) in enumerate(STAGES):
        left, center = lefts[index], centers[index]
        intensity = max((max(0.0, 1.0 - abs(x - center) / 110)
                         for x, y, _, _ in records if y == 313), default=0.0)
        if index == 3 and 38 <= frame <= 57:
            intensity = max(intensity, .65)
        draw.rounded_rectangle(box((left, 137, left + 158, 278)), radius=15 * SCALE,
                               fill=blend(PANEL, PANEL_ACTIVE, intensity),
                               outline=blend(EDGE, CORAL, intensity), width=2 * SCALE)
        text(draw, (left + 15, 151), eyebrow, 11, blend(MUTED, PALE_CORAL, intensity), True)
        draw.ellipse(box((left + 15, 177, left + 28, 190)),
                     fill=blend(EDGE, CORAL, intensity))
        text(draw, (left + 15, 197), title, 23, TEXT, True)
        text(draw, (left + 15, 231), tech, 14, PALE_CORAL if intensity > .55 else MUTED)
        text(draw, (left + 15, 253), purpose, 11, MUTED)

    draw.line(box((centers[0], 313, centers[-1], 313)),
              fill=(82, 101, 92), width=3 * SCALE)
    for center in centers:
        draw.line(box((center, 279, center, 302)), fill=(66, 83, 78), width=2 * SCALE)
        draw.ellipse(box((center - 4, 309, center + 4, 317)), fill=EDGE)

    # An exception branches at validation. The next valid row keeps moving.
    draw.line(box((668, 314, 668, 357)), fill=(139, 81, 72), width=2 * SCALE)
    draw.polygon([(668 * SCALE, 359 * SCALE), (662 * SCALE, 351 * SCALE),
                  (674 * SCALE, 351 * SCALE)], fill=CORAL)
    draw.rounded_rectangle(box((572, 359, 762, 405)), radius=10 * SCALE,
                           fill=(43, 42, 40), outline=CORAL, width=2 * SCALE)
    text(draw, (585, 367), "QUARANTINE", 12, PALE_CORAL, True)
    if frame < 38:
        reason = "Exceptions retain their reason"
    elif frame <= 51:
        reason = "1 row held / reason kept"
    else:
        reason = "Corrected event replays"
    text(draw, (585, 386), reason, 11, MUTED)

    published = int(frame >= 45) + int(frame >= 62) + int(frame >= 67)
    draw.rounded_rectangle(box((793, 359, 936, 405)), radius=10 * SCALE,
                           fill=(35, 49, 45), outline=GREEN, width=2 * SCALE)
    text(draw, (806, 367), "PUBLISHED", 12, GREEN, True)
    text(draw, (806, 385), f"{published} clean records", 12, TEXT)

    for x, y, name, color in records:
        image = draw_record(image, x, y, name, color)

    draw = ImageDraw.Draw(image)
    text(draw, (26, 411), "GOOD ROWS CONTINUE", 11, MUTED, True)
    text(draw, (375, 411), "EXCEPTIONS WAIT / REPLAY IS SAFE", 11, MUTED, True)
    text(draw, (850, 411), "BY VIM", 11, PALE_CORAL, True)
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
