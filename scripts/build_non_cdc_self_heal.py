"""Render the synthetic non-CDC file self-healing animation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "non-cdc-self-heal.gif"
WIDTH, HEIGHT, SCALE = 960, 505, 2
FRAMES, DURATION_MS = 78, 95
FONT_FILE = Path("/System/Library/Fonts/Avenir Next.ttc")
if not FONT_FILE.exists():
    FONT_FILE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

BG = (15, 21, 31)
PANEL = (24, 33, 47)
EDGE = (53, 67, 82)
TEXT = (242, 245, 247)
MUTED = (164, 179, 193)
CYAN = (102, 221, 229)
GREEN = (152, 224, 170)
AMBER = (242, 188, 100)
RED = (244, 132, 126)
VIOLET = (181, 156, 249)

STAGES = [
    ("01 / ARRIVE", "S3 object", "Beacon / v17", CYAN),
    ("02 / REPLAY", "Manifest", "version + SHA-256", GREEN),
    ("03 / CONTRACT", "Schema gate", "unknown = hold", AMBER),
    ("04 / REPAIR", "Self-heal", "approved cast only", VIOLET),
    ("05 / LAND", "Delta Bronze", "accepted rows", GREEN),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILE), size * SCALE, index=0 if bold else 7)


def box(values: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(v * SCALE) for v in values)


def text(draw: ImageDraw.ImageDraw, x: float, y: float, value: str, size: int,
         fill: tuple[int, int, int] = TEXT, bold: bool = False) -> None:
    draw.text((round(x * SCALE), round(y * SCALE)), value,
              font=font(size, bold), fill=fill, anchor="lt")


def progress(frame: int, start: int, end: int) -> float:
    return min(1.0, max(0.0, (frame - start) / (end - start)))


def draw_arrow(draw: ImageDraw.ImageDraw, x1: int, x2: int, y: int) -> None:
    draw.line(box((x1, y, x2 - 5, y)), fill=EDGE, width=2 * SCALE)
    draw.polygon([(round((x2 - 6) * SCALE), round((y - 4) * SCALE)),
                  (round(x2 * SCALE), round(y * SCALE)),
                  (round((x2 - 6) * SCALE), round((y + 4) * SCALE))], fill=EDGE)


def record(draw: ImageDraw.ImageDraw, x: float, y: float,
           color: tuple[int, int, int], caption: str) -> None:
    for radius, opacity in ((18, .12), (12, .25), (7, .48)):
        shade = tuple(round(BG[i] * (1 - opacity) + color[i] * opacity) for i in range(3))
        draw.ellipse(box((x - radius, y - radius, x + radius, y + radius)), fill=shade)
    draw.ellipse(box((x - 6, y - 6, x + 6, y + 6)), fill=color, outline=TEXT,
                 width=SCALE)
    text(draw, x - 24, y + 14, caption, 10, color, True)


def render(frame: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)
    for gx in range(0, WIDTH, 50):
        draw.line(box((gx, 0, gx, HEIGHT)), fill=(21, 29, 42), width=SCALE)
    for gy in range(0, HEIGHT, 50):
        draw.line(box((0, gy, WIDTH, gy)), fill=(21, 29, 42), width=SCALE)

    text(draw, 22, 14, "NON-CDC", 33, TEXT, True)
    text(draw, 217, 14, "SAFE SELF-HEAL", 33, GREEN, True)
    text(draw, 22, 56, "Known formatting issue: repair. Bad row: quarantine. New field: hold.",
         15, MUTED)
    text(draw, 760, 60, "SYNTHETIC DESIGN SKETCH", 10, AMBER, True)

    lefts = [20, 205, 390, 575, 760]
    if frame < 40:
        active_stage = min(4, round(4 * progress(frame, 0, 39)))
    elif frame < 51:
        active_stage = 1
    else:
        active_stage = 2
    for i, (tag, title, detail, color) in enumerate(STAGES):
        left = lefts[i]
        active = i == active_stage
        draw.rounded_rectangle(box((left, 113, left + 170, 225)), radius=12 * SCALE,
                               fill=(31, 45, 56) if active else PANEL,
                               outline=color if active else EDGE,
                               width=(2 if active else 1) * SCALE)
        text(draw, left + 12, 128, tag, 11, color, True)
        text(draw, left + 12, 156, title, 19, TEXT, True)
        text(draw, left + 12, 195, detail, 12, MUTED)
        if i < 4:
            draw_arrow(draw, left + 172, lefts[i + 1] - 3, 169)

    draw.line(box((105, 263, 845, 263)), fill=EDGE, width=2 * SCALE)
    for center in (105, 290, 475, 660, 845):
        draw.ellipse(box((center - 4, 259, center + 4, 267)), fill=EDGE)

    if frame < 40:
        x = 105 + 740 * progress(frame, 0, 39)
        color = GREEN if frame >= 29 else CYAN if frame < 20 else AMBER
        record(draw, x, 263, color, "v17")
        if 24 <= frame <= 40:
            bad_y = 263 + 46 * progress(frame, 24, 34)
            record(draw, 475, bad_y, RED, "row 2")
        if frame >= 34:
            draw.rounded_rectangle(box((392, 291, 558, 316)), radius=6 * SCALE,
                                   fill=(58, 38, 43), outline=RED, width=SCALE)
            text(draw, 406, 294, "QUARANTINE / BAD VALUE", 10, RED, True)
    elif frame < 51:
        x = 105 + 185 * progress(frame, 40, 48)
        record(draw, x, 263, AMBER, "v17")
        if frame >= 48:
            draw.rounded_rectangle(box((221, 291, 361, 316)), radius=6 * SCALE,
                                   fill=(56, 47, 34), outline=AMBER, width=SCALE)
            text(draw, 236, 294, "RETRY / NO-OP", 11, AMBER, True)
    else:
        x = 105 + 370 * progress(frame, 51, 65)
        record(draw, x, 263, AMBER, "v18")
        if frame >= 65:
            draw.rounded_rectangle(box((414, 291, 536, 316)), radius=6 * SCALE,
                                   fill=(57, 46, 33), outline=AMBER, width=SCALE)
            text(draw, 431, 294, "SCHEMA HOLD", 11, AMBER, True)

    draw.rounded_rectangle(box((20, 330, 453, 465)), radius=11 * SCALE,
                           fill=PANEL, outline=EDGE, width=SCALE)
    text(draw, 35, 342, "BEACON / FILE LOG", 13, CYAN, True)
    if frame < 40:
        if frame < 17:
            lines = [("v17: 3 order rows", TEXT),
                     ("Checking version ID and checksum", MUTED),
                     ("Contract and quality gates ahead", CYAN)]
        else:
            lines = [("v17: 3 order rows", TEXT),
                     ("'19.50' -> 19.50 / approved exact cast", GREEN),
                     ("1 invalid amount quarantined; 2 land", RED)]
    elif frame < 51:
        lines = [("v17 arrives again", TEXT),
                 ("Same version ID + checksum", MUTED),
                 ("Manifest says committed: no-op", GREEN)]
    else:
        lines = [("v18 adds customer_phone", TEXT),
                 ("Unknown field: hold the whole file", AMBER),
                 ("Other tenant routes keep moving", GREEN)]
    for i, (line, color) in enumerate(lines):
        text(draw, 36, 369 + i * 27, line, 15 if i == 0 else 13,
             color, i == 0)

    draw.rounded_rectangle(box((471, 330, 940, 465)), radius=11 * SCALE,
                           fill=PANEL, outline=VIOLET if frame >= 65 else EDGE,
                           width=(2 if frame >= 65 else 1) * SCALE)
    text(draw, 486, 342, "REPAIR POLICY + AI ADVISORY", 13, VIOLET, True)
    if frame < 51:
        text(draw, 487, 373, "Auto-fix: exact decimal cast only", 15, TEXT, True)
        text(draw, 487, 402, "No guessed amounts or new fields", 13, MUTED)
        text(draw, 487, 429, "Every repair keeps its rule and source ID", 13, GREEN)
    elif frame < 65:
        text(draw, 487, 378, "Schema diff detected; AI waits for metadata", 14, MUTED)
        text(draw, 487, 407, "File v18 remains held", 13, AMBER)
    else:
        text(draw, 487, 369, "+ customer_phone : string", 16, TEXT, True)
        text(draw, 487, 395, "Mock AI: review as personal data", 13, VIOLET)
        text(draw, 487, 422, "Human approval required; no auto-release", 13, AMBER, True)

    text(draw, 22, 480,
         "Self-heal is an approved rule, not a model changing business data.",
         13, MUTED, True)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main() -> None:
    frames = [render(frame) for frame in range(FRAMES)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   duration=DURATION_MS, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT}: {FRAMES} frames, {OUTPUT.stat().st_size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
