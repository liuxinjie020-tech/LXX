"""Batch-render LiXiang Design presentation sheets without altering source images."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


DEFAULT_ORANGE = "#EF6512"
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError("Color must be a six-digit hex value, e.g. #EF6512")
    return tuple(int(value[index:index + 2], 16) for index in range(0, 6, 2))


def chinese_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def latin_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)


def source_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    return sorted(item for item in source.iterdir() if item.suffix.lower() in IMAGE_TYPES)


def draw_mark(draw: ImageDraw.ImageDraw, x: int, y: int, block: int, gap: int,
              color: tuple[int, int, int]) -> None:
    for column, row in ((0, 0), (2, 0), (0, 1), (1, 1), (0, 2), (1, 2), (2, 2)):
        left = x + column * (block + gap)
        top = y + row * (block + gap)
        draw.rectangle((left, top, left + block, top + block), fill=color)


def place_source(canvas: Image.Image, source: Image.Image, safe: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = safe
    available = (right - left, bottom - top)
    prepared = ImageOps.exif_transpose(source).convert("RGB")
    prepared.thumbnail(available, Image.Resampling.LANCZOS)
    prepared = ImageEnhance.Contrast(prepared).enhance(1.02)
    prepared = prepared.filter(ImageFilter.UnsharpMask(radius=1.0, percent=75, threshold=3))
    x = left + (available[0] - prepared.width) // 2
    y = top + (available[1] - prepared.height) // 2
    canvas.paste(prepared, (x, y))


def add_frame_and_brand(canvas: Image.Image, color: tuple[int, int, int], title: str,
                        watermark_cn: str, watermark_en: str, opacity: int) -> Image.Image:
    width, height = canvas.size
    draw = ImageDraw.Draw(canvas)
    margin, stroke = 58, 9
    draw.rectangle((margin, margin, width - margin, height - margin), outline=color, width=stroke)

    if title:
        draw.rectangle((128, 110, 170, 152), fill=color)
        draw.text((188, 92), title, font=chinese_font(76), fill=color)
        draw.line((188, 188, 1480, 188), fill=color, width=8)

    # Lower-left logo: direct vector geometry remains crisp at any output size.
    logo_x, logo_y = 128, height - 270
    draw_mark(draw, logo_x, logo_y, 38, 6, color)
    draw.text((logo_x, logo_y + 143), "LiXiang Design", font=latin_font(58), fill=color)

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    mark = ImageDraw.Draw(overlay)
    large_font = chinese_font(360, bold=True)
    bounds = mark.textbbox((0, 0), watermark_cn, font=large_font)
    mark.text(((width - (bounds[2] - bounds[0])) // 2, height // 2 - 240), watermark_cn,
              font=large_font, fill=(*color, opacity))
    sub_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 84)
    bounds = mark.textbbox((0, 0), watermark_en, font=sub_font)
    mark.text(((width - (bounds[2] - bounds[0])) // 2, height // 2 + 155), watermark_en,
              font=sub_font, fill=(*color, max(20, opacity - 10)))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def render(path: Path, destination: Path, args: argparse.Namespace, color: tuple[int, int, int]) -> None:
    canvas = Image.new("RGB", (args.width, args.height), "white")
    with Image.open(path) as source:
        place_source(canvas, source, (120, 260, args.width - 120, args.height - 250))
    final = add_frame_and_brand(canvas, color, args.title, args.watermark_cn,
                                args.watermark_en, args.watermark_opacity)
    stem = f"{path.stem}_LiXiang品牌排版"
    final.save(destination / f"{stem}.png", "PNG", optimize=True, dpi=(300, 300))
    final.save(destination / f"{stem}.jpg", "JPEG", quality=97, subsampling=0,
               optimize=True, dpi=(300, 300))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input image file or directory")
    parser.add_argument("--output", required=True, help="Empty or new output directory")
    parser.add_argument("--title", default="秋季快题作品展示")
    parser.add_argument("--frame-color", default=DEFAULT_ORANGE)
    parser.add_argument("--watermark-cn", default="厘想")
    parser.add_argument("--watermark-en", default="LIXIANG DESIGN")
    parser.add_argument("--watermark-opacity", type=int, default=46)
    parser.add_argument("--width", type=int, default=4800)
    parser.add_argument("--height", type=int, default=3400)
    args = parser.parse_args()
    if not 0 <= args.watermark_opacity <= 255:
        parser.error("--watermark-opacity must be between 0 and 255")

    input_path, output_path = Path(args.input), Path(args.output)
    files = source_files(input_path)
    if not files:
        parser.error("No supported image files found")
    output_path.mkdir(parents=True, exist_ok=True)
    color = rgb(args.frame_color)
    for file in files:
        render(file, output_path, args, color)
        print(file.name)


if __name__ == "__main__":
    main()
