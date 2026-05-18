from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from PIL import Image

DEFAULT_PALETTE = ["#6F7F35", "#D8C58A", "#F4E8D0", "#B83A68", "#7A2E2E", "#111827"]

_TEMPLATES = {
    "sidekick_shelves": {
        "template_id": "sidekick_shelves",
        "base_image": "assets/visual_templates/sidekick_shelves/base.png",
        "zones": {
            "header": {
                "label": "Header",
                "mask": "assets/visual_templates/sidekick_shelves/mask_header.png",
            },
            "body_panels": {
                "label": "Body Panels",
                "mask": "assets/visual_templates/sidekick_shelves/mask_body_panels.png",
            },
            "shelf_lips": {
                "label": "Shelf Lips / Front Strips",
                "mask": "assets/visual_templates/sidekick_shelves/mask_shelf_lips.png",
            },
            "base": {
                "label": "Base",
                "mask": "assets/visual_templates/sidekick_shelves/mask_base.png",
            },
        },
    }
}

_RENDER_ORDER = ("body_panels", "base", "header", "shelf_lips")


def get_template(template_id: str) -> dict:
    try:
        return _TEMPLATES[template_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported visual template: {template_id}") from exc


def template_available(template_id: str) -> bool:
    try:
        template = get_template(template_id)
    except ValueError:
        return False

    required_paths = [template["base_image"]]
    required_paths.extend(zone["mask"] for zone in template["zones"].values())
    return all(Path(path).is_file() for path in required_paths)


def _hex_from_rgb(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _color_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right)) ** 0.5


def _white_background(size: tuple[int, int]) -> Image.Image:
    return Image.new("RGBA", size, (255, 255, 255, 255))


def _extract_line_art(base: Image.Image) -> Image.Image:
    rgba_base = base.convert("RGBA")
    grayscale = rgba_base.convert("L")
    original_alpha = rgba_base.getchannel("A")

    computed_alpha = Image.new("L", rgba_base.size)
    computed_alpha.putdata(
        [
            round(max(0, min(255, (220 - luminance) * 2.0)) * (alpha / 255))
            for luminance, alpha in zip(grayscale.getdata(), original_alpha.getdata())
        ]
    )

    line_art = rgba_base.copy()
    line_art.putalpha(computed_alpha)
    return line_art


def _load_piece_layer(path: str, base_size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as source:
        piece = source.convert("RGBA")
    if piece.size != base_size:
        piece = piece.resize(base_size, Image.Resampling.LANCZOS)
    return piece


def _piece_alpha(piece: Image.Image) -> Image.Image:
    rgba_piece = piece.convert("RGBA")
    alpha = rgba_piece.getchannel("A")
    if alpha.getextrema()[0] < 255:
        return alpha
    return rgba_piece.convert("L")


def _tint_piece(piece: Image.Image, color_hex: str, *, strength: float = 0.72) -> Image.Image:
    rgba_piece = piece.convert("RGBA")
    alpha = _piece_alpha(rgba_piece)
    strength = max(0.0, min(1.0, strength))

    try:
        color = Image.new("RGB", rgba_piece.size, color_hex)
    except ValueError:
        color = Image.new("RGB", rgba_piece.size, "#000000")

    original_rgb = rgba_piece.convert("RGB")
    tinted_rgb = Image.blend(original_rgb, color, strength)
    tinted_piece = tinted_rgb.convert("RGBA")
    tinted_piece.putalpha(alpha)
    return tinted_piece


def extract_palette(image_file: BinaryIO, *, max_colors: int = 6) -> list[str]:
    try:
        if hasattr(image_file, "seek"):
            image_file.seek(0)

        with Image.open(image_file) as source:
            image = source.convert("RGBA")
            image.thumbnail((240, 240))

            pixels: list[tuple[int, int, int]] = []
            for red, green, blue, alpha in image.getdata():
                if alpha < 32:
                    continue
                if red >= 242 and green >= 242 and blue >= 242:
                    continue
                pixels.append((red, green, blue))

        if not pixels:
            return DEFAULT_PALETTE.copy()

        compact = Image.new("RGB", (len(pixels), 1))
        compact.putdata(pixels)
        quantized = compact.quantize(colors=max(max_colors * 3, max_colors), method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()
        if not palette:
            return DEFAULT_PALETTE.copy()

        ranked_colors: list[tuple[int, tuple[int, int, int]]] = []
        for count, palette_idx in quantized.getcolors() or []:
            start = palette_idx * 3
            rgb = tuple(palette[start : start + 3])
            if len(rgb) == 3:
                ranked_colors.append((count, rgb))

        ranked_colors.sort(reverse=True)

        unique_colors: list[tuple[int, int, int]] = []
        for _, rgb in ranked_colors:
            if all(_color_distance(rgb, existing) >= 42 for existing in unique_colors):
                unique_colors.append(rgb)
            if len(unique_colors) >= max_colors:
                break

        return [_hex_from_rgb(rgb) for rgb in unique_colors] or DEFAULT_PALETTE.copy()
    except Exception:
        return DEFAULT_PALETTE.copy()


def render_preview(
    template_id: str,
    zone_colors: dict[str, str],
    *,
    overlay_opacity: float = 0.70,
) -> Image.Image:
    template = get_template(template_id)
    with Image.open(template["base_image"]) as base_source:
        base = base_source.convert("RGBA")

    result = _white_background(base.size)
    for zone_key in _RENDER_ORDER:
        zone = template["zones"][zone_key]
        piece = _load_piece_layer(zone["mask"], base.size)
        tinted_piece = _tint_piece(
            piece,
            str(zone_colors.get(zone_key) or "#000000"),
            strength=overlay_opacity,
        )
        result.alpha_composite(tinted_piece)

    result.alpha_composite(_extract_line_art(base))

    return result


def pil_image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
