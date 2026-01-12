# pages/Display.py
# Catalog-driven PDQ UI + rule resolution + preview (includes footprint base; float weight input)
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

# ---------- Page setup ----------
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
      .kkg-tile { border:1px solid #e5e7eb; border-radius:12px; padding:12px; background:#ffffff; }
      .kkg-label { text-align:center; font-weight:700; font-size:16px; color:#3b3f46; margin:10px 0 10px; letter-spacing:0.5px; }
      .kkg-table th, .kkg-table td { padding:6px 8px; border-bottom:1px solid #f1f5f9; }
      .kkg-table th { text-align:left; color:#475569; font-weight:600; }
      .muted { color:#6b7280; }
      .pill { display:inline-block; padding:2px 8px; border:1px solid #e5e7eb; border-radius:999px; font-size:12px; margin-left:6px; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

CATALOG_PATH = "data/catalog/pdq.json"
ASSETS_ROOT = "assets/references"

# include your new folder "dumpbin"
ALLOWED_DIRS = {"pdq", "dumpbin", "pallet", "sidekick", "endcap", "display", "header"}

LABEL_OVERRIDES = {
    "digital_pdq_tray": "PDQ TRAY",
    "pdq-tray-standard": "PDQ TRAY",
    "dump_bin": "DUMP BIN",
    "dumpbin": "DUMP BIN",
}

# ---------- Helpers ----------
def load_catalog(path: str) -> Dict:
    if not os.path.isfile(path):
        st.error(f"Catalog not found at `{path}`. Add `data/catalog/pdq.json` and reload.")
        st.stop()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to parse `{path}`: {e}")
        st.stop()

@dataclass
class OptionTile:
    key: str
    label: str
    path: str
    category: str

def _prettify(stem: str) -> str:
    if stem in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[stem]
    s = stem.replace("_", " ").replace("-", " ").strip()
    return " ".join(w.capitalize() for w in s.split())

def scan_pngs() -> List[OptionTile]:
    opts: List[OptionTile] = []
    if not os.path.isdir(ASSETS_ROOT):
        return opts
    for cat in sorted(os.listdir(ASSETS_ROOT)):
        cat_path = os.path.join(ASSETS_ROOT, cat)
        if not (os.path.isdir(cat_path) and cat in ALLOWED_DIRS):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if not fname.lower().endswith(".png"):
                continue
            if fname.lower().startswith(("kkg-logo", "logo")):
                continue
            stem, _ = os.path.splitext(fname)
            path = os.path.join(cat_path, fname)
            try:
                Image.open(path).close()
            except Exception:
                continue
            opts.append(OptionTile(key=f"{cat}/{stem}", label=_prettify(stem), path=path, category=cat))
    return opts

def _find_control(catalog: Dict, control_id: str) -> Optional[Dict]:
    for c in catalog.get("controls", []):
        if c.get("id") == control_id:
            return c
    return None

def _footprint_dims(catalog: Dict, footprint_key: str) -> Tuple[Optional[int], Optional[int]]:
    fp = _find_control(catalog, "footprint")
    if not fp:
        return None, None
    for opt in fp.get("options", []):
        if opt.get("key") == footprint_key:
            dims = opt.get("dims", {})
            return dims.get("width_in"), dims.get("depth_in")
    return None, None

def _parts_value(catalog: Dict, part_key: str) -> float:
    try:
        return float(catalog.get("parts", {}).get(part_key, {}).get("base_value", 0) or 0)
    except Exception:
        return 0.0

def _round_display_weight(total_lbs: float, policy: Dict) -> str:
    step = policy.get("display_weight_round", 0.01)
    try:
        step = float(step)
    except Exception:
        step = 0.01
    s = f"{step:.10f}".rstrip("0").rstrip(".")
    decimals = len(s.split(".")[1]) if "." in s else 0
    fmt = f"{{:.{decimals}f}}"
    return fmt.format(total_lbs)

def _chunk(lst: List[OptionTile], n: int) -> List[List[OptionTile]]:
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def _fixed_preview(path: str, target_w: int = 320, target_h: int = 230) -> Image.Image:
    """
    Keeps tiles aligned by forcing every preview into the same pixel box.
    - no stretching
    - preserves aspect ratio
    - pads with white background
    """
    img = Image.open(path).convert("RGBA")
    # contain within box, then pad to exact size
    contained = ImageOps.contain(img, (target_w, target_h))
    padded = ImageOps.pad(contained, (target_w, target_h), color=(255, 255, 255))
    return padded.convert("RGB")

# ---------- Page header ----------
st.markdown("## Select the type of display")

# ---------- Gallery ----------
tiles = scan_pngs()

if not tiles:
    st.info(
        f"No PNGs found. Add images under `{ASSETS_ROOT}/<category>/...` "
        "(e.g., `assets/references/pdq/digital_pdq_tray.png`)."
    )
else:
    # force 2-per-row so PDQ + DUMP BIN sit together cleanly
    per_row = 2
    for row in _chunk(tiles, per_row):
        cols = st.columns(len(row), gap="large")  # IMPORTANT: no empty columns -> no blank boxes
        for c, t in zip(cols, row):
            with c:
                st.markdown('<div class="kkg-tile">', unsafe_allow_html=True)
                preview = _fixed_preview(t.path, target_w=320, target_h=230)
                st.image(preview, width=320)
                st.markdown(f"<div class='kkg-label'>{t.label}</div>", unsafe_allow_html=True)
                if st.button("Select", key=f"select_{t.key}", use_container_width=True):
                    st.session_state.selected_display_key = t.key
                st.markdown("</div>", unsafe_allow_html=True)

selected_key: Optional[str] = st.session_state.get("selected_display_key")

# ---------- PDQ FORM (catalog-driven) ----------
def render_pdq_form():
    catalog = load_catalog(CATALOG_PATH)

    st.divider()
    st.subheader("PDQ TRAY — Configuration")

    if "form" not in st.session_state:
        st.session_state.form = {}

    controls = catalog.get("controls", [])
    for ctrl in controls:
        cid = ctrl.get("id")
        ctype = ctrl.get("type")
        label = ctrl.get("label")
        key = f"pdq__{cid}"

        if cid == "product_touches":
            assembly_key = st.session_state.form.get("assembly")
            if assembly_key != "assembly-turnkey":
                st.session_state.form.pop("product_touches", None)
                continue

        if ctype == "single":
            opts = ctrl.get("options", [])
            labels = [o.get("label") for o in opts]
            keys = [o.get("key") for o in opts]

            default_idx = 0
            if cid in st.session_state.form and st.session_state.form[cid] in keys:
                default_idx = keys.index(st.session_state.form[cid])

            if len(labels) <= 3:
                choice = st.radio(label, labels, index=default_idx, key=key, horizontal=True)
            else:
                choice = st.selectbox(label, labels, index=default_idx, key=key)

            st.session_state.form[cid] = keys[labels.index(choice)]

        elif ctype == "number":
            min_v = ctrl.get("min", 0)
            saved = st.session_state.form.get(cid)

            if cid in ("quantity", "divider_count", "product_touches"):
                default = int(saved) if saved is not None else (max(1, min_v) if cid == "quantity" else int(min_v))
                val = st.number_input(label, min_value=int(min_v), step=1, value=int(default), key=key)
                st.session_state.form[cid] = int(val)

            elif cid == "unit_weight_value":
                default = float(saved) if saved is not None else 0.0
                val = st.number_input(label, min_value=0.0, step=0.01, value=float(default), format="%.2f", key=key)
                st.session_state.form[cid] = float(val)

            else:
                default = float(saved) if saved is not None else float(min_v)
                val = st.number_input(label, min_value=float(min_v), step=0.01, value=float(default), key=key)
                st.session_state.form[cid] = float(val)
        else:
            st.caption(f"Unsupported control type: {ctype} for `{cid}`")

    form = st.session_state.form
    rules = catalog.get("rules", {})

    resolved: List[Tuple[str, int]] = []

    fp_key = form.get("footprint")
    width_in, depth_in = _footprint_dims(catalog, fp_key) if fp_key else (None, None)

    if "resolve_footprint_base" in rules and fp_key:
        r = rules["resolve_footprint_base"]
        base_part = r.get("map", {}).get(fp_key)
        if base_part:
            resolved.append((base_part, 1))

    if "resolve_header" in rules:
        r = rules["resolve_header"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            if r.get("match_on_dim") == "width_in" and width_in is not None:
                part = r.get("map", {}).get(str(width_in), r.get("else"))
            else:
                part = r.get("else")
        else:
            part = r.get("else")
        if part:
            resolved.append((part, 1))

    if "resolve_dividers" in rules:
        r = rules["resolve_dividers"]
        qty_ctrl = r.get("quantity_control")
        dqty = int(form.get(qty_ctrl, 0) or 0)
        part = None
        if dqty > 0 and r.get("match_on_dim") == "depth_in" and depth_in is not None:
            part = r.get("map", {}).get(str(depth_in), r.get("else"))
        if part and dqty > 0:
            resolved.append((part, dqty))

    if "resolve_shipper" in rules:
        r = rules["resolve_shipper"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            part = r.get("map", {}).get(fp_key, r.get("else"))
            if part:
                resolved.append((part, 1))

    if "resolve_assembly_touches" in rules:
        r = rules["resolve_assembly_touches"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            tq_ctrl = r.get("quantity_control")
            tqty = int(form.get(tq_ctrl, 0) or 0)
            if tqty >= int(r.get("min_quantity", 1)):
                part = r.get("part")
                if part:
                    resolved.append((part, tqty))

    policy = catalog.get("policy", {})
    qty = int(form.get("quantity", 1) or 1)

    unit_factor = 1.0
    for band in policy.get("unit_tiers", []):
        min_q = int(band.get("min_qty", 0))
        max_q = band.get("max_qty")
        if max_q is None:
            if qty >= min_q:
                unit_factor = float(band.get("factor", 1.0))
        else:
            if policy.get("tier_boundary", "inclusive") == "inclusive":
                if qty >= min_q and qty <= int(max_q):
                    unit_factor = float(band.get("factor", 1.0))
            else:
                if qty >= min_q and qty < int(max_q):
                    unit_factor = float(band.get("factor", 1.0))

    unit_weight_unit = form.get("unit_weight_unit", "lb")
    unit_weight_val = float(form.get("unit_weight_value", 0) or 0)
    unit_lb = unit_weight_val / 16.0 if unit_weight_unit == "oz" else unit_weight_val
    total_lbs = unit_lb * qty

    weight_add = 0.0
    for bucket in policy.get("weight_tiers", []):
        min_l = float(bucket.get("min_lbs", 0))
        max_l = bucket.get("max_lbs")
        if max_l is None:
            if total_lbs >= min_l:
                weight_add = float(bucket.get("add", 0))
        else:
            if total_lbs >= min_l and total_lbs <= float(max_l):
                weight_add = float(bucket.get("add", 0))

    cx_key = form.get("complexity_level", "cx-low")
    complexity_add = float(policy.get("complexity_add", {}).get(cx_key, 0.0))
    base_markup = float(policy.get("base_markup", 0.35))
    markup_pct = base_markup + weight_add + complexity_add

    per_unit_parts_subtotal = 0.0
    for part_key, q in resolved:
        per_unit_parts_subtotal += _parts_value(catalog, part_key) * q

    per_unit_after_tier = per_unit_parts_subtotal * unit_factor
    program_base = per_unit_after_tier * qty
    final_total = program_base * (1.0 + markup_pct)

    left, right = st.columns([0.58, 0.42], gap="large")

    with left:
        st.markdown("#### Resolved parts (per unit)")
        if not resolved:
            st.caption("Nothing resolved yet (all base values are 0).")
        else:
            rows = []
            for part_key, q in resolved:
                unit_val = _parts_value(catalog, part_key)
                line = unit_val * q
                label = catalog.get("parts", {}).get(part_key, {}).get("label", part_key)
                rows.append({"Part": label, "Qty": q, "Unit $": f"{unit_val:,.2f}", "Line $": f"{line:,.2f}"})
            df = pd.DataFrame(rows, columns=["Part", "Qty", "Unit $", "Line $"])
            st.table(df)

        st.markdown("#### Unit tier match")
        st.write(f"Quantity **{qty}** → factor **{unit_factor:.3f}**")

        st.markdown("#### Weight & Markup")
        weight_str = _round_display_weight(total_lbs, policy)
        st.write(
            f"Total weight: **{weight_str} lb**  "
            f"<span class='pill'>unit={unit_weight_val:g} {unit_weight_unit}</span>"
            f"<span class='pill'>qty={qty}</span>",
            unsafe_allow_html=True,
        )
        st.write(
            f"Markup breakdown: Base **{base_markup*100:.0f}%** + Weight **{weight_add*100:.0f}%** + Complexity **{complexity_add*100:.0f}%** "
            f"= **{markup_pct*100:.0f}%**"
        )

    with right:
        st.markdown("#### Totals")
        st.write(f"Per-unit parts subtotal: **${per_unit_parts_subtotal:,.2f}**")
        st.write(f"Per-unit after tier: **${per_unit_after_tier:,.2f}**")
        st.write(f"Program base (pre-markup): **${program_base:,.2f}**")
        st.write(f"Final (post-markup): **${final_total:,.2f}**")

    st.markdown("<div class='muted'>All values are placeholders until prices are updated in the catalog.</div>", unsafe_allow_html=True)

# ---------- Router ----------
if selected_key and selected_key.startswith("pdq/"):
    render_pdq_form()
elif selected_key:
    st.divider()
    st.subheader("Configuration")
    st.caption("Fields for this display type will be added soon.")
else:
    st.caption("Select a display above to configure its details.")

st.divider()
st.page_link("Home.py", label="Back to Home", icon="🏠")
