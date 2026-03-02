# tools/split_pdq_catalog.py
"""
Split `data/catalog/pdq.json` into 4 PDQ-specific catalogs and duplicate footprint into Raw/Clean.

Run (from repo root):
  python tools/split_pdq_catalog.py

Outputs:
  data/catalog/pdq_clipped.json
  data/catalog/pdq_angled.json
  data/catalog/pdq_square.json
  data/catalog/pdq_standard.json

Notes:
- Does NOT invent new pricing. Raw/Clean footprint parts copy the existing base footprint base_value.
- Updates meta.display_label + meta.hero_image to your PDQ images.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "catalog" / "pdq.json"
OUT_DIR = ROOT / "data" / "catalog"

PDQ_VARIANTS: List[Tuple[str, str, str]] = [
    ("clipped", "Clipped PDQ Tray", "assets/references/pdq/clipped_pdq_tray.png"),
    ("angled", "Angled PDQ Tray", "assets/references/pdq/digital_pdq_tray.png"),
    ("square", "Square PDQ Tray", "assets/references/pdq/square_pdq_tray.png"),
    ("standard", "Standard PDQ Tray", "assets/references/pdq/standarddclub_pdq_tray.png"),
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _find_control(catalog: Dict[str, Any], control_id: str) -> Optional[Dict[str, Any]]:
    for c in catalog.get("controls", []) or []:
        if c.get("id") == control_id:
            return c
    return None


def _ensure_edge_control(catalog: Dict[str, Any]) -> None:
    if _find_control(catalog, "edge") is not None:
        return

    controls = catalog.setdefault("controls", [])
    fp_idx = next((i for i, c in enumerate(controls) if c.get("id") == "footprint"), len(controls))

    edge_control = {
        "id": "edge",
        "label": "Edge",
        "type": "single",
        "required": True,
        "options": [
            {"key": "raw", "label": "Raw", "base_value": 0},
            {"key": "clean", "label": "Clean", "base_value": 0},
        ],
        "notes": "Affects the footprint priced part (Raw vs Clean).",
    }
    controls.insert(fp_idx + 1, edge_control)


def _duplicate_footprint_options_raw_clean(catalog: Dict[str, Any]) -> None:
    fp = _find_control(catalog, "footprint")
    if not fp:
        raise ValueError("PDQ catalog missing control id='footprint'.")

    options = fp.get("options", []) or []
    if not options:
        raise ValueError("PDQ footprint control has no options.")

    keys = [str(o.get("key", "")) for o in options]
    if any(k.endswith("-raw") for k in keys) or any(k.endswith("-clean") for k in keys):
        return

    new_opts: List[Dict[str, Any]] = []
    for opt in options:
        base_key = str(opt.get("key"))
        raw_opt = copy.deepcopy(opt)
        clean_opt = copy.deepcopy(opt)
        raw_opt["key"] = f"{base_key}-raw"
        clean_opt["key"] = f"{base_key}-clean"
        new_opts.extend([raw_opt, clean_opt])

    fp["options"] = new_opts
    fp["notes"] = (
        (fp.get("notes") or "").strip()
        + " Defaults to Raw; Edge selection switches between Raw/Clean priced footprint."
    ).strip()


def _ensure_resolve_footprint_base_raw_clean(catalog: Dict[str, Any]) -> None:
    rules = catalog.setdefault("rules", {})
    r = rules.get("resolve_footprint_base")
    if not isinstance(r, dict):
        raise ValueError("PDQ catalog missing rules.resolve_footprint_base.")

    m = r.get("map", {}) or {}
    if any(str(k).endswith("-raw") for k in m) or any(str(k).endswith("-clean") for k in m):
        return

    new_map: Dict[str, Any] = {}
    for fp_key, part_key in m.items():
        fp_key_s = str(fp_key)
        part_key_s = str(part_key) if part_key is not None else None
        new_map[f"{fp_key_s}-raw"] = f"{part_key_s}-raw" if part_key_s else None
        new_map[f"{fp_key_s}-clean"] = f"{part_key_s}-clean" if part_key_s else None

    r["map"] = new_map


def _ensure_footprint_parts_raw_clean(catalog: Dict[str, Any]) -> None:
    rules = catalog.get("rules", {}) or {}
    r = rules.get("resolve_footprint_base", {}) or {}
    m = r.get("map", {}) or {}
    parts = catalog.setdefault("parts", {})

    for _, part_key in m.items():
        if part_key is None:
            continue

        pk = str(part_key)
        if pk in parts:
            continue

        if pk.endswith("-raw"):
            base_pk = pk.removesuffix("-raw")
            suffix_label = "Raw"
        elif pk.endswith("-clean"):
            base_pk = pk.removesuffix("-clean")
            suffix_label = "Clean"
        else:
            base_pk = pk
            suffix_label = ""

        base_part = parts.get(base_pk)
        if not isinstance(base_part, dict):
            raise ValueError(f"Missing base footprint part '{base_pk}' needed to create '{pk}'.")

        new_part = copy.deepcopy(base_part)
        if suffix_label:
            new_part["label"] = f'{new_part.get("label", base_pk)} ({suffix_label})'
        parts[pk] = new_part


def _build_variant(base: Dict[str, Any], variant_key: str, label: str, hero: str) -> Dict[str, Any]:
    cat = copy.deepcopy(base)

    meta = cat.setdefault("meta", {})
    meta["category"] = "pdq"
    meta["display_label"] = label
    meta["hero_image"] = hero
    meta["id"] = f"pdq-{variant_key}"

    _ensure_edge_control(cat)
    _duplicate_footprint_options_raw_clean(cat)
    _ensure_resolve_footprint_base_raw_clean(cat)
    _ensure_footprint_parts_raw_clean(cat)

    return cat


def main() -> None:
    if not IN_PATH.exists():
        raise SystemExit(f"Missing input file: {IN_PATH}")

    base = _load_json(IN_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for key, label, hero in PDQ_VARIANTS:
        out = _build_variant(base, variant_key=key, label=label, hero=hero)
        out_path = OUT_DIR / f"pdq_{key}.json"
        _dump_json(out_path, out)
        print(f"Wrote {out_path.relative_to(ROOT)}")

    print("Done.")


if __name__ == "__main__":
    main()