"""Render a looping, synthetic gameplay preview for the profile README.

The scene follows Pipeline Rush's visual design and actual mechanics: clean
records pass through, duplicates need Dedupe, and corrupt rows are quarantined.
Requires Pillow; run from anywhere with ``python scripts/build_pipeline_rush_preview.py``.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "play" / "pipeline-rush-preview.gif"
WIDTH, HEIGHT, SCALE = 960, 525, 2
FRAMES, DURATION_MS = 60, 100
FONT_FILE = Path("/System/Library/Fonts/Avenir Next.ttc")
if not FONT_FILE.exists():
    FONT_FILE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

BG = (11, 15, 23)
PANEL = (18, 24, 38)
EDGE = (38, 48, 65)
TEXT = (229, 231, 235)
MUTED = (154, 164, 181)
BRONZE = (192, 122, 62)
SILVER = (168, 179, 194)
GOLD = (230, 180, 34)
GREEN = (52, 211, 153)
BLUE = (96, 165, 250)
RED = (248, 113, 113)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILE), size * SCALE, index=0 if bold else 7)


def box(coords: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(value * SCALE) for value in coords)


def label(draw: ImageDraw.ImageDraw, x: float, y: float, value: str, size: int,
          color: tuple[int, int, int] = TEXT, bold: bool = False,
          anchor: str = "lt") -> None:
    draw.text((round(x * SCALE), round(y * SCALE)), value,
              font=font(size, bold), fill=color, anchor=anchor)


def progress(frame: int, start: int, end: int) -> float:
    return min(1, max(0, (frame - start) / (end - start)))


def smooth(value: float) -> float:
    return value * value * (3 - 2 * value)


def card(draw: ImageDraw.ImageDraw, x: float, y: float, number: str,
         state: str = "raw", accent: bool = False) -> None:
    color = {"raw": BLUE, "target": BLUE, "fixed": GREEN,
             "gold": GOLD, "bad": RED}.get(state, BLUE)
    if state == "target" or accent:
        draw.rounded_rectangle(box((x - 41, y - 30, x + 41, y + 30)),
                               radius=10 * SCALE, fill=(35, 55, 79),
                               outline=(55, 99, 150), width=3 * SCALE)
    fill = (33, 41, 60) if state in {"raw", "target"} else (
        (28, 58, 53) if state == "fixed" else
        (57, 48, 29) if state == "gold" else (63, 35, 45))
    draw.rounded_rectangle(box((x - 37, y - 26, x + 37, y + 26)),
                           radius=8 * SCALE, fill=fill, outline=color,
                           width=2 * SCALE)
    cy = y - 9
    if state == "raw":
        draw.ellipse(box((x - 4, cy - 4, x + 4, cy + 4)), fill=color)
    elif state == "target":
        draw.line(box((x - 5, cy - 5, x + 5, cy + 5)), fill=color, width=2 * SCALE)
        draw.line(box((x - 5, cy + 5, x + 5, cy - 5)), fill=color, width=2 * SCALE)
    elif state == "fixed":
        points = [(x - 7, cy), (x - 2, cy + 5), (x + 8, cy - 6)]
        draw.line([(round(px * SCALE), round(py * SCALE)) for px, py in points],
                  fill=color, width=3 * SCALE, joint="curve")
    elif state == "gold":
        draw.polygon([(round(px * SCALE), round(py * SCALE)) for px, py in
                      [(x, cy - 8), (x + 5, cy), (x, cy + 8), (x - 5, cy)]], fill=color)
    else:
        draw.line(box((x, cy - 6, x, cy + 2)), fill=color, width=3 * SCALE)
        draw.ellipse(box((x - 1.5, cy + 5, x + 1.5, cy + 8)), fill=color)
    label(draw, x, y + 12, f"#{number}", 11, TEXT, True, "mm")


def render(frame: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)

    label(draw, 18, 13, "Pipeline", 27, TEXT, True)
    label(draw, 131, 13, "Rush", 27, GOLD, True)
    label(draw, 678, 20, "a tiny data engineering game by @rfim", 12, MUTED)

    # The HUD changes only after successful gameplay events.
    rows = int(frame >= 49) + int(frame >= 57)
    stats = [(18, "ROWS IN GOLD", str(rows)), (253, "DATA QUALITY", "100%"),
             (488, "STAKEHOLDER TRUST", ""), (723, "SLA WINDOW", f"{60 - frame // 10}s")]
    for x, heading, value in stats:
        draw.rounded_rectangle(box((x, 62, x + 219, 133)), radius=10 * SCALE,
                               fill=PANEL, outline=EDGE, width=SCALE)
        label(draw, x + 13, 73, heading, 10, MUTED, True)
        label(draw, x + 13, 93, value, 22, TEXT, True)
    for heart_x in (502, 521, 540):
        heart_y = 109
        draw.ellipse(box((heart_x - 5, heart_y - 6, heart_x + 1, heart_y)), fill=TEXT)
        draw.ellipse(box((heart_x + 1, heart_y - 6, heart_x + 7, heart_y)), fill=TEXT)
        draw.polygon([(round(px * SCALE), round(py * SCALE)) for px, py in
                      [(heart_x - 5, heart_y - 1), (heart_x + 7, heart_y - 1),
                       (heart_x + 1, heart_y + 7)]], fill=TEXT)
    draw.rounded_rectangle(box((736, 117, 926, 123)), radius=3 * SCALE,
                           fill=(43, 51, 67))
    draw.rounded_rectangle(box((736, 117, 736 + (190 - frame // 2), 123)),
                           radius=3 * SCALE, fill=GREEN)

    # Three zones use the same proportions and labels as the playable game.
    draw.rounded_rectangle(box((18, 149, 942, 394)), radius=12 * SCALE,
                           fill=(21, 23, 29), outline=EDGE, width=SCALE)
    draw.rectangle(box((19, 150, 342, 393)), fill=(37, 30, 29))
    draw.rectangle(box((342, 150, 619, 393)), fill=(28, 36, 49))
    draw.rectangle(box((619, 150, 941, 393)), fill=(37, 35, 25))
    for x in (342, 619):
        for y in range(150, 394, 12):
            draw.line(box((x, y, x, min(y + 6, 394))),
                      fill=(101, 110, 126), width=2 * SCALE)
    label(draw, 30, 162, "BRONZE", 14, BRONZE, True)
    label(draw, 30, 184, "raw, untrusted", 12, MUTED)
    label(draw, 354, 162, "SILVER GATE", 14, SILVER, True)
    label(draw, 354, 184, "fix it here", 12, MUTED)
    label(draw, 631, 162, "GOLD", 14, GOLD, True)
    label(draw, 631, 184, "stakeholders look here", 12, MUTED)

    # One clean row; one duplicate repaired in Silver; one bad row quarantined.
    clean_x = 65 + 805 * progress(frame, 0, 52)
    if frame <= 55:
        card(draw, clean_x, 268, "1007", "gold" if clean_x >= 619 else "raw")

    if frame >= 6:
        if frame <= 34:
            duplicate_x = 65 + 438 * smooth(progress(frame, 6, 34))
        elif frame <= 42:
            duplicate_x = 503
        else:
            duplicate_x = 503 + 365 * smooth(progress(frame, 42, 58))
        if frame <= 59:
            duplicate_state = ("raw" if frame < 34 else "target" if frame < 42
                               else "fixed" if duplicate_x < 619 else "gold")
            card(draw, duplicate_x, 334, "1008", duplicate_state,
                 accent=34 <= frame < 42)

    if frame >= 14:
        if frame <= 48:
            bad_x = 65 + 478 * smooth(progress(frame, 14, 48))
            bad_y = 235
        else:
            bad_x = 543
            bad_y = 235 + 75 * smooth(progress(frame, 52, 56))
        if frame < 56:
            card(draw, bad_x, bad_y, "1009",
                 "raw" if frame < 48 else "bad", accent=48 <= frame < 53)
        else:
            draw.rounded_rectangle(box((468, 342, 606, 372)), radius=7 * SCALE,
                                   fill=(63, 35, 45), outline=RED, width=SCALE)
            label(draw, 537, 350, "QUARANTINED", 12, RED, True, "mt")

    action_titles = [("D", "Dedupe"), ("N", "Backfill"),
                     ("S", "Cast"), ("P", "Mask"), ("Q", "Quarantine")]
    for index, (key, title) in enumerate(action_titles):
        x = 18 + index * 187
        active = (index == 0 and 34 <= frame <= 43) or (index == 4 and 50 <= frame <= 58)
        draw.rounded_rectangle(box((x, 408, x + 176, 474)), radius=9 * SCALE,
                               fill=(28, 47, 58) if active else PANEL,
                               outline=GREEN if active else EDGE,
                               width=(2 if active else 1) * SCALE)
        label(draw, x + 88, 418, title, 14, TEXT, True, "mt")
        draw.rounded_rectangle(box((x + 76, 447, x + 100, 468)),
                               radius=4 * SCALE, fill=(12, 17, 28),
                               outline=BLUE if active else EDGE, width=SCALE)
        label(draw, x + 88, 452, key, 12, BLUE, True, "mt")

    if frame < 33:
        message = "Keep clean records moving. Catch bad data at the Silver gate."
    elif frame < 42:
        message = "Duplicate #1008 detected  >  Dedupe [D]"
    elif frame < 49:
        message = "#1008 deduplicated and cleared for Gold"
    elif frame < 57:
        message = "Corrupt #1009 detected  >  Quarantine [Q]"
    else:
        message = "#1009 held safely. Stakeholder trust intact."
    label(draw, 20, 489, message, 14, GREEN if frame >= 42 else MUTED)
    label(draw, 764, 492, "PLAY THE GAME  >", 11, BLUE, True)

    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main() -> None:
    frames = [render(frame) for frame in range(FRAMES)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   duration=DURATION_MS, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT}: {FRAMES} frames, {OUTPUT.stat().st_size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
