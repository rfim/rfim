"""Render four NEXUS accordion equations as an animated profile GIF.

Requires Pillow. GitHub renders the generated GIF in the profile README.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "nexus-math.gif"
WIDTH, HEIGHT, SCALE = 960, 402, 2
FRAMES, DURATION_MS = 48, 90

AVENIR = Path("/System/Library/Fonts/Avenir Next.ttc")
MATH_FONT = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
if not AVENIR.exists():
    AVENIR = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
if not MATH_FONT.exists():
    MATH_FONT = AVENIR

BG = (20, 28, 31)
PANEL = (29, 41, 43)
PANEL_ACTIVE = (47, 52, 49)
EDGE = (58, 77, 73)
TEXT = (246, 247, 239)
MUTED = (164, 184, 175)
CORAL = (241, 127, 100)
PALE_CORAL = (255, 180, 153)

RULES = [
    ("01 / REPLAY", "load(load(T, B), B) = load(T, B)",
     "The same batch leaves visible state unchanged."),
    ("02 / RECONCILE", "N_received = N_applied + N_replayed + N_quarantined",
     "Every received row has an outcome."),
    ("03 / PUBLISH", "publish(r) ⇔ schema(r) ∧ key(r) ∧ value(r) ∧ tenant(r)",
     "Only records passing every contract become visible."),
    ("04 / TENANT", "deliver(t) = { r ∈ published : tenant(r) = t }",
     "Each output contains one client's approved records."),
]


def font(size: int, bold: bool = False, mathematical: bool = False) -> ImageFont.FreeTypeFont:
    path = MATH_FONT if mathematical else AVENIR
    if path == AVENIR and path.suffix == ".ttc":
        return ImageFont.truetype(str(path), size * SCALE, index=0 if bold else 7)
    return ImageFont.truetype(str(path), size * SCALE)


def box(values: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(value * SCALE) for value in values)


def label(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str,
          size: int, fill: tuple[int, int, int], bold: bool = False,
          mathematical: bool = False) -> None:
    draw.text((xy[0] * SCALE, xy[1] * SCALE), value,
              font=font(size, bold, mathematical), fill=fill, anchor="lt")


def blend(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def reconciliation_equation(draw: ImageDraw.ImageDraw, xy: tuple[float, float]) -> None:
    """Typeset the accordion's received = applied + replayed + quarantined rule."""
    x, y = xy[0] * SCALE, xy[1] * SCALE
    base_font, sub_font = font(22, mathematical=True), font(12, mathematical=True)
    for main, subscript in [("N", "received"), (" = ", ""), ("N", "applied"),
                            (" + ", ""), ("N", "replayed"), (" + ", ""),
                            ("N", "quarantined")]:
        draw.text((x, y), main, font=base_font, fill=TEXT, anchor="lt")
        x += draw.textlength(main, font=base_font)
        if subscript:
            draw.text((x, y + 14 * SCALE), subscript, font=sub_font, fill=TEXT, anchor="lt")
            x += draw.textlength(subscript, font=sub_font) + 2 * SCALE


def render(index: int) -> Image.Image:
    progress = index / FRAMES
    pulse_y = 140 + 214 * progress
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)

    for x in range(23, WIDTH, 64):
        draw.line(box((x, 0, x, HEIGHT)), fill=(27, 37, 39), width=SCALE)
    for y in range(16, HEIGHT, 64):
        draw.line(box((0, y, WIDTH, y)), fill=(27, 37, 39), width=SCALE)
    label(draw, (29, 20), "NEXUS", 37, TEXT, True)
    draw.ellipse(box((172, 54, 181, 63)), fill=CORAL)
    label(draw, (29, 68), "THE MATH BEHIND TRUST", 13, PALE_CORAL, True)
    label(draw, (604, 36), "four rules behind a reliable data path", 17, TEXT)

    top_positions = [111, 178, 245, 312]
    rail_x = 43
    draw.line(box((rail_x, 139, rail_x, 356)), fill=EDGE, width=3 * SCALE)
    draw.line(box((rail_x, 139, rail_x, pulse_y)), fill=CORAL, width=3 * SCALE)

    for (name, equation, explanation), top in zip(RULES, top_positions):
        center = top + 28
        intensity = max(0.0, 1.0 - abs(pulse_y - center) / 66)
        draw.rounded_rectangle(box((64, top, 936, top + 57)), radius=11 * SCALE,
                               fill=blend(PANEL, PANEL_ACTIVE, intensity),
                               outline=blend(EDGE, CORAL, intensity), width=2 * SCALE)
        draw.line(box((224, top + 10, 224, top + 47)), fill=EDGE, width=SCALE)
        label(draw, (81, top + 19), name, 13, blend(MUTED, PALE_CORAL, intensity), True)
        if name.startswith("02"):
            reconciliation_equation(draw, (243, top + 8))
        else:
            label(draw, (243, top + 8), equation, 22, TEXT, mathematical=True)
        label(draw, (244, top + 38), explanation, 12, MUTED)
        draw.ellipse(box((rail_x - 5, center - 5, rail_x + 5, center + 5)),
                     fill=CORAL if pulse_y >= center else EDGE)

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for radius, alpha in [(23, 14), (14, 42), (6, 255)]:
        glow_draw.ellipse(box((rail_x - radius, pulse_y - radius,
                               rail_x + radius, pulse_y + radius)),
                          fill=(*PALE_CORAL, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(image)
    label(draw, (28, 380), "ORDER  /  REPLAY  /  RECONCILE  /  CLIENT SCOPE", 11, MUTED, True)
    label(draw, (816, 380), "BY VIM", 11, PALE_CORAL, True)
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
