"""Render a synthetic NEXUS Cortex chat storyboard for the profile README.

This is an illustration of a proposed semantic interface, not a live chatbot.
Run with Pillow: python scripts/build_nexus_cortex.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "nexus-cortex-agumon.gif"
WIDTH, HEIGHT, SCALE = 960, 520, 2
FRAMES, DURATION_MS = 78, 95
FONT_FILE = Path("/System/Library/Fonts/Avenir Next.ttc")
if not FONT_FILE.exists():
    FONT_FILE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

BG = (12, 18, 29)
PANEL = (21, 30, 44)
PANEL_2 = (27, 39, 55)
EDGE = (54, 71, 89)
TEXT = (239, 245, 247)
MUTED = (164, 181, 195)
CYAN = (103, 218, 229)
GREEN = (144, 222, 173)
AMBER = (247, 191, 111)
ORANGE = (246, 137, 62)
ORANGE_LIGHT = (255, 181, 91)
CREAM = (255, 228, 176)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILE), size * SCALE, index=0 if bold else 7)


def xy(values: tuple[float, ...]) -> tuple[int, ...]:
    return tuple(round(value * SCALE) for value in values)


def label(draw: ImageDraw.ImageDraw, x: float, y: float, value: str,
          size: int, color: tuple[int, int, int] = TEXT,
          bold: bool = False) -> None:
    draw.text(xy((x, y)), value, font=font(size, bold), fill=color, anchor="lt")


def rounded(draw: ImageDraw.ImageDraw, bounds: tuple[float, float, float, float],
            fill: tuple[int, int, int], outline: tuple[int, int, int] = EDGE,
            radius: int = 12, width: int = 1) -> None:
    draw.rounded_rectangle(xy(bounds), radius=radius * SCALE, fill=fill,
                           outline=outline, width=width * SCALE)


def polygon(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]],
            fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None) -> None:
    draw.polygon([xy(point) for point in points], fill=fill)
    if outline:
        draw.line([xy(point) for point in points + [points[0]]],
                  fill=outline, width=2 * SCALE, joint="curve")


def progress(frame: int, start: int, end: int) -> float:
    return min(1.0, max(0.0, (frame - start) / (end - start)))


def typed(value: str, frame: int, start: int, end: int) -> str:
    return value[:round(len(value) * progress(frame, start, end))]


def agumon(draw: ImageDraw.ImageDraw, frame: int) -> None:
    """Draw an original, simplified orange dinosaur fan sketch."""
    bob = math.sin(frame * .22) * 3
    blink = frame % 43 in (29, 30)
    pulse = 4 + 5 * (0.5 + 0.5 * math.sin(frame * .32))

    draw.ellipse(xy((56 - pulse, 111 - pulse, 250 + pulse, 305 + pulse)),
                 outline=(42, 91, 103), width=2 * SCALE)
    draw.ellipse(xy((69, 124, 237, 292)), fill=(29, 62, 73))
    draw.ellipse(xy((90, 386, 218, 403)), fill=(11, 17, 25))

    # Tail and compact body sit behind the large head.
    polygon(draw, [(122, 312 + bob), (85, 319 + bob), (59, 301 + bob),
                   (76, 343 + bob), (121, 356 + bob)], ORANGE, (181, 85, 41))
    draw.ellipse(xy((108, 293 + bob, 213, 388 + bob)), fill=ORANGE,
                 outline=(181, 85, 41), width=2 * SCALE)
    draw.ellipse(xy((135, 314 + bob, 198, 374 + bob)), fill=CREAM)
    polygon(draw, [(111, 357 + bob), (100, 374 + bob), (116, 382 + bob),
                   (136, 376 + bob), (143, 351 + bob)], ORANGE, (181, 85, 41))
    polygon(draw, [(183, 351 + bob), (192, 379 + bob), (212, 386 + bob),
                   (223, 377 + bob), (211, 353 + bob)], ORANGE, (181, 85, 41))

    # A friendly, distinct fan-art silhouette: round eyes, broad snout, little teeth.
    polygon(draw, [(97, 195 + bob), (87, 154 + bob), (115, 171 + bob),
                   (136, 126 + bob), (146, 169 + bob), (180, 123 + bob),
                   (188, 172 + bob), (214, 154 + bob), (212, 195 + bob)],
            ORANGE, (181, 85, 41))
    draw.ellipse(xy((81, 168 + bob, 231, 311 + bob)), fill=ORANGE,
                 outline=(181, 85, 41), width=2 * SCALE)
    draw.ellipse(xy((104, 241 + bob, 229, 315 + bob)), fill=CREAM,
                 outline=(189, 120, 71), width=2 * SCALE)
    draw.ellipse(xy((110, 196 + bob, 153, 244 + bob)), fill=TEXT)
    draw.ellipse(xy((169, 196 + bob, 212, 244 + bob)), fill=TEXT)
    if blink:
        draw.line(xy((118, 223 + bob, 146, 223 + bob)), fill=(35, 42, 52), width=4 * SCALE)
        draw.line(xy((177, 223 + bob, 205, 223 + bob)), fill=(35, 42, 52), width=4 * SCALE)
    else:
        draw.ellipse(xy((123, 205 + bob, 146, 237 + bob)), fill=(39, 88, 77))
        draw.ellipse(xy((180, 205 + bob, 203, 237 + bob)), fill=(39, 88, 77))
        draw.ellipse(xy((128, 207 + bob, 134, 215 + bob)), fill=TEXT)
        draw.ellipse(xy((185, 207 + bob, 191, 215 + bob)), fill=TEXT)
    draw.ellipse(xy((151, 261 + bob, 160, 269 + bob)), fill=(112, 71, 50))
    draw.ellipse(xy((190, 261 + bob, 199, 269 + bob)), fill=(112, 71, 50))
    draw.arc(xy((141, 265 + bob, 209, 302 + bob)), 8, 168,
             fill=(112, 71, 50), width=3 * SCALE)
    polygon(draw, [(152, 291 + bob), (158, 302 + bob), (164, 291 + bob)], TEXT)
    polygon(draw, [(186, 292 + bob), (192, 303 + bob), (198, 290 + bob)], TEXT)
    label(draw, 77, 417, "AGUMON", 18, ORANGE_LIGHT, True)
    label(draw, 77, 441, "semantic guide · concept", 11, MUTED)


def draw_card(draw: ImageDraw.ImageDraw, x: int, title: str, detail: str,
              color: tuple[int, int, int], active: bool) -> None:
    rounded(draw, (x, 199, x + 183, 270), PANEL_2 if active else PANEL,
            color if active else EDGE, 10, 2 if active else 1)
    label(draw, x + 12, 211, title, 11, color, True)
    label(draw, x + 12, 235, detail, 13, TEXT if active else MUTED, True)


def render(frame: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)
    for gx in range(0, WIDTH, 48):
        draw.line(xy((gx, 0, gx, HEIGHT)), fill=(18, 27, 40), width=SCALE)
    for gy in range(0, HEIGHT, 48):
        draw.line(xy((0, gy, WIDTH, gy)), fill=(18, 27, 40), width=SCALE)

    label(draw, 21, 13, "NEXUS", 29, TEXT, True)
    label(draw, 132, 13, "CORTEX", 29, CYAN, True)
    label(draw, 21, 54, "A governed answer, with receipts.", 15, MUTED)
    label(draw, 758, 25, "SYNTHETIC STORYBOARD", 11, AMBER, True)

    rounded(draw, (20, 88, 303, 466), PANEL, EDGE, 15)
    agumon(draw, frame)

    rounded(draw, (322, 88, 940, 466), PANEL, EDGE, 15)
    label(draw, 343, 101, "YOU ASK", 11, CYAN, True)
    rounded(draw, (342, 126, 919, 181), PANEL_2, EDGE, 10)
    question = "How many paid orders did Aurora have last week?"
    label(draw, 357, 140, typed(question, frame, 0, 11), 18, TEXT, True)
    if frame < 11 and frame % 4 < 2:
        cursor_x = 357 + draw.textlength(typed(question, frame, 0, 11), font=font(18, True)) / SCALE
        draw.line(xy((cursor_x + 2, 141, cursor_x + 2, 164)), fill=CYAN, width=2 * SCALE)

    active = -1 if frame < 12 else min(2, (frame - 12) // 7)
    draw_card(draw, 343, "01 / MEANING", "paid_orders · v1", CYAN, active >= 0)
    draw_card(draw, 539, "02 / POLICY", "tenant = Aurora", GREEN, active >= 1)
    draw_card(draw, 735, "03 / EVIDENCE", "Gold orders", AMBER, active >= 2)
    for x in (530, 726):
        draw.line(xy((x - 4, 235, x + 5, 235)), fill=CYAN if active >= 1 else EDGE,
                  width=2 * SCALE)
        polygon(draw, [(x + 5, 231), (x + 11, 235), (x + 5, 239)],
                CYAN if active >= 1 else EDGE)

    label(draw, 343, 282, "AGUMON ANSWERS", 11, ORANGE_LIGHT, True)
    rounded(draw, (342, 305, 919, 444), (29, 46, 58),
            GREEN if frame >= 39 else EDGE, 11, 2 if frame >= 39 else 1)
    if frame < 31:
        state = "Reading the approved metric and checking scope"
        label(draw, 360, 319, state + "." * (1 + (frame // 5) % 3), 16, MUTED)
    else:
        answer = "Aurora had 128 paid orders last week."
        label(draw, 360, 317, typed(answer, frame, 31, 42), 19, TEXT, True)
        if frame >= 42:
            label(draw, 360, 353, "COUNT(DISTINCT order_id)  ·  status = paid", 13, CYAN)
        if frame >= 49:
            rounded(draw, (358, 384, 496, 423), (32, 61, 63), GREEN, 7)
            label(draw, 370, 393, "tenant-scoped", 12, GREEN, True)
        if frame >= 55:
            rounded(draw, (507, 384, 636, 423), (32, 54, 67), CYAN, 7)
            label(draw, 520, 393, "metric v1", 12, CYAN, True)
        if frame >= 61:
            rounded(draw, (647, 384, 899, 423), (60, 52, 40), AMBER, 7)
            label(draw, 660, 393, "Gold lineage + freshness", 12, AMBER, True)

    rounded(draw, (20, 480, 940, 507), (27, 35, 47), EDGE, 6)
    label(draw, 31, 485,
          "DESIGN CONCEPT  ·  Result is synthetic  ·  Definition, policy, query and lineage travel with the answer",
          12, MUTED)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main() -> None:
    frames = [render(frame) for frame in range(FRAMES)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   duration=DURATION_MS, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT}: {FRAMES} frames, {OUTPUT.stat().st_size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
