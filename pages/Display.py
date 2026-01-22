# pages/Display.py
# Catalog-driven PDQ UI + rule resolution + preview
# Markup is driven strictly by policy.matrix_markups[row][col] from the 3x3 selection.

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import html
import streamlit.components.v1 as components
from urllib.parse import urlencode
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

# ---------- Page setup ----------
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    textwrap.dedent(
        """
        <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
          html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
          .kkg-tile { border:1px solid #e5e7eb; border-radius:12px; padding:12px; background:#ffffff; }
          .kkg-label { text-align:center; font-weight:700; font-size:16px; color:#3b3f46; margin:10px 0 10px; letter-spacing:0.5px; }
          .muted { color:#6b7280; }
          .kkg-total-line { display:flex; justify-content:space-between; align-items:baseline; gap:12px; margin:6px 0; }
          .kkg-total-key { font-weight:600; color:#374151; font-size:34px; }
          .kkg-total-val { font-weight:600; color:#111827; font-size:34px; }
          .kkg-total-amount { font-weight:700; font-size:34px; letter-spacing:0.3px; color:#111827; }
          .kkg-total-range { font-size:34px; color:#374151; }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

CATALOG_PATH = "data/catalog/pdq.json"
ASSETS_ROOT = "assets/references"

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


def _unit_factor(policy: Dict, qty: int) -> float:
    unit_factor = 1.0
    for band in policy.get("unit_tiers", []) or []:
        min_q = int(band.get("min_qty", 0) or 0)
        max_q = band.get("max_qty")
        factor = float(band.get("factor", 1.0) or 1.0)

        if max_q is None:
            if qty >= min_q:
                unit_factor = factor
            continue

        max_q_i = int(max_q)
        inclusive = (policy.get("tier_boundary", "inclusive") == "inclusive")
        if inclusive and (qty >= min_q and qty <= max_q_i):
            unit_factor = factor
        if not inclusive and (qty >= min_q and qty < max_q_i):
            unit_factor = factor

    return float(unit_factor)


def _matrix_markup_pct(policy: Dict, rc: Tuple[int, int]) -> float:
    """
    Reads markup strictly from policy.matrix_markups[r][c].
    Expects decimals (0.35 == 35%).
    Hard-fails if missing/invalid so you don't silently apply wrong totals.
    """
    grid = policy.get("matrix_markups")
    if not (isinstance(grid, list) and len(grid) == 3 and all(isinstance(r, list) and len(r) == 3 for r in grid)):
        st.error("Missing/invalid `policy.matrix_markups` in pdq.json (expected 3x3 list of decimals).")
        st.stop()

    r, c = rc
    try:
        val = float(grid[r][c])
    except Exception:
        st.error("Invalid value in `policy.matrix_markups` (must be numeric decimals like 0.35).")
        st.stop()

    if val < 0:
        st.error("Invalid markup in `policy.matrix_markups` (negative).")
        st.stop()

    return val


def _resolve_parts_per_unit(catalog: Dict, form: Dict) -> List[Tuple[str, int]]:
    rules = catalog.get("rules", {}) or {}
    resolved: List[Tuple[str, int]] = []

    fp_key = form.get("footprint")
    width_in, depth_in = _footprint_dims(catalog, fp_key) if fp_key else (None, None)

    if fp_key and "resolve_footprint_base" in rules:
        r = rules["resolve_footprint_base"]
        base_part = (r.get("map", {}) or {}).get(fp_key)
        if base_part:
            resolved.append((base_part, 1))

    if "resolve_header" in rules:
        r = rules["resolve_header"]
        part = r.get("else")
        if form.get(r.get("when_control")) == r.get("when_value"):
            if r.get("match_on_dim") == "width_in" and width_in is not None:
                part = (r.get("map", {}) or {}).get(str(width_in), r.get("else"))
        if part:
            resolved.append((part, 1))

    if "resolve_dividers" in rules:
        r = rules["resolve_dividers"]
        qty_ctrl = r.get("quantity_control")
        dqty = int(form.get(qty_ctrl, 0) or 0)
        if dqty > 0 and r.get("match_on_dim") == "depth_in" and depth_in is not None:
            part = (r.get("map", {}) or {}).get(str(depth_in), r.get("else"))
            if part:
                resolved.append((part, dqty))

    if "resolve_shipper" in rules:
        r = rules["resolve_shipper"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
            if part:
                resolved.append((part, 1))

    if "resolve_assembly_touches" in rules:
        r = rules["resolve_assembly_touches"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            tq_ctrl = r.get("quantity_control")
            tqty = int(form.get(tq_ctrl, 0) or 0)
            if tqty >= int(r.get("min_quantity", 1) or 1):
                part = r.get("part")
                if part:
                    resolved.append((part, tqty))

    return resolved


def render_wc_grid(
    *,
    key: str = "wc_idx",
    size_px: int = 300,
    default_rc: Tuple[int, int] = (2, 0),  # bottom-left
    gap: str = "xxsmall",
) -> Tuple[int, int]:
    """
    3×3 tile grid (pure Streamlit, reliable buttons) with fixed labels in exact positions.
    No internal scroll: tiles auto-size (no fixed height).

    Labels (top->bottom, left->right):
      Heavy | Moderate/Heavy | Complex/Heavy
      Medium | Moderate/Medium | Complex/Medium
      Light | Moderate | Complex
    """
    labels = [
        ["Heavy", "Moderate/Heavy", "Complex/Heavy"],
        ["Medium", "Moderate/Medium", "Complex/Medium"],
        ["Light", "Moderate", "Complex"],
    ]

    cell_px = int(min(140, max(96, size_px // 3)))

    default_idx = int(default_rc[0] * 3 + default_rc[1])
    selected_idx = int(st.session_state.get(key, default_idx))
    selected_idx = min(8, max(0, selected_idx))
    st.session_state[key] = selected_idx

    st.markdown(
        f"""
        <style>
          div[data-testid="column"] {{
            min-width: {cell_px}px !important;
          }}

          div[data-testid="stVerticalBlockBorderWrapper"] {{
            max-width: {cell_px}px;
            min-height: {cell_px}px;
            padding: 8px 10px !important;
            margin: 0 auto;
          }}

          div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stButton"] {{
            display: flex;
            justify-content: center;
          }}

          div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stButton"] button {{
            padding: 0.12rem 0.5rem !important;
            font-weight: 700 !important;
            font-size: 12px !important;
            border-radius: 10px !important;
          }}

          .wc-cell-label {{
            font-weight: 800;
            font-size: 18px;
            line-height: 1.15;
            text-align: center;
            color: #111827;
            user-select: none;
            margin: 2px 0 8px 0;
            white-space: normal;
            overflow-wrap: anywhere;
          }}

          .wc-ind {{
            height: 5px;
            width: 100%;
            border-radius: 999px;
            margin: 2px 0 8px 0;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    for r in range(3):
        cols = st.columns(3, gap=gap)
        for c in range(3):
            idx = r * 3 + c
            is_selected = idx == selected_idx

            with cols[c]:
                tile = st.container(border=True)
                with tile:
                    st.markdown(
                        f"<div class='wc-ind' style='background:{'#111827' if is_selected else '#e5e7eb'};'></div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"<div class='wc-cell-label'>{labels[r][c]}</div>", unsafe_allow_html=True)

                    btn_text = "Selected" if is_selected else "Select"
                    if st.button(btn_text, key=f"{key}__{idx}", use_container_width=False):
                        st.session_state[key] = idx
                        st.rerun()

    rr, cc = divmod(int(st.session_state[key]), 3)
    return int(rr), int(cc)


def wc_idx_to_rc(idx: int) -> Tuple[int, int]:
    """Helper for readability elsewhere."""
    idx = min(8, max(0, int(idx)))
    return divmod(idx, 3)


def matrix_markup_pct(policy: Dict, rc: Tuple[int, int]) -> float:
    """policy['matrix_markups'] must be a 3×3 list of decimals (e.g. 0.35)."""
    grid = policy["matrix_markups"]
    r, c = rc
    return float(grid[r][c])


# ---------- UI tile helpers ----------
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


def _chunk(lst: List[OptionTile], n: int) -> List[List[OptionTile]]:
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def _fixed_preview(path: str, target_w: int = 320, target_h: int = 230) -> Image.Image:
    img = Image.open(path).convert("RGBA")
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
    for row in _chunk(tiles, 2):
        cols = st.columns(len(row), gap="large")
        for c, t in zip(cols, row):
            with c:
                st.markdown('<div class="kkg-tile">', unsafe_allow_html=True)
                st.image(_fixed_preview(t.path, target_w=320, target_h=230), width=320)
                st.markdown(f"<div class='kkg-label'>{t.label}</div>", unsafe_allow_html=True)
                if st.button("Select", key=f"select_{t.key}", use_container_width=True):
                    st.session_state.selected_display_key = t.key
                st.markdown("</div>", unsafe_allow_html=True)

selected_key: Optional[str] = st.session_state.get("selected_display_key")


# ---------- PDQ FORM (catalog-driven) ----------
def render_pdq_form() -> None:
    catalog = load_catalog(CATALOG_PATH)
    policy = catalog.get("policy", {}) or {}

    st.divider()
    st.subheader("PDQ TRAY — Configuration")

    if "form" not in st.session_state:
        st.session_state.form = {}
    form = st.session_state.form

    for ctrl in catalog.get("controls", []) or []:
        cid = ctrl.get("id")
        ctype = ctrl.get("type")
        label = ctrl.get("label")
        widget_key = f"pdq__{cid}"

        # Controls removed from the current UI (kept in catalog for now)
        if cid in ("unit_weight_unit", "unit_weight_value", "complexity_level"):
            continue

        if cid == "product_touches":
            if form.get("assembly") != "assembly-turnkey":
                form.pop("product_touches", None)
                continue

        if ctype == "single":
            opts = ctrl.get("options", []) or []
            labels = [o.get("label") for o in opts]
            keys = [o.get("key") for o in opts]

            default_idx = 0
            if cid in form and form[cid] in keys:
                default_idx = keys.index(form[cid])

            if len(labels) <= 3:
                choice = st.radio(label, labels, index=default_idx, key=widget_key, horizontal=True)
            else:
                choice = st.selectbox(label, labels, index=default_idx, key=widget_key)

            form[cid] = keys[labels.index(choice)]
            continue

        if ctype == "number":
            min_v = ctrl.get("min", 0)
            saved = form.get(cid)

            if cid in ("quantity", "divider_count", "product_touches"):
                default = int(saved) if saved is not None else (max(1, int(min_v)) if cid == "quantity" else int(min_v))
                val = st.number_input(label, min_value=int(min_v), step=1, value=int(default), key=widget_key)
                form[cid] = int(val)
            else:
                default = float(saved) if saved is not None else float(min_v)
                val = st.number_input(label, min_value=float(min_v), step=0.01, value=float(default), key=widget_key)
                form[cid] = float(val)
            continue

        st.caption(f"Unsupported control type: {ctype} for `{cid}`")

    st.markdown("#### Select Weight and Complexity Level")
    selected_rc = render_wc_grid(key="wc_idx", size_px=360, default_rc=(2, 0))

    resolved = _resolve_parts_per_unit(catalog, form)

    qty = int(form.get("quantity", 1) or 1)
    unit_factor = _unit_factor(policy, qty)

    per_unit_parts_subtotal = sum(_parts_value(catalog, part_key) * q for part_key, q in resolved)
    per_unit_after_tier = per_unit_parts_subtotal * unit_factor
    program_base = per_unit_after_tier * qty

    markup_pct = _matrix_markup_pct(policy, selected_rc)
    final_total = program_base * (1.0 + markup_pct)

    final_per_unit = final_total / max(qty, 1)

    min_total = program_base * 1.25
    max_total = program_base * 1.45

    labels = [
        ["Heavy", "Moderate/Heavy", "Complex/Heavy"],
        ["Medium", "Moderate/Medium", "Complex/Medium"],
        ["Light", "Moderate", "Complex"],
    ]
    sel_r, sel_c = selected_rc
    selected_label = labels[int(sel_r)][int(sel_c)]

    left, right = st.columns([0.58, 0.42], gap="large")

    with left:
        st.markdown("### Totals")
        st.markdown(
        f"<div class='kkg-total-line'>"
        f"<span class='kkg-total-key' style='font-size:26px;'>Selected tier</span>"
        f"<span class='kkg-total-val' style='font-size:26px;'>{selected_label}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='kkg-total-line'>"
        f"<span class='kkg-total-key' style='font-size:26px;'>Per-unit price</span>"
        f"<span class='kkg-total-val' style='font-size:26px;'>${final_per_unit:,.2f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='kkg-total-line'>"
        f"<span class='kkg-total-key' style='font-size:26px;'>Program total</span>"
        f"<span class='kkg-total-amount' style='font-size:26px;'>${final_total:,.2f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='kkg-total-line'>"
        f"<span class='kkg-total-key' style='font-size:26px;'>Program total range</span>"
        f"<span class='kkg-total-range' style='font-size:26px;'>${min_total:,.2f} - ${max_total:,.2f}</span>"
        f"</div>",
        f"<span class='kkg-total-key' style='font-size:26px;'>Program total</span>"
        f"<span class='kkg-total-amount' style='font-size:26px;'>${final_total:,.2f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='kkg-total-line'>"
        f"<span class='kkg-total-key' style='font-size:26px;'>Program total range</span>"
        f"<span class='kkg-total-range' style='font-size:26px;'>${min_total:,.2f} - ${max_total:,.2f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    with right:
        st.empty()


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
