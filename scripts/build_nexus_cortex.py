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
YELLOW = (246, 193, 45)
YELLOW_LIGHT = (255, 222, 103)
YELLOW_DARK = (175, 116, 25)
EYE_GREEN = (79, 160, 143)


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
    """Draw a simplified yellow Agumon sketch based on the supplied reference."""
    bob = math.sin(frame * .22) * 3
    blink = frame % 43 in (29, 30)
    pulse = 4 + 5 * (0.5 + 0.5 * math.sin(frame * .32))

    draw.ellipse(xy((56 - pulse, 111 - pulse, 250 + pulse, 305 + pulse)),
                 outline=(42, 91, 103), width=2 * SCALE)
    draw.ellipse(xy((69, 124, 237, 292)), fill=(29, 62, 73))
    draw.ellipse(xy((90, 386, 218, 403)), fill=(11, 17, 25))

    # Tail and little limbs sit behind the oversized head.
    polygon(draw, [(209, 317 + bob), (255, 336 + bob), (266, 354 + bob),
                   (230, 346 + bob), (213, 365 + bob)], YELLOW, YELLOW_DARK)
    draw.ellipse(xy((119, 287 + bob, 221, 383 + bob)), fill=YELLOW,
                 outline=YELLOW_DARK, width=2 * SCALE)
    draw.ellipse(xy((145, 320 + bob, 197, 375 + bob)), fill=(255, 208, 71))
    polygon(draw, [(120, 342 + bob), (108, 371 + bob), (132, 386 + bob),
                   (154, 377 + bob), (153, 347 + bob)], YELLOW, YELLOW_DARK)
    polygon(draw, [(187, 348 + bob), (193, 379 + bob), (220, 388 + bob),
                   (231, 373 + bob), (218, 343 + bob)], YELLOW, YELLOW_DARK)
    for x, y in ((116, 374), (133, 379), (201, 381), (220, 380)):
        polygon(draw, [(x - 6, y + bob), (x + 6, y + bob),
                       (x + 1, y + 13 + bob)], TEXT)
    # One raised hand gives the chatbot a small wave.
    hand_lift = math.sin(frame * .22) * 5
    polygon(draw, [(120, 311 + bob), (84, 330 + bob - hand_lift),
                   (70, 312 + bob - hand_lift), (62, 337 + bob - hand_lift),
                   (87, 359 + bob - hand_lift), (132, 339 + bob)],
            YELLOW, YELLOW_DARK)
    for x, y in ((62, 316), (72, 309), (83, 315)):
        polygon(draw, [(x, y + bob - hand_lift),
                       (x + 10, y + 5 + bob - hand_lift),
                       (x - 2, y - 11 + bob - hand_lift)], TEXT)

    # The supplied Agumon has a long left-facing snout, rounded crest,
    # one large green eye, white teeth and claws, and golden-yellow skin.
    draw.ellipse(xy((113, 144 + bob, 253, 305 + bob)), fill=YELLOW,
                 outline=YELLOW_DARK, width=2 * SCALE)
    draw.ellipse(xy((119, 129 + bob, 177, 190 + bob)), fill=YELLOW)
    draw.ellipse(xy((155, 144 + bob, 219, 194 + bob)), fill=YELLOW)
    draw.ellipse(xy((196, 158 + bob, 246, 205 + bob)), fill=YELLOW)
    polygon(draw, [(118, 155 + bob), (147, 132 + bob), (176, 145 + bob),
                   (211, 156 + bob), (243, 182 + bob), (245, 225 + bob),
                   (212, 252 + bob), (128, 233 + bob)], YELLOW)
    draw.ellipse(xy((55, 202 + bob, 217, 306 + bob)), fill=(227, 163, 32),
                 outline=YELLOW_DARK, width=2 * SCALE)
    draw.ellipse(xy((46, 181 + bob, 198, 276 + bob)), fill=YELLOW,
                 outline=YELLOW_DARK, width=2 * SCALE)
    draw.ellipse(xy((69, 174 + bob, 202, 259 + bob)), fill=YELLOW)
    draw.ellipse(xy((64, 190 + bob, 146, 224 + bob)), fill=YELLOW_LIGHT)
    # Mouth line and the small alternating white teeth.
    draw.arc(xy((53, 231 + bob, 234, 307 + bob)), 12, 163,
             fill=(132, 84, 28), width=3 * SCALE)
    for x, y in ((77, 271), (106, 281), (141, 288), (175, 292), (206, 287)):
        polygon(draw, [(x - 7, y + bob), (x + 8, y + bob),
                       (x + 1, y + 15 + bob)], TEXT)
    draw.ellipse(xy((67, 216 + bob, 73, 229 + bob)), fill=(85, 61, 34))
    draw.ellipse(xy((127, 231 + bob, 134, 240 + bob)), fill=(85, 61, 34))

    # A single expressive eye makes the side profile read like the reference.
    draw.ellipse(xy((183, 191 + bob, 246, 265 + bob)), fill=(48, 55, 50))
    if blink:
        draw.ellipse(xy((186, 215 + bob, 244, 252 + bob)), fill=YELLOW)
        draw.arc(xy((187, 216 + bob, 243, 248 + bob)), 10, 170,
                 fill=(81, 68, 43), width=4 * SCALE)
    else:
        draw.ellipse(xy((188, 196 + bob, 242, 260 + bob)), fill=EYE_GREEN)
        draw.ellipse(xy((194, 211 + bob, 228, 255 + bob)), fill=(40, 72, 57))
        draw.ellipse(xy((200, 198 + bob, 216, 216 + bob)), fill=TEXT)
        draw.ellipse(xy((224, 238 + bob, 233, 248 + bob)), fill=TEXT)
    label(draw, 77, 417, "AGUMON", 18, YELLOW_LIGHT, True)
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

    label(draw, 343, 282, "AGUMON ANSWERS", 11, YELLOW_LIGHT, True)
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
