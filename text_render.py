from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int) -> ImageFont.ImageFont:
    font_candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    for font_path in font_candidates:
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size=size)
    return ImageFont.load_default()


def draw_unicode_text(
    image: np.ndarray,
    text: str,
    org: tuple[int, int],
    color: tuple[int, int, int],
    *,
    rgb_input: bool,
    font_size: int = 30,
) -> np.ndarray:
    """Draw unicode text on numpy image array (RGB or BGR)."""
    if rgb_input:
        pil_img = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_img)
        draw.text(org, text, fill=color, font=_load_font(font_size))
        return np.array(pil_img)

    pil_img = Image.fromarray(image[:, :, ::-1])  # BGR -> RGB
    draw = ImageDraw.Draw(pil_img)
    draw.text(org, text, fill=color, font=_load_font(font_size))
    return np.array(pil_img)[:, :, ::-1]  # RGB -> BGR
