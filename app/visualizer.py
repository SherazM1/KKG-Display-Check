from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Optional

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
_DEFAULT_ZONE_MODES = {
    "header": "graphic",
    "body_panels": "color",
    "shelf_lips": "graphic",
    "base": "color",
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


def _white_background(size: tuple[int, int]) -> Image.Image:
    return Image.new("RGBA", size, (255, 255, 255, 255))


def _extract_line_art(base: Image.Image, *, opacity: float = 0.40) -> Image.Image:
    rgba_base = base.convert("RGBA")
    grayscale = rgba_base.convert("L")
    original_alpha = rgba_base.getchannel("A")
    opacity = max(0.0, min(1.0, opacity))

    computed_alpha = Image.new("L", rgba_base.size)
    computed_alpha.putdata(
        [
            round(max(0, min(255, (185 - luminance) * 2.4)) * (alpha / 255) * opacity)
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


def _mask_to_alpha(mask_source: Image.Image) -> Image.Image:
    rgba_mask = mask_source.convert("RGBA")
    alpha = rgba_mask.getchannel("A")
    if alpha.getextrema()[0] < 255:
        return alpha
    return rgba_mask.convert("L")


def _solid_fill(size: tuple[int, int], color_hex: str) -> Image.Image:
    try:
        return Image.new("RGBA", size, color_hex)
    except ValueError:
        return Image.new("RGBA", size, "#000000")


def _open_reference_image(image_file: Optional[BinaryIO]) -> Optional[Image.Image]:
    if image_file is None:
        return None
    try:
        if hasattr(image_file, "seek"):
            image_file.seek(0)
        with Image.open(image_file) as source:
            return source.convert("RGBA")
    except Exception:
        return None


def extract_reference_art_crop(image_file_or_image: BinaryIO | Image.Image) -> Image.Image:
    if isinstance(image_file_or_image, Image.Image):
        source = image_file_or_image.convert("RGBA")
    else:
        opened = _open_reference_image(image_file_or_image)
        if opened is None:
            raise ValueError("Could not open reference image.")
        source = opened

    meaningful = Image.new("L", source.size)
    meaningful.putdata(
        [
            255
            if alpha >= 32
            and not (red > 242 and green > 242 and blue > 242)
            and not (
                max(red, green, blue) > 224
                and max(red, green, blue) - min(red, green, blue) < 18
            )
            else 0
            for red, green, blue, alpha in source.getdata()
        ]
    )
    bbox = _largest_component_bbox(meaningful)
    if not bbox:
        return source

    left, top, right, bottom = bbox
    pad_x = max(4, round((right - left) * 0.04))
    pad_y = max(4, round((bottom - top) * 0.04))
    return source.crop(
        (
            max(0, left - pad_x),
            max(0, top - pad_y),
            min(source.width, right + pad_x),
            min(source.height, bottom + pad_y),
        )
    )


def _largest_component_bbox(mask: Image.Image) -> Optional[tuple[int, int, int, int]]:
    width, height = mask.size
    scale = min(1.0, 320 / max(width, height))
    if scale < 1.0:
        reduced = mask.resize(
            (max(1, round(width * scale)), max(1, round(height * scale))),
            Image.Resampling.NEAREST,
        )
    else:
        reduced = mask

    rw, rh = reduced.size
    pixels = reduced.load()
    visited: set[tuple[int, int]] = set()
    largest: tuple[int, int, int, int, int] | None = None

    for y in range(rh):
        for x in range(rw):
            if pixels[x, y] == 0 or (x, y) in visited:
                continue

            stack = [(x, y)]
            visited.add((x, y))
            min_x = max_x = x
            min_y = max_y = y
            count = 0

            while stack:
                cx, cy = stack.pop()
                count += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for nx in range(max(0, cx - 1), min(rw, cx + 2)):
                    for ny in range(max(0, cy - 1), min(rh, cy + 2)):
                        if pixels[nx, ny] and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            stack.append((nx, ny))

            if largest is None or count > largest[0]:
                largest = (count, min_x, min_y, max_x + 1, max_y + 1)

    if largest is None:
        return None

    _, left, top, right, bottom = largest
    if scale < 1.0:
        return (
            max(0, round(left / scale)),
            max(0, round(top / scale)),
            min(width, round(right / scale)),
            min(height, round(bottom / scale)),
        )
    return (left, top, right, bottom)


def derive_reference_art_regions(reference_art: Image.Image) -> dict[str, Image.Image]:
    art = reference_art.convert("RGBA")
    width, height = art.size
    if width <= 0 or height <= 0:
        return {"header_art": art, "shelf_strip": art, "base_strip": art}

    header_top = round(height * 0.10)
    header_bottom = max(header_top + 1, round(height * 0.62))
    lower_third = round(height * 0.60)
    base_top = round(height * 0.72)

    return {
        "header_art": art.crop((0, header_top, width, header_bottom)),
        "shelf_strip": art.crop((0, lower_third, width, height)),
        "base_strip": art.crop((0, base_top, width, height)),
    }


def _mask_bbox(mask: Image.Image) -> Optional[tuple[int, int, int, int]]:
    return mask.getbbox()


def _cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    if target_w <= 0 or target_h <= 0:
        return Image.new("RGBA", size, (0, 0, 0, 0))

    source_w, source_h = image.size
    scale = max(target_w / source_w, target_h / source_h)
    resized = image.resize(
        (max(1, round(source_w * scale)), max(1, round(source_h * scale))),
        Image.Resampling.LANCZOS,
    )
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def _repeat_strip(strip: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    fitted = _cover_resize(strip, (max(1, round(strip.width * target_h / max(strip.height, 1))), target_h))
    repeated = Image.new("RGBA", size, (0, 0, 0, 0))
    x = 0
    while x < target_w:
        repeated.alpha_composite(fitted, (x, 0))
        x += fitted.width
    return repeated.crop((0, 0, target_w, target_h))


def _graphic_fill(size: tuple[int, int], mask: Image.Image, graphic: Image.Image, zone_key: str) -> Optional[Image.Image]:
    bbox = _mask_bbox(mask)
    if not bbox:
        return None

    left, top, right, bottom = bbox
    fill_size = (right - left, bottom - top)
    if zone_key in {"shelf_lips", "base"}:
        fill = _repeat_strip(graphic, fill_size)
    else:
        fill = _cover_resize(graphic, fill_size)

    graphic_fill = Image.new("RGBA", size, (0, 0, 0, 0))
    graphic_fill.alpha_composite(fill, (left, top))
    return graphic_fill


def _shade_fill_with_base(fill: Image.Image, base: Image.Image, *, strength: float = 0.55) -> Image.Image:
    fill_rgb = fill.convert("RGB")
    base_luma = base.convert("L")
    strength = max(0.0, min(1.0, strength))

    shaded = Image.new("RGB", fill.size)
    shaded.putdata(
        [
            (
                round(red * ((1 - strength) + strength * (luma / 255))),
                round(green * ((1 - strength) + strength * (luma / 255))),
                round(blue * ((1 - strength) + strength * (luma / 255))),
            )
            for (red, green, blue), luma in zip(fill_rgb.getdata(), base_luma.getdata())
        ]
    )
    result = shaded.convert("RGBA")
    result.putalpha(fill.getchannel("A"))
    return result


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
    reference_image: Optional[BinaryIO] = None,
    zone_modes: Optional[dict[str, str]] = None,
    overlay_opacity: float = 0.70,
) -> Image.Image:
    template = get_template(template_id)
    with Image.open(template["base_image"]) as base_source:
        base = base_source.convert("RGBA")

    reference = _open_reference_image(reference_image)
    reference_art = extract_reference_art_crop(reference) if reference is not None else None
    regions = derive_reference_art_regions(reference_art) if reference_art is not None else {}
    modes = {**_DEFAULT_ZONE_MODES, **(zone_modes or {})}
    result = _white_background(base.size)
    result.alpha_composite(base)

    for zone_key in _RENDER_ORDER:
        zone = template["zones"][zone_key]
        with Image.open(zone["mask"]) as mask_source:
            mask = _mask_to_alpha(mask_source)
        if mask.size != base.size:
            mask = mask.resize(base.size, Image.Resampling.LANCZOS)

        fill = _solid_fill(base.size, str(zone_colors.get(zone_key) or "#000000"))
        if modes.get(zone_key) == "graphic" and reference_art is not None:
            graphic_source = {
                "header": regions.get("header_art"),
                "shelf_lips": regions.get("shelf_strip"),
                "base": regions.get("base_strip"),
                "body_panels": reference_art,
            }.get(zone_key)
            graphic_fill = _graphic_fill(base.size, mask, graphic_source, zone_key) if graphic_source is not None else None
            if graphic_fill is not None:
                fill = graphic_fill

        shaded_fill = _shade_fill_with_base(fill, base, strength=overlay_opacity)
        clipped_fill = Image.new("RGBA", base.size, (0, 0, 0, 0))
        clipped_fill.paste(shaded_fill, mask=mask)
        result.alpha_composite(clipped_fill)

    result.alpha_composite(_extract_line_art(base, opacity=0.18))

    return result


def pil_image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
