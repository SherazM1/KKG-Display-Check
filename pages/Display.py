from __future__ import annotations

import html
import os
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from app import catalog as cat
from app import gallery
from app import pricing

# ---------- Page setup ----------
st.set_page_config(page_title="Display · KKG", layout="wide")

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
      .kkg-tile { border:1px solid #e5e7eb; border-radius:12px; padding:10px; }
      .kkg-label { text-align:center; font-weight:800; font-size:16px; color:#111827; margin:10px 0 8px; letter-spacing:0.4px; }
      .muted { color:#6b7280; }
      .pill { display:inline-block; padding:2px 8px; border:1px solid #e5e7eb; border-radius:999px; font-size:12px; margin-left:6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

ASSETS_ROOT = "assets/references"
CATALOG_PATH_PDQ = "data/catalog/pdq.json"

# Category rows we want right now
ROW_ORDER = ["pdq", "sidekick"]
ROW_TITLES = {"pdq": "PDQs", "sidekick": "Sidekicks"}

# Labels you want (keep “PDQ TRAY” style)
LABEL_OVERRIDES = {
    "digital_pdq_tray": "PDQ TRAY",
    "pdq-tray-standard": "PDQ TRAY",
    "dump_bin": "DUMP BIN",
}

# ---------- Weight/Complexity grid ----------
def render_wc_grid(
    *,
    key: str = "wc_idx",
    size_px: int = 360,
    default_rc: Tuple[int, int] = (2, 0),
    gap: str = "xxsmall",
) -> Tuple[int, int]:
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


# ---------- Header ----------
st.markdown("## Select the type of display")

# ---------- Rows: PDQs then Sidekicks ----------
for cat_name in ROW_ORDER:
    st.markdown(f"### {ROW_TITLES.get(cat_name, cat_name.title())}")

    tiles = gallery.scan_category_pngs(ASSETS_ROOT, cat_name, label_overrides=LABEL_OVERRIDES)

    if not tiles:
        st.caption(f"No images found in `{ASSETS_ROOT}/{cat_name}`.")
        continue

    # You said 4 each, so we render 4 columns (and it still works if fewer)
    cols = st.columns(4, gap="large")
    for i, t in enumerate(tiles[:4]):
        with cols[i]:
            gallery.render_tile(t, preview_w=640, preview_h=460)

# Selection key (one at a time)
selected_key: Optional[str] = st.session_state.get("selected_display_key")

# ---------- PDQ CONFIG ----------
def render_pdq_form() -> None:
    catalog = cat.load_catalog(CATALOG_PATH_PDQ)
    policy = catalog.get("policy", {}) or {}

    st.divider()
    st.subheader("PDQ TRAY — Configuration")

    if "form" not in st.session_state:
        st.session_state.form = {}
    form: Dict = st.session_state.form

    # Render catalog-driven controls (except we currently hide weight/unit/complexity controls if they exist in JSON)
    for ctrl in catalog.get("controls", []) or []:
        cid = ctrl.get("id")
        ctype = ctrl.get("type")
        label = ctrl.get("label")
        widget_key = f"pdq__{cid}"

        # Keep this: product touches only if turnkey
        if cid == "product_touches":
            if form.get("assembly") != "assembly-turnkey":
                form.pop("product_touches", None)
                continue

        # If your pdq.json still contains these but you are using the 3×3 grid UI,
        # you can skip them here (we keep the grid below).
        if cid in ("unit_weight_unit", "unit_weight_value", "complexity_level"):
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

    # Weight/Complexity selection grid (3×3)
    st.markdown("#### Select Weight and Complexity Level")
    selected_rc = render_wc_grid(key="wc_idx", size_px=360, default_rc=(2, 0))

    # Resolve parts per unit
    fp_key = form.get("footprint")
    width_in, depth_in = cat.footprint_dims(catalog, fp_key) if fp_key else (None, None)

    resolved = pricing.resolve_parts_per_unit(catalog, form, footprint_dims=(width_in, depth_in))

    # Pricing math
    qty = int(form.get("quantity", 1) or 1)
    uf = pricing.unit_factor(policy, qty)

    per_unit_parts_subtotal = sum(pricing.parts_value(catalog, part_key) * q for part_key, q in resolved)
    per_unit_after_tier = per_unit_parts_subtotal * uf
    program_base = per_unit_after_tier * qty

    try:
        markup_pct = pricing.matrix_markup_pct(policy, selected_rc)
    except Exception as e:
        st.error(str(e))
        st.stop()

    final_total = program_base * (1.0 + markup_pct)
    final_per_unit = final_total / max(qty, 1)

    # Simple range preview (your current behavior)
    min_total = program_base * 1.25
    max_total = program_base * 1.45

    labels = [
        ["Heavy", "Moderate/Heavy", "Complex/Heavy"],
        ["Medium", "Moderate/Medium", "Complex/Medium"],
        ["Light", "Moderate", "Complex"],
    ]
    sel_r, sel_c = selected_rc
    selected_label = labels[int(sel_r)][int(sel_c)]

    st.markdown("### Totals")
    st.markdown(
        f"""
        <div style="display:grid; gap:10px; max-width:720px;">
          <div><b>Selected tier:</b> {html.escape(str(selected_label))}</div>
          <div><b>Per-unit price:</b> ${final_per_unit:,.2f}</div>
          <div><b>Program total:</b> ${final_total:,.2f}</div>
          <div><b>Program total range:</b> ${min_total:,.2f} - ${max_total:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Optional: resolved parts table (debug-friendly)
    st.markdown("#### Resolved parts (per unit)")
    if resolved:
        rows = []
        for part_key, q in resolved:
            unit_val = pricing.parts_value(catalog, part_key)
            line = unit_val * q
            label = catalog.get("parts", {}).get(part_key, {}).get("label", part_key)
            rows.append({"Part": label, "Qty": q, "Unit $": f"{unit_val:,.2f}", "Line $": f"{line:,.2f}"})
        st.table(pd.DataFrame(rows, columns=["Part", "Qty", "Unit $", "Line $"]))
    else:
        st.caption("Nothing resolved yet (all base values may still be 0).")

    st.markdown("<div class='muted'>All values are placeholders until prices are updated in the catalog.</div>", unsafe_allow_html=True)


# ---------- Router ----------
if selected_key and selected_key.startswith("pdq/"):
    render_pdq_form()
elif selected_key and selected_key.startswith("sidekick/"):
    st.divider()
    st.subheader("SIDEKICK — Configuration")
    st.caption("Sidekick configuration coming next (we’ll wire this to data/catalog/sidekick.json).")
elif selected_key:
    st.divider()
    st.subheader("Configuration")
    st.caption("Fields for this display type will be added soon.")
else:
    st.caption("Select a display above to configure its details.")

st.divider()
st.page_link("Home.py", label="Back to Home", icon="🏠")
