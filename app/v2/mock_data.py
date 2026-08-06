"""Static copy, defaults, and asset paths for the v2 UI shell."""

from pathlib import Path


PROJECT_DEFAULTS = {
    "project_name": "Display Check Sample",
    "display_type": "Sidekick",
    "quantity": 500,
    "print_type": "Litho Laminate",
    "shipping_packout": "Flat Pack",
    "width": 20,
    "height": 48,
    "depth": 12,
}

ESTIMATE_SAMPLE = {
    "Display Type": "Sidekick",
    "Complexity": "Medium",
    "Ballpark Unit Range": "$48-$64",
    "Program Range": "$24,000-$32,000",
    "Confidence": "Medium",
    "Review Required": "Yes",
}

ESTIMATE_ASSUMPTIONS = [
    "four shelves",
    "reinforced base",
    "flat-packed shipping",
    "full-color print treatment",
]

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
