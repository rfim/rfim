"""Render a synthetic, config-driven multi-tenant ingestion architecture GIF."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "multitenant-ingestion.gif"
WIDTH, HEIGHT, SCALE = 960, 470, 2
FRAMES, DURATION_MS = 72, 90
FONT_FILE = Path("/System/Library/Fonts/Avenir Next.ttc")
if not FONT_FILE.exists():
    FONT_FILE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

BG = (15, 21, 31)
PANEL = (24, 33, 47)
EDGE = (54, 67, 82)
TEXT = (242, 245, 247)
MUTED = (164, 179, 193)
CYAN = (102, 221, 229)
VIOLET = (181, 156, 249)
GREEN = (152, 224, 170)
GOLD = (242, 188, 100)
COLORS = (CYAN, VIOLET, GREEN)

ROUTES = [
    ("AURORA", "POSTGRES CDC", "orders", "checkpoints/aurora", CYAN),
    ("BEACON", "S3 FILES", "orders", "checkpoints/beacon", VIOLET),
    ("CEDAR", "REST API", "accounts", "checkpoints/cedar", GREEN),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILE), size * SCALE, index=0 if bold else 7)


def xy(values: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(v * SCALE) for v in values)


def text(draw: ImageDraw.ImageDraw, x: float, y: float, value: str, size: int,
         fill: tuple[int, int, int] = TEXT, bold: bool = False,
         anchor: str = "lt") -> None:
    draw.text((round(x * SCALE), round(y * SCALE)), value,
              font=font(size, bold), fill=fill, anchor=anchor)


def progress(frame: int, start: int, end: int) -> float:
    return min(1.0, max(0.0, (frame - start) / (end - start)))


def arrow(draw: ImageDraw.ImageDraw, x1: float, y1: float,
          x2: float, y2: float, color: tuple[int, int, int]) -> None:
    draw.line(xy((x1, y1, x2, y2)), fill=color, width=2 * SCALE)
    draw.polygon([(round((x2 - 7) * SCALE), round((y2 - 4) * SCALE)),
                  (round(x2 * SCALE), round(y2 * SCALE)),
                  (round((x2 - 7) * SCALE), round((y2 + 4) * SCALE))], fill=color)


def render(frame: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)

    # A faint grid lets the three animated routes read as a system.
    for gx in range(0, WIDTH, 50):
        draw.line(xy((gx, 0, gx, HEIGHT)), fill=(21, 29, 42), width=SCALE)
    for gy in range(0, HEIGHT, 50):
        draw.line(xy((0, gy, WIDTH, gy)), fill=(21, 29, 42), width=SCALE)

    text(draw, 23, 15, "ONE YAML.", 32, TEXT, True)
    text(draw, 218, 15, "MANY INGESTION ROUTES.", 32, CYAN, True)
    text(draw, 23, 57, "Config defines tenants; the controller expands isolated routes.", 15, MUTED)
    text(draw, 739, 62, "SYNTHETIC DESIGN SKETCH", 11, GOLD, True)

    # The code panel is a concise excerpt of the committed YAML example.
    draw.rounded_rectangle(xy((22, 101, 291, 405)), radius=13 * SCALE,
                           fill=PANEL, outline=EDGE, width=2 * SCALE)
    draw.rounded_rectangle(xy((22, 101, 291, 139)), radius=12 * SCALE,
                           fill=(31, 44, 57))
    text(draw, 37, 111, "multitenant-ingestion.yaml", 14, TEXT, True)
    lines = [
        ("version: 1", None),
        ("defaults:", None),
        ("  target_format: delta", None),
        ("  schema_drift: quarantine", None),
        ("tenants:", None),
        ("  - id: aurora", 0),
        ("    source: postgres_cdc", 0),
        ("  - id: beacon", 1),
        ("    source: s3_files", 1),
        ("  - id: cedar", 2),
        ("    source: rest_api", 2),
    ]
    launched = [frame >= 8, frame >= 23, frame >= 38]
    for index, (content, tenant) in enumerate(lines):
        ly = 151 + index * 21
        active = tenant is not None and (8 <= frame < 24 and tenant == 0 or
                                         23 <= frame < 39 and tenant == 1 or
                                         38 <= frame < 54 and tenant == 2)
        if active:
            draw.rounded_rectangle(xy((34, ly - 2, 279, ly + 20)), radius=4 * SCALE,
                                   fill=(42, 64, 74))
        color = COLORS[tenant] if tenant is not None else (
            GOLD if content.startswith("  ") else MUTED)
        text(draw, 39, ly, content, 12, color, tenant is not None)

    arrow(draw, 298, 253, 329, 253, CYAN)
    draw.rounded_rectangle(xy((335, 176, 494, 329)), radius=13 * SCALE,
                           fill=PANEL, outline=CYAN, width=2 * SCALE)
    text(draw, 350, 195, "VALIDATE", 19, TEXT, True)
    text(draw, 350, 222, "contract + paths", 13, MUTED)
    draw.line(xy((350, 250, 478, 250)), fill=EDGE, width=SCALE)
    text(draw, 350, 262, "EXPAND", 19, TEXT, True)
    text(draw, 350, 289, f"{sum(launched)} of 3 routes", 14, CYAN, True)

    # An arrow fans out from the controller to three independent lanes.
    draw.line(xy((495, 253, 508, 253)), fill=EDGE, width=2 * SCALE)
    draw.line(xy((508, 155, 508, 357)), fill=EDGE, width=2 * SCALE)
    for i, (tenant, source, dataset, checkpoint, color) in enumerate(ROUTES):
        top = 101 + i * 107
        center_y = top + 54
        arrow(draw, 508, center_y, 523, center_y, color)
        draw.rounded_rectangle(xy((529, top, 939, top + 95)), radius=12 * SCALE,
                               fill=PANEL, outline=color if launched[i] else EDGE,
                               width=(2 if launched[i] else 1) * SCALE)
        text(draw, 545, top + 10, tenant, 18, color, True)
        text(draw, 654, top + 15, source, 12, MUTED, True)
        text(draw, 546, top + 38, f"{dataset}  |  {checkpoint}", 12, MUTED)
        arrow(draw, 552, top + 73, 768, top + 73, EDGE)
        draw.rounded_rectangle(xy((781, top + 58, 925, top + 87)), radius=7 * SCALE,
                               fill=(33, 46, 51), outline=color, width=SCALE)
        text(draw, 853, top + 66, "DELTA BRONZE", 11, color, True, "mt")

        p = progress(frame, (8, 23, 38)[i], (41, 56, 71)[i])
        if 0 < p < 1:
            dot_x = 555 + 208 * p
            for radius, alpha in ((12, 65), (7, 125), (4, 255)):
                # Explicit RGB glow rings stay small and readable in GitHub GIFs.
                shade = tuple(round(BG[c] * (1 - alpha / 255) + color[c] * alpha / 255)
                              for c in range(3))
                draw.ellipse(xy((dot_x - radius, top + 73 - radius,
                                 dot_x + radius, top + 73 + radius)), fill=shade)
        if p >= 1:
            draw.ellipse(xy((753, top + 68, 763, top + 78)), fill=color)

    draw.rounded_rectangle(xy((22, 426, 938, 454)), radius=7 * SCALE,
                           fill=(29, 41, 53), outline=EDGE, width=SCALE)
    text(draw, 36, 432,
         "Per-tenant secrets  /  independent checkpoints  /  schema contracts  /  replay one route",
         13, TEXT, True)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main() -> None:
    frames = [render(frame) for frame in range(FRAMES)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   duration=DURATION_MS, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT}: {FRAMES} frames, {OUTPUT.stat().st_size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
