"""Render the synthetic CDC, schema-drift, and privacy review GIF."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "cdc-guardrails.gif"
WIDTH, HEIGHT, SCALE = 960, 505, 2
FRAMES, DURATION_MS = 66, 100
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
VIOLET = (181, 156, 249)

STAGES = [
    ("01 / CAPTURE", "Debezium CDC", "WAL + tx order", CYAN),
    ("02 / IDEMPOTENCY", "Event identity", "duplicate = no-op", GREEN),
    ("03 / SCHEMA", "Contract gate", "unknown = hold", AMBER),
    ("04 / PRIVACY", "Policy gate", "allowlist + token", VIOLET),
    ("05 / SERVE", "Delta MERGE", "key + source order", GREEN),
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


def draw_arrow(draw: ImageDraw.ImageDraw, x1: int, x2: int, y: int,
               color: tuple[int, int, int]) -> None:
    draw.line(box((x1, y, x2 - 5, y)), fill=color, width=2 * SCALE)
    draw.polygon([(round((x2 - 6) * SCALE), round((y - 4) * SCALE)),
                  (round(x2 * SCALE), round(y * SCALE)),
                  (round((x2 - 6) * SCALE), round((y + 4) * SCALE))], fill=color)


def record(draw: ImageDraw.ImageDraw, x: float, y: float,
           color: tuple[int, int, int], caption: str) -> None:
    for radius, opacity in [(18, .12), (12, .25), (7, .48)]:
        shade = tuple(round(BG[i] * (1 - opacity) + color[i] * opacity) for i in range(3))
        draw.ellipse(box((x - radius, y - radius, x + radius, y + radius)), fill=shade)
    draw.ellipse(box((x - 6, y - 6, x + 6, y + 6)), fill=color, outline=TEXT,
                 width=SCALE)
    text(draw, x - 27, y + 14, caption, 10, color, True)


def render(frame: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)
    for gx in range(0, WIDTH, 50):
        draw.line(box((gx, 0, gx, HEIGHT)), fill=(21, 29, 42), width=SCALE)
    for gy in range(0, HEIGHT, 50):
        draw.line(box((0, gy, WIDTH, gy)), fill=(21, 29, 42), width=SCALE)

    text(draw, 22, 14, "CDC GUARDRAILS", 33, TEXT, True)
    text(draw, 22, 56, "Replay-safe effects. Schema changes held. AI suggests; reviewers decide.",
         15, MUTED)
    text(draw, 759, 60, "SYNTHETIC DESIGN SKETCH", 10, AMBER, True)

    lefts = [20, 205, 390, 575, 760]
    for i, (tag, title, detail, color) in enumerate(STAGES):
        left = lefts[i]
        active = ((frame < 19 and i <= round(4 * progress(frame, 0, 18))) or
                  (19 <= frame < 34 and i == 1) or
                  (frame >= 34 and i == 2))
        draw.rounded_rectangle(box((left, 113, left + 170, 225)), radius=12 * SCALE,
                               fill=(31, 45, 56) if active else PANEL,
                               outline=color if active else EDGE,
                               width=(2 if active else 1) * SCALE)
        text(draw, left + 12, 128, tag, 11, color, True)
        text(draw, left + 12, 156, title, 19, TEXT, True)
        text(draw, left + 12, 195, detail, 12, MUTED)
        if i < 4:
            draw_arrow(draw, left + 172, lefts[i + 1] - 3, 169, EDGE)

    # One source event succeeds; the exact replay stops at the event gate;
    # a new column stops at the schema gate and creates an AI review packet.
    draw.line(box((103, 262, 846, 262)), fill=(54, 70, 83), width=2 * SCALE)
    for center in (105, 290, 475, 660, 845):
        draw.ellipse(box((center - 4, 258, center + 4, 266)), fill=EDGE)
    if frame < 19:
        x = 105 + 740 * progress(frame, 0, 18)
        record(draw, x, 262, CYAN, "2048")
    elif frame < 34:
        x = 105 + 185 * progress(frame, 19, 27)
        record(draw, x, 262, AMBER, "2048")
        if frame >= 27:
            draw.rounded_rectangle(box((220, 287, 362, 312)), radius=6 * SCALE,
                                   fill=(55, 47, 33), outline=AMBER, width=SCALE)
            text(draw, 233, 291, "DUPLICATE  /  NO-OP", 10, AMBER, True)
    else:
        x = 105 + 370 * progress(frame, 34, 45)
        record(draw, x, 262, AMBER, "2051")
        if frame >= 45:
            draw.line(box((475, 272, 475, 312)), fill=AMBER, width=2 * SCALE)
            draw.rounded_rectangle(box((411, 289, 539, 313)), radius=6 * SCALE,
                                   fill=(57, 46, 33), outline=AMBER, width=SCALE)
            text(draw, 432, 292, "SCHEMA HOLD", 11, AMBER, True)

    draw.rounded_rectangle(box((20, 330, 453, 465)), radius=11 * SCALE,
                           fill=PANEL, outline=EDGE, width=SCALE)
    text(draw, 35, 342, "EVENT + CONTROL LOG", 13, CYAN, True)
    if frame < 19:
        lines = [("UPDATE orders / id=42", TEXT),
                 ("LSN 2048 + transaction order 1", MUTED),
                 ("Applying ordered MERGE..." if frame < 16 else
                  "Applied once with ordered MERGE", GREEN)]
    elif frame < 34:
        lines = [("REPLAY: same source event", TEXT),
                 ("Event identity already committed", MUTED),
                 ("No duplicate row or side effect", GREEN)]
    else:
        lines = [("NEW FIELD: customer_phone", TEXT),
                 ("Contract v1 has no approved field", MUTED),
                 ("Aurora held; other tenants continue", AMBER)]
    for index, (line, color) in enumerate(lines):
        text(draw, 36, 369 + index * 27, line, 15 if index == 0 else 13,
             color, index == 0)

    draw.rounded_rectangle(box((471, 330, 940, 465)), radius=11 * SCALE,
                           fill=PANEL, outline=VIOLET if frame >= 45 else EDGE,
                           width=(2 if frame >= 45 else 1) * SCALE)
    text(draw, 486, 342, "AI ADVISORY  /  METADATA ONLY", 13, VIOLET, True)
    if frame < 45:
        text(draw, 487, 377, "Waiting for a schema diff...", 15, MUTED)
        text(draw, 487, 405, "No customer values sent to a model", 13, MUTED)
    else:
        text(draw, 487, 370, "+ customer_phone : string", 16, TEXT, True)
        text(draw, 487, 395, "Suggest: classify as personal; tokenise", 13, VIOLET)
        text(draw, 487, 422, "Status: human approval required", 13, AMBER, True)

    text(draw, 23, 480, "Policy blocks unapproved fields. AI cannot unlock a held route.",
         13, MUTED, True)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main() -> None:
    frames = [render(frame) for frame in range(FRAMES)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   duration=DURATION_MS, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT}: {FRAMES} frames, {OUTPUT.stat().st_size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
