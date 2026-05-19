from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Optional

from PIL import Image, ImageDraw

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
    "base": "texture",
}

_SIDEKICK_SALES_REGIONS = {
    "header": (0.293, 0.054, 0.684, 0.181),
    "body_panels": (0.267, 0.168, 0.774, 0.872),
    "base": (0.247, 0.864, 0.787, 0.980),
    "side_panel_poly": (
        (0.650, 0.185),
        (0.779, 0.236),
        (0.786, 0.883),
        (0.674, 0.966),
        (0.636, 0.330),
    ),
}

_SIDEKICK_FALLBACK_COLORS = {
    "header": "#D8C58A",
    "body_panels": "#626B37",
    "side_panel": "#56612F",
    "shelf_lips": "#C27D8E",
    "base": "#5B6433",
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


def _sanitized_mask(mask_source: Image.Image, size: tuple[int, int], *, min_coverage: float = 0.002, max_coverage: float = 0.75) -> Optional[Image.Image]:
    mask = _mask_to_alpha(mask_source)
    if mask.size != size:
        mask = mask.resize(size, Image.Resampling.LANCZOS)
    mask = mask.point(lambda value: 255 if value >= 32 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return None
    histogram = mask.histogram()
    coverage = sum(count for value, count in enumerate(histogram) if value > 0) / (size[0] * size[1])
    if coverage < min_coverage or coverage > max_coverage:
        return None
    return mask


def build_color_fill(size: tuple[int, int], color_hex: str) -> Image.Image:
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


def _scaled_box(size: tuple[int, int], box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    width, height = size
    left, top, right, bottom = box
    return (
        max(0, min(width, round(left * width))),
        max(0, min(height, round(top * height))),
        max(0, min(width, round(right * width))),
        max(0, min(height, round(bottom * height))),
    )


def _scaled_polygon(size: tuple[int, int], points: tuple[tuple[float, float], ...]) -> list[tuple[int, int]]:
    width, height = size
    return [(round(x * width), round(y * height)) for x, y in points]


def _box_mask(size: tuple[int, int], box: tuple[int, int, int, int]) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rectangle(box, fill=255)
    return mask


def _polygon_mask(size: tuple[int, int], points: list[tuple[int, int]]) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask


def _safe_fraction_crop(image: Optional[Image.Image], box: tuple[float, float, float, float]) -> Optional[Image.Image]:
    if image is None:
        return None
    source = image.convert("RGBA")
    crop_box = _scaled_box(source.size, box)
    left, top, right, bottom = crop_box
    if right <= left or bottom <= top:
        return None
    return source.crop(crop_box)


def _mask_component_boxes(mask: Image.Image, *, min_area: int = 1200) -> list[tuple[int, int, int, int]]:
    width, height = mask.size
    pixels = mask.load()
    visited: set[tuple[int, int]] = set()
    boxes: list[tuple[int, int, int, int, int]] = []

    for y in range(height):
        for x in range(width):
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
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < width and 0 <= ny < height and pixels[nx, ny] and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        stack.append((nx, ny))

            if count >= min_area:
                boxes.append((min_y, min_x, min_y, max_x + 1, max_y + 1))

    boxes.sort()
    return [(left, top, right, bottom) for _, left, top, right, bottom in boxes]


def _composite_clipped(result: Image.Image, base: Image.Image, fill: Image.Image, mask: Image.Image, *, strength: float, opacity: float) -> None:
    shaded = _shade_fill_with_base(fill, base, strength=strength, style_opacity=opacity)
    clipped = Image.new("RGBA", base.size, (0, 0, 0, 0))
    clipped.paste(shaded, mask=mask)
    result.alpha_composite(clipped)


def _art_fill_for_box(size: tuple[int, int], box: tuple[int, int, int, int], artwork: Image.Image, *, fit_mode: str = "fill_crop") -> Image.Image:
    left, top, right, bottom = box
    fill_size = (max(1, right - left), max(1, bottom - top))
    if fit_mode == "tile":
        fill = _repeat_strip(artwork, fill_size)
    elif fit_mode in {"fit", "fit_center"}:
        fill = _fit_center(artwork, fill_size)
    else:
        fill = _cover_resize(artwork, fill_size)
    placed = Image.new("RGBA", size, (0, 0, 0, 0))
    placed.alpha_composite(fill, (left, top))
    return placed


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


def _fit_center(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    if target_w <= 0 or target_h <= 0:
        return Image.new("RGBA", size, (0, 0, 0, 0))

    source_w, source_h = image.size
    scale = min(target_w / source_w, target_h / source_h)
    resized = image.resize(
        (max(1, round(source_w * scale)), max(1, round(source_h * scale))),
        Image.Resampling.LANCZOS,
    )
    result = Image.new("RGBA", size, (0, 0, 0, 0))
    result.alpha_composite(resized, ((target_w - resized.width) // 2, (target_h - resized.height) // 2))
    return result


def _repeat_strip(strip: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    fitted = _cover_resize(strip, (max(1, round(strip.width * target_h / max(strip.height, 1))), target_h))
    repeated = Image.new("RGBA", size, (0, 0, 0, 0))
    x = 0
    while x < target_w:
        repeated.alpha_composite(fitted, (x, 0))
        x += fitted.width
    return repeated.crop((0, 0, target_w, target_h))


def _place_fill_in_mask_bounds(
    size: tuple[int, int],
    mask: Image.Image,
    artwork: Image.Image,
    *,
    fit_mode: str,
) -> Optional[Image.Image]:
    bbox = _mask_bbox(mask)
    if not bbox:
        return None

    left, top, right, bottom = bbox
    fill_size = (right - left, bottom - top)
    if fit_mode == "tile":
        fill = _repeat_strip(artwork, fill_size)
    elif fit_mode in {"fit", "fit_center"}:
        fill = _fit_center(artwork, fill_size)
    else:
        fill = _cover_resize(artwork, fill_size)

    placed = Image.new("RGBA", size, (0, 0, 0, 0))
    placed.alpha_composite(fill, (left, top))
    return placed


def build_texture_fill(size: tuple[int, int], mask: Image.Image, texture: Image.Image, *, fit_mode: str) -> Optional[Image.Image]:
    return _place_fill_in_mask_bounds(size, mask, texture.convert("RGBA"), fit_mode=fit_mode)


def build_graphic_fill(size: tuple[int, int], mask: Image.Image, graphic: Image.Image, *, fit_mode: str) -> Optional[Image.Image]:
    return _place_fill_in_mask_bounds(size, mask, graphic.convert("RGBA"), fit_mode=fit_mode)


def _shade_fill_with_base(
    fill: Image.Image,
    base: Image.Image,
    *,
    strength: float = 0.55,
    style_opacity: float = 0.82,
) -> Image.Image:
    fill_rgb = fill.convert("RGB")
    base_rgb = base.convert("RGB")
    base_luma = base.convert("L")
    strength = max(0.0, min(1.0, strength))
    style_opacity = max(0.0, min(1.0, style_opacity))

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
    blended = Image.blend(base_rgb, shaded, style_opacity)
    result = blended.convert("RGBA")
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


def _sidekick_mask(template: dict, zone_key: str, size: tuple[int, int]) -> Optional[Image.Image]:
    zone = template["zones"].get(zone_key)
    if not zone:
        return None
    try:
        with Image.open(zone["mask"]) as mask_source:
            return _sanitized_mask(mask_source, size)
    except Exception:
        return None


def _sidekick_zone_color(zone_colors: dict[str, str], zone_key: str) -> str:
    color = str(zone_colors.get(zone_key) or _SIDEKICK_FALLBACK_COLORS.get(zone_key) or "#000000")
    try:
        Image.new("RGB", (1, 1), color)
        return color
    except ValueError:
        return _SIDEKICK_FALLBACK_COLORS.get(zone_key, "#000000")


def render_sales_mockup_preview(
    template_id: str,
    zone_colors: dict[str, str],
    *,
    reference_image: Optional[BinaryIO] = None,
    texture_image: Optional[BinaryIO] = None,
    graphic_image: Optional[BinaryIO] = None,
    zone_modes: Optional[dict[str, str]] = None,
    zone_config: Optional[dict[str, dict[str, str]]] = None,
    overlay_opacity: float = 0.70,
) -> Image.Image:
    if template_id != "sidekick_shelves":
        return render_preview(
            template_id,
            zone_colors,
            reference_image=reference_image,
            texture_image=texture_image,
            graphic_image=graphic_image,
            zone_modes=zone_modes,
            zone_config=zone_config,
            overlay_opacity=overlay_opacity,
        )

    template = get_template(template_id)
    with Image.open(template["base_image"]) as base_source:
        base = base_source.convert("RGBA")

    reference = _open_reference_image(reference_image)
    texture_source = _open_reference_image(texture_image) or reference
    graphic_source = _open_reference_image(graphic_image) or reference

    reference_header = _safe_fraction_crop(graphic_source or reference, (0.18, 0.06, 0.84, 0.40))
    reference_strip = _safe_fraction_crop(graphic_source or reference, (0.05, 0.34, 0.82, 0.58))
    reference_pattern = _safe_fraction_crop(texture_source or reference, (0.08, 0.58, 0.92, 0.86))

    result = _white_background(base.size)
    result.alpha_composite(base)

    body_color = _sidekick_zone_color(zone_colors, "body_panels")
    side_color = _sidekick_zone_color(zone_colors, "side_panel") if "side_panel" in zone_colors else body_color
    header_color = _sidekick_zone_color(zone_colors, "header")
    shelf_color = _sidekick_zone_color(zone_colors, "shelf_lips")
    base_color = _sidekick_zone_color(zone_colors, "base")

    body_mask = _sidekick_mask(template, "body_panels", base.size) or _box_mask(base.size, _scaled_box(base.size, _SIDEKICK_SALES_REGIONS["body_panels"]))
    side_mask = _polygon_mask(base.size, _scaled_polygon(base.size, _SIDEKICK_SALES_REGIONS["side_panel_poly"]))
    header_mask = _sidekick_mask(template, "header", base.size) or _box_mask(base.size, _scaled_box(base.size, _SIDEKICK_SALES_REGIONS["header"]))
    shelf_mask = _sidekick_mask(template, "shelf_lips", base.size)
    base_mask = _sidekick_mask(template, "base", base.size) or _box_mask(base.size, _scaled_box(base.size, _SIDEKICK_SALES_REGIONS["base"]))

    _composite_clipped(
        result,
        base,
        build_color_fill(base.size, body_color),
        body_mask,
        strength=0.46,
        opacity=max(0.55, min(0.78, overlay_opacity)),
    )
    _composite_clipped(
        result,
        base,
        build_color_fill(base.size, side_color),
        side_mask,
        strength=0.42,
        opacity=0.62,
    )

    if reference_pattern is not None:
        base_fill = _art_fill_for_box(base.size, base_mask.getbbox() or _scaled_box(base.size, _SIDEKICK_SALES_REGIONS["base"]), reference_pattern)
    else:
        base_fill = build_color_fill(base.size, base_color)
    _composite_clipped(result, base, base_fill, base_mask, strength=0.48, opacity=0.72)

    if reference_header is not None:
        header_fill = _art_fill_for_box(base.size, header_mask.getbbox() or _scaled_box(base.size, _SIDEKICK_SALES_REGIONS["header"]), reference_header)
    else:
        header_fill = build_color_fill(base.size, header_color)
    _composite_clipped(result, base, header_fill, header_mask, strength=0.35, opacity=0.82)

    if shelf_mask is not None:
        shelf_fill = Image.new("RGBA", base.size, (0, 0, 0, 0))
        shelf_boxes = _mask_component_boxes(shelf_mask, min_area=max(500, round(base.width * base.height * 0.00035)))
        if not shelf_boxes:
            shelf_boxes = [shelf_mask.getbbox()] if shelf_mask.getbbox() else []
        for box in shelf_boxes:
            if reference_strip is not None:
                component_fill = _art_fill_for_box(base.size, box, reference_strip, fit_mode="fill_crop")
            else:
                component_fill = build_color_fill(base.size, shelf_color)
            shelf_fill.alpha_composite(component_fill)
        _composite_clipped(result, base, shelf_fill, shelf_mask, strength=0.28, opacity=0.88)

    result.alpha_composite(_extract_line_art(base, opacity=0.20))
    return result


def render_preview(
    template_id: str,
    zone_colors: dict[str, str],
    *,
    reference_image: Optional[BinaryIO] = None,
    texture_image: Optional[BinaryIO] = None,
    graphic_image: Optional[BinaryIO] = None,
    zone_modes: Optional[dict[str, str]] = None,
    zone_config: Optional[dict[str, dict[str, str]]] = None,
    overlay_opacity: float = 0.70,
) -> Image.Image:
    template = get_template(template_id)
    with Image.open(template["base_image"]) as base_source:
        base = base_source.convert("RGBA")

    reference = _open_reference_image(reference_image)
    texture_source = _open_reference_image(texture_image) or reference
    graphic_source = _open_reference_image(graphic_image) or reference
    reference_art = extract_reference_art_crop(reference) if reference is not None else None
    texture_art = extract_reference_art_crop(texture_source) if texture_source is not None else None
    graphic_art = extract_reference_art_crop(graphic_source) if graphic_source is not None else None
    regions = derive_reference_art_regions(reference_art) if reference_art is not None else {}
    texture_regions = derive_reference_art_regions(texture_art) if texture_art is not None else {}
    graphic_regions = derive_reference_art_regions(graphic_art) if graphic_art is not None else {}
    modes = {**_DEFAULT_ZONE_MODES, **(zone_modes or {})}
    result = _white_background(base.size)
    result.alpha_composite(base)

    for zone_key in _RENDER_ORDER:
        zone = template["zones"][zone_key]
        with Image.open(zone["mask"]) as mask_source:
            mask = _mask_to_alpha(mask_source)
        if mask.size != base.size:
            mask = mask.resize(base.size, Image.Resampling.LANCZOS)

        config = (zone_config or {}).get(zone_key, {})
        mode = str(config.get("mode") or modes.get(zone_key) or "color").lower()
        color = str(config.get("color") or zone_colors.get(zone_key) or "#000000")
        texture_fit = str(config.get("texture_fit_mode") or config.get("fit_mode") or "fill_crop").lower()
        graphic_fit = str(config.get("graphic_fit_mode") or config.get("fit_mode") or "fill_crop").lower()

        fill = build_color_fill(base.size, color)
        if mode == "texture" and texture_art is not None:
            texture_source_for_zone = {
                "header": texture_regions.get("header_art"),
                "shelf_lips": texture_regions.get("shelf_strip"),
                "base": texture_regions.get("base_strip"),
                "body_panels": texture_art,
            }.get(zone_key)
            texture_fill = (
                build_texture_fill(base.size, mask, texture_source_for_zone, fit_mode=texture_fit)
                if texture_source_for_zone is not None
                else None
            )
            if texture_fill is not None:
                fill = texture_fill
        elif mode == "graphic" and graphic_art is not None:
            graphic_source_for_zone = {
                "header": graphic_regions.get("header_art") or regions.get("header_art"),
                "shelf_lips": graphic_regions.get("shelf_strip") or regions.get("shelf_strip"),
                "base": graphic_regions.get("base_strip") or regions.get("base_strip"),
                "body_panels": graphic_art,
            }.get(zone_key)
            graphic_fill = (
                build_graphic_fill(base.size, mask, graphic_source_for_zone, fit_mode=graphic_fit)
                if graphic_source_for_zone is not None
                else None
            )
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
