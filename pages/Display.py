# pages/Display.py
# Catalog-driven PDQ UI + rule resolution + preview (includes footprint base)
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import streamlit as st
from PIL import Image

# ---------- Page setup ----------
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
      .kkg-tile { border:1px solid #e5e7eb; border-radius:12px; padding:10px; }
      .kkg-label { text-align:center; font-weight:700; font-size:16px; color:#3b3f46; margin:6px 0 8px; }
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
ALLOWED_DIRS = {"pdq", "pallet", "sidekick", "endcap", "display", "header"}
LABEL_OVERRIDES = {"digital_pdq_tray": "PDQ TRAY", "pdq-tray-standard": "PDQ TRAY"}

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
    # Why: safe if keys are missing or zero during placeholder phase
    try:
        return float(catalog.get("parts", {}).get(part_key, {}).get("base_value", 0) or 0)
    except Exception:
        return 0.0

# ---------- Page header ----------
st.markdown("## Select the type of display")

# ---------- Gallery ----------
tiles = scan_pngs()
if not tiles:
    st.info(f"No PNGs found. Add images under `{ASSETS_ROOT}/<category>/...` "
            "(e.g., `assets/references/pdq/digital_pdq_tray.png`).")
else:
    cols = st.columns(3, gap="large")
    for i, t in enumerate(tiles):
        with cols[i % 3]:
            st.markdown('<div class="kkg-tile">', unsafe_allow_html=True)
            st.image(Image.open(t.path), use_column_width=False, width=320)
            st.markdown(f"<div class='kkg-label'>{t.label}</div>", unsafe_allow_html=True)
            if st.button("Select", key=f"select_{t.key}", use_container_width=True):
                st.session_state.selected_display_key = t.key
            st.markdown('</div>', unsafe_allow_html=True)

selected_key: Optional[str] = st.session_state.get("selected_display_key")

# ---------- PDQ FORM (catalog-driven) ----------
def render_pdq_form():
    catalog = load_catalog(CATALOG_PATH)

    st.divider()
    st.subheader("PDQ TRAY — Configuration")

    # Minimal state bag
    if "form" not in st.session_state:
        st.session_state.form = {}

    # Render controls by catalog order
    controls = catalog.get("controls", [])
    for ctrl in controls:
        cid = ctrl.get("id")
        ctype = ctrl.get("type")
        label = ctrl.get("label")
        key = f"pdq__{cid}"

        # Conditional visibility: product_touches only if assembly-turnkey
        if cid == "product_touches":
            assembly_key = st.session_state.form.get("assembly")
            if assembly_key != "assembly-turnkey":
                st.session_state.form.pop("product_touches", None)
                continue

        if ctype == "single":
            opts = ctrl.get("options", [])
            labels = [o.get("label") for o in opts]
            keys = [o.get("key") for o in opts]
            widget = st.radio if len(labels) <= 3 else st.selectbox
            default_idx = 0
            if cid in st.session_state.form and st.session_state.form[cid] in keys:
                default_idx = keys.index(st.session_state.form[cid])
            choice = widget(label, labels, index=default_idx, key=key, horizontal=True if widget==st.radio else False)
            st.session_state.form[cid] = keys[labels.index(choice)]
        elif ctype == "number":
            min_v = ctrl.get("min", 0)
            default = st.session_state.form.get(cid, min_v if cid != "quantity" else max(1, min_v))
            val = st.number_input(label, min_value=min_v, step=1, value=int(default), key=key)
            st.session_state.form[cid] = int(val)
        else:
            st.caption(f"Unsupported control type: {ctype} for `{cid}`")

    # ---------- Resolution (rules) ----------
    form = st.session_state.form
    rules = catalog.get("rules", {})
    parts = catalog.get("parts", {})

    resolved: List[Tuple[str, int]] = []  # (part_key, qty)

    # Helper: footprint dims
    fp_key = form.get("footprint")
    width_in, depth_in = _footprint_dims(catalog, fp_key) if fp_key else (None, None)

    # resolve_footprint_base (always map to one base per unit)
    if "resolve_footprint_base" in rules and fp_key:
        r = rules["resolve_footprint_base"]
        base_part = r.get("map", {}).get(fp_key)
        if base_part:
            resolved.append((base_part, 1))

    # resolve_header
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

    # resolve_dividers
    if "resolve_dividers" in rules:
        r = rules["resolve_dividers"]
        qty_ctrl = r.get("quantity_control")
        qty = int(form.get(qty_ctrl, 0) or 0)
        part = None
        if qty > 0 and r.get("match_on_dim") == "depth_in" and depth_in is not None:
            part = r.get("map", {}).get(str(depth_in), r.get("else"))
        if part and qty > 0:
            resolved.append((part, qty))

    # resolve_shipper
    if "resolve_shipper" in rules:
        r = rules["resolve_shipper"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            part = r.get("map", {}).get(fp_key, r.get("else"))
            if part:
                resolved.append((part, 1))

    # resolve_assembly_touches
    if "resolve_assembly_touches" in rules:
        r = rules["resolve_assembly_touches"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            qty_ctrl = r.get("quantity_control")
            qty = int(form.get(qty_ctrl, 0) or 0)
            if qty >= int(r.get("min_quantity", 1)):
                part = r.get("part")
                if part:
                    resolved.append((part, qty))

    # ---------- Policy: tiers/weight/complexity ----------
    policy = catalog.get("policy", {})
    qty = int(form.get("quantity", 1) or 1)

    # Unit tiers (per-unit)
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

    # Weight (total lbs)
    unit_weight_unit = form.get("unit_weight_unit", "lb")
    unit_weight_val = float(form.get("unit_weight_value", 0) or 0)
    unit_lb = unit_weight_val / 16.0 if unit_weight_unit == "oz" else unit_weight_val
    total_lbs = unit_lb * qty

    # Weight add %
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

    # Complexity add %
    cx_key = form.get("complexity_level", "cx-low")
    complexity_add = float(policy.get("complexity_add", {}).get(cx_key, 0.0))
    base_markup = float(policy.get("base_markup", 0.35))
    markup_pct = base_markup + weight_add + complexity_add

    # ---------- Totals ----------
    per_unit_parts_subtotal = 0.0
    for part_key, q in resolved:
        per_unit_parts_subtotal += _parts_value(catalog, part_key) * q

    per_unit_after_tier = per_unit_parts_subtotal * unit_factor
    program_base = per_unit_after_tier * qty
    final_total = program_base * (1.0 + markup_pct)

    # ---------- UI: Derived Preview ----------
    left, right = st.columns([0.58, 0.42], gap="large")

    with left:
        st.markdown("#### Resolved parts (per unit)")
        if not resolved:
            st.caption("Nothing resolved yet (all base values are 0).")
        else:
            st.markdown("<table class='kkg-table' width='100%'><tr><th>Part</th><th class='mono'>Qty</th><th class='mono'>Unit $</th><th class='mono'>Line $</th></tr>", unsafe_allow_html=True)
            for part_key, q in resolved:
                unit_val = _parts_value(catalog, part_key)
                line = unit_val * q
                label = catalog.get("parts", {}).get(part_key, {}).get("label", part_key)
                st.markdown(f"<tr><td>{label}</td><td class='mono'>{q}</td><td class='mono'>{unit_val:,.2f}</td><td class='mono'>{line:,.2f}</td></tr>", unsafe_allow_html=True)
            st.markdown("</table>", unsafe_allow_html=True)

        st.markdown("#### Unit tier match")
        st.write(f"Quantity **{qty}** → factor **{unit_factor:.3f}**")

        st.markdown("#### Weight & Markup")
        st.write(
            f"Total weight: **{total_lbs:.2f} lb**  "
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

    st.markdown("<div class='muted'>All values are placeholders until prices are populated.</div>", unsafe_allow_html=True)

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
