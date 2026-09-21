"""Render a 1:6 architectural-board review long image from a JSON config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1800, 10800
ORANGE, INK, PAPER, MUTED = "#f47600", "#151515", "#ffffff", "#6d6a66"


def font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    raise RuntimeError("No usable Chinese-capable font was found.")


def wrap(draw: ImageDraw.ImageDraw, value: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, line = [], ""
    for char in value:
        test = line + char
        if draw.textlength(test, font=face) <= width:
            line = test
        else:
            if line:
                lines.append(line)
            line = char
    if line:
        lines.append(line)
    return lines


def fit_image(source: Image.Image, max_width: int, max_height: int) -> Image.Image:
    factor = min(max_width / source.width, max_height / source.height)
    size = (max(1, round(source.width * factor)), max(1, round(source.height * factor)))
    return source.resize(size, Image.Resampling.LANCZOS)


def load_config(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Config must include a non-empty 'items' list.")
    for number, item in enumerate(items, 1):
        missing = [key for key in ("image", "title", "highlight", "improvement") if not item.get(key)]
        if missing:
            raise ValueError(f"Item {number} is missing: {', '.join(missing)}")
        if not Path(item["image"]).is_file():
            raise FileNotFoundError(f"Item {number} image does not exist: {item['image']}")
    return data


def render(data: dict, output: Path) -> None:
    items = data["items"]
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#efefed")
    draw = ImageDraw.Draw(canvas)
    block_h = HEIGHT // len(items)
    review_left, review_right = 150, WIDTH - 150

    for index, item in enumerate(items, 1):
        top = (index - 1) * block_h
        draw.rectangle((0, top, WIDTH, top + block_h), fill="#f4f3f0")
        draw.polygon([(0, top + 68), (WIDTH, top + 18), (WIDTH, top + 160), (0, top + 220)], fill=ORANGE)
        draw.polygon([(92, top + 48), (WIDTH - 100, top + 48), (WIDTH - 100, top + 162), (92, top + 205)], fill=PAPER, outline=INK)
        draw.text((120, top + 72), f"{index:02}", font=font(46), fill=ORANGE)
        draw.text((260, top + 67), item["title"], font=font(62), fill=INK)
        draw.text((WIDTH - 490, top + 136), "LIXIANG · DESIGN REVIEW", font=font(25), fill=INK)
        draw.text((240, top + 222), "FAST STUDIO / AUTUMN WORKS", font=font(23), fill=MUTED)
        draw.rectangle((240, top + 256, 358, top + 268), fill=INK)
        draw.rectangle((370, top + 256, 510, top + 268), fill=ORANGE)

        source = Image.open(item["image"]).convert("RGB")
        image_top = top + 302
        image = fit_image(source, 1320, int(block_h * 0.44))
        image_x = (WIDTH - image.width) // 2
        draw.rectangle((image_x - 12, image_top - 12, image_x + image.width + 12, image_top + image.height + 12), fill=INK)
        canvas.paste(image, (image_x, image_top))
        draw.rectangle((image_x, image_top, image_x + image.width, image_top + image.height), outline=PAPER, width=4)

        review_top = image_top + image.height + 52
        text_x, content_width = review_left + 36, review_right - review_left - 96
        para_face, line_h = font(48), 57
        high_lines = wrap(draw, item["highlight"], para_face, content_width)
        improve_lines = wrap(draw, item["improvement"], para_face, content_width)
        highlight_h = 87 + len(high_lines) * line_h + 20
        improve_top = review_top + highlight_h + 30
        footer_y = top + block_h - 90
        required_bottom = improve_top + 87 + len(improve_lines) * line_h + 20
        if required_bottom > footer_y:
            raise ValueError(f"Item {index} text is too long for its panel; shorten the two paragraphs.")

        draw.rectangle((review_left, review_top, review_right, review_top + highlight_h), fill=ORANGE)
        draw.rectangle((text_x, review_top + 16, text_x + 218, review_top + 69), fill=INK)
        draw.text((text_x + 18, review_top + 19), "方案亮点", font=font(40), fill=PAPER)
        y = review_top + 87
        for line in high_lines:
            draw.text((text_x, y), line, font=para_face, fill=PAPER)
            y += line_h

        draw.rectangle((review_left, improve_top, review_right, footer_y), fill=PAPER, outline=INK, width=3)
        draw.rectangle((text_x, improve_top + 16, text_x + 218, improve_top + 69), fill=INK)
        draw.rectangle((text_x + 232, improve_top + 38, review_right - 22, improve_top + 50), fill=ORANGE)
        draw.text((text_x + 18, improve_top + 19), "改进建议", font=font(40), fill=PAPER)
        y = improve_top + 87
        for line in improve_lines:
            draw.text((text_x, y), line, font=para_face, fill=INK)
            y += line_h

        draw.text((review_left, top + block_h - 57), "LiXiang Design  /  Fast Studio Review", font=font(22), fill=MUTED)
        if index < len(items):
            draw.line((240, top + block_h - 1, WIDTH - 240, top + block_h - 1), fill=ORANGE, width=4)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=95, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    output = Path(config.get("output", "architecture-review-long-image.png"))
    render(config, output)
    print(f"Saved {output.resolve()} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
