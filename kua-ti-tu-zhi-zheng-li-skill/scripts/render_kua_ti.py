"""Render numbered architecture sheets as complete, PNG-only presentation boards."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


WIDTH, HEIGHT = 4800, 3400
ORANGE = (239, 101, 18)
NUMBERED_IMAGE = re.compile(r"^(\d+)(?:\.(\d+))?\.(?:jpe?g|png|tiff?|webp)$", re.I)


def chinese_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size)


def latin_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)


def draw_logo(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    block, gap = 38, 6
    for column, row in ((0, 0), (2, 0), (0, 1), (1, 1), (0, 2), (1, 2), (2, 2)):
        left = x + column * (block + gap)
        top = y + row * (block + gap)
        draw.rectangle((left, top, left + block, top + block), fill=ORANGE)


def group_sources(folder: Path) -> dict[int, list[Path]]:
    grouped: dict[int, list[tuple[int, Path]]] = {}
    for file in folder.iterdir():
        if not file.is_file():
            continue
        match = NUMBERED_IMAGE.match(file.name)
        if match:
            grouped.setdefault(int(match.group(1)), []).append((int(match.group(2) or 0), file))
    if not grouped:
        raise ValueError("未找到形如 5.1.jpg 或 5.jpg 的已编号图片。")
    return {number: [file for _, file in sorted(files)] for number, files in sorted(grouped.items())}


def trim_blank_border(source: Image.Image, padding: int = 32) -> Image.Image:
    """Trim only definitely white outer paper while keeping all visible content plus padding."""
    image = ImageOps.exif_transpose(source).convert("RGB")
    pixels = np.asarray(image)
    visible = pixels.min(axis=2) < 250
    rows, columns = np.flatnonzero(visible.any(axis=1)), np.flatnonzero(visible.any(axis=0))
    if not len(rows) or not len(columns):
        return image
    return image.crop((
        max(0, int(columns[0]) - padding),
        max(0, int(rows[0]) - padding),
        min(image.width, int(columns[-1]) + 1 + padding),
        min(image.height, int(rows[-1]) + 1 + padding),
    ))


def watermark_layer(path: Path) -> Image.Image:
    supplied = Image.open(path).convert("RGBA")
    rgba = np.asarray(supplied).copy()
    darkness = 255 - rgba[:, :, :3].min(axis=2)
    rgba[:, :, 3] = np.minimum(54, (darkness * 0.22).astype(np.uint8))
    mark = Image.fromarray(rgba, "RGBA")
    scale = min(1760 / mark.width, 1760 / mark.height)
    return mark.resize((round(mark.width * scale), round(mark.height * scale)), Image.Resampling.LANCZOS)


def cells_for(count: int, bounds: tuple[int, int, int, int]) -> list[tuple[int, int, int, int]]:
    left, top, right, bottom = bounds
    gap = 20
    if count == 1:
        return [bounds]
    if count == 2:
        mid = (left + right - gap) // 2
        return [(left, top, mid, bottom), (mid + gap, top, right, bottom)]
    if count == 3:
        split = left + int((right - left - gap) * 0.56)
        half = (bottom - top - gap) // 2
        return [(left, top, split, bottom), (split + gap, top, right, top + half),
                (split + gap, top + half + gap, right, bottom)]
    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)
    cell_w = (right - left - gap * (columns - 1)) // columns
    cell_h = (bottom - top - gap * (rows - 1)) // rows
    return [
        (left + col * (cell_w + gap), top + row * (cell_h + gap),
         left + col * (cell_w + gap) + cell_w, top + row * (cell_h + gap) + cell_h)
        for row in range(rows) for col in range(columns)
    ][:count]


def paste_complete(canvas: Image.Image, file: Path, cell: tuple[int, int, int, int]) -> None:
    with Image.open(file) as raw:
        image = trim_blank_border(raw)
    left, top, right, bottom = cell
    scale = min((right - left) / image.width, (bottom - top) / image.height)
    rendered = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                            Image.Resampling.LANCZOS)
    rendered = ImageEnhance.Contrast(rendered).enhance(1.02)
    x = left + ((right - left) - rendered.width) // 2
    y = top + ((bottom - top) - rendered.height) // 2
    canvas.paste(rendered, (x, y))


def add_branding(canvas: Image.Image, watermark: Image.Image, title: str) -> Image.Image:
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((58, 58, WIDTH - 58, HEIGHT - 58), outline=ORANGE, width=9)
    draw.rectangle((128, 110, 170, 152), fill=ORANGE)
    draw.text((188, 92), title, font=chinese_font(76), fill=ORANGE)
    draw.line((188, 188, 1480, 188), fill=ORANGE, width=8)
    draw_logo(draw, 128, HEIGHT - 270)
    draw.text((128, HEIGHT - 127), "LiXiang Design", font=latin_font(58), fill=ORANGE)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay.alpha_composite(watermark, ((WIDTH - watermark.width) // 2, (HEIGHT - watermark.height) // 2))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def render_board(files: list[Path], watermark: Image.Image, title: str) -> Image.Image:
    board = Image.new("RGB", (WIDTH, HEIGHT), "white")
    art_bounds = (118, 245, WIDTH - 118, HEIGHT - 305)
    for file, cell in zip(files, cells_for(len(files), art_bounds)):
        paste_complete(board, file, cell)
    return add_branding(board, watermark, title)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Directory containing numbered source images")
    parser.add_argument("--watermark", required=True, type=Path, help="Watermark image supplied for this batch")
    parser.add_argument("--output", required=True, type=Path, help="Destination directory for PNG boards")
    parser.add_argument("--title", default="秋季快题作品展示")
    parser.add_argument("--overwrite", action="store_true", help="Replace matching PNG files in the destination")
    args = parser.parse_args()
    if not args.input.is_dir():
        parser.error("--input 必须是图片目录。")
    if not args.watermark.is_file():
        parser.error("--watermark 必须是存在的图片文件。")
    args.output.mkdir(parents=True, exist_ok=True)
    mark = watermark_layer(args.watermark)
    for number, files in group_sources(args.input).items():
        destination = args.output / f"{number:02d}_快题整理.png"
        if destination.exists() and not args.overwrite:
            raise FileExistsError(f"已有输出文件：{destination}。确认后使用 --overwrite 覆盖。")
        render_board(files, mark, args.title).save(destination, "PNG", optimize=True, dpi=(300, 300))
        print(f"{destination.name}: {len(files)} 张原图")


if __name__ == "__main__":
    main()
