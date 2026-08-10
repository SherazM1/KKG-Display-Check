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
BASE_TEMPLATE = ASSET_ROOT / "base.png"
REFERENCE_IMAGE = ASSET_ROOT / "referenceimagesample_dc2.webp"
STATIC_MOCKUP = ASSET_ROOT / "staticreference.png"
