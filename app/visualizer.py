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
    overlay_opacity: float = 0.55,
) -> Image.Image:
    template = get_template(template_id)
    with Image.open(template["base_image"]) as base_source:
        base = base_source.convert("RGBA")
    opacity = max(0.0, min(1.0, overlay_opacity))

    result = base.copy()
    for zone_key, zone in template["zones"].items():
        with Image.open(zone["mask"]) as mask_source:
            mask = mask_source.convert("L")
        if mask.size != base.size:
            mask = mask.resize(base.size, Image.Resampling.LANCZOS)

        zone_color = str(zone_colors.get(zone_key) or "#000000")
        rgb = Image.new("RGBA", (1, 1), zone_color).getpixel((0, 0))[:3]
        overlay = Image.new("RGBA", base.size, (*rgb, 255))
        alpha_mask = mask.point(lambda value: round(value * opacity))
        result = Image.composite(overlay, result, alpha_mask)

    return result


def pil_image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
