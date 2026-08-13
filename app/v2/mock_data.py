"""Static options and asset paths for the v2 UI shell."""

from pathlib import Path


DISPLAY_OPTIONS = ["Sidekick", "PDQ", "Half Pallet", "Quarter Pallet"]
PRINT_TYPE_OPTIONS = ["Litho Laminate", "Digital Print", "Flexo Print"]
SHIPPING_PACKOUT_OPTIONS = ["Flat Pack", "Assembled", "Retail Ready"]

PALETTE_SWATCHES = [
    {"label": "Olive green", "hex": "#7A823B"},
    {"label": "Dark green", "hex": "#304C2F"},
    {"label": "Muted gold", "hex": "#C4A85B"},
    {"label": "Strawberry pink", "hex": "#D46F83"},
]

ASSET_ROOT = Path("assets") / "visual_templates" / "sidekick"


def _preferred_asset(preferred_name: str, fallback_name: str) -> Path:
    """Return a preferred asset when present, otherwise its stable fallback."""
    preferred = ASSET_ROOT / preferred_name
    if preferred.exists():
        return preferred
    return ASSET_ROOT / fallback_name


BASE_TEMPLATE = _preferred_asset("base_transparent.png", "base.png")
REFERENCE_IMAGE = ASSET_ROOT / "referenceimagesample_dc2.webp"
REFERENCE_IMAGE_NAME = "Demo reference image"
STATIC_MOCKUP = _preferred_asset("staticreference_transparent.png", "staticreference.png")
