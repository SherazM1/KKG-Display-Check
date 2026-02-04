from __future__ import annotations

import html
from typing import Dict, Optional, Tuple

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
      .pill { display:inline-block; padding:2px 8px; border:1px solid #e5e7eb; border-radius:999px; font-size:12px; margin:6px 0 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

ASSETS_ROOT = "assets/references"
CATALOG_PATH_PDQ = "data/catalog/pdq.json"

ROW_ORDER = ["pdq", "sidekick"]
ROW_TITLES = {"pdq": "PDQs", "sidekick": "Sidekicks"}

LABEL_OVERRIDES = {
    # --- PDQs (order doesn't matter; mapping by filename stem) ---
    "clipped_pdq_tray": "Clipped PDQ Tray",
    "digital_pdq_tray": "Angled PDQ Tray",
    "square_pdq_tray": "Square PDQ Tray",
    "standardclub_pdq_tray": "Standard PDQ Tray",

    # --- Sidekicks ---
    "sidekickpeg24": "Sidekick - Pegged 24",
    "sidekickpeg48": "Sidekick - Pegged 48",
    "sidekickshelves24": "Sidekick - Shelves 24",
    "sidekickshelves48": "Sidekick - Shelves 48",
}


# ---------- Weight/Complexity grid ----------
def render_wc_grid(
    *,
    key: str = "wc_idx",
    size_px: int = 360,
    default_rc: Tuple[int, int] = (2, 0),
    gap: str = "xxsmall",
) -> Tuple[int, int]:
    """
    3x3 selection grid with axis labels:
      - Left (vertical): Weight
      - Bottom (horizontal): Complexity
    Returns (row, col) selected.
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
          .wc-axis-left {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: #111827;
            transform: rotate(-90deg);
            white-space: nowrap;
            user-select: none;
          }}
          .wc-axis-bottom {{
            text-align: center;
            font-weight: 800;
            margin-top: 10px;
            color: #111827;
            user-select: none;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    outer = st.columns([0.06, 0.94], gap="small")

    with outer[0]:
        st.markdown("<div class='wc-axis-left'>Weight</div>", unsafe_allow_html=True)

    with outer[1]:
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

        st.markdown("<div class='wc-axis-bottom'>Complexity</div>", unsafe_allow_html=True)

    rr, cc = divmod(int(st.session_state[key]), 3)
    return int(rr), int(cc)



def _is_required_answered(ctrl: Dict, form: Dict, *, prefix: str) -> bool:
    """
    Strict gating rules:
      - single: must NOT be '__unset__'
      - number: must be >= min AND user must have interacted (touched), even if value is 0
    """
    cid = ctrl.get("id")
    if not cid:
        return True

    if not bool(ctrl.get("required", False)):
        return True

    ctype = ctrl.get("type")

    if ctype == "single":
        val = form.get(cid)
        return val not in (None, "", "__unset__")

    if ctype == "number":
        touched_key = f"{prefix}__{cid}__touched"
        if not bool(st.session_state.get(touched_key, False)):
            return False

        try:
            v = float(form.get(cid))
        except Exception:
            return False

        min_v = float(ctrl.get("min", 0) or 0)
        return v >= min_v

    return True

def _control_visible_for_form(ctrl_id: str, form: Dict) -> bool:
    if ctrl_id == "product_touches":
        return form.get("assembly") == "assembly-turnkey"
    return True


def _render_catalog_controls(
    *,
    catalog: Dict,
    form: Dict,
    prefix: str,
    fixed_footprint: Optional[str] = None,
) -> bool:
    """
    Renders controls with strict step-gating (required chain).
    Returns True iff all required controls (that are visible in the current form state) are answered.

    Strict behavior:
      - required single controls start at '__unset__' via a '— Select —' option
      - required number controls are not "answered" until touched, even if 0
    """
    required_chain_ok = True

    if fixed_footprint:
        form["footprint"] = fixed_footprint

    for ctrl in catalog.get("controls", []) or []:
        cid = ctrl.get("id")
        ctype = ctrl.get("type")
        label = ctrl.get("label")
        widget_key = f"{prefix}__{cid}"

        if not cid:
            continue

        if cid == "footprint" and fixed_footprint:
            continue

        if cid in ("unit_weight_unit", "unit_weight_value", "complexity_level"):
            continue

        if not _control_visible_for_form(cid, form):
            form.pop(cid, None)
            st.session_state.pop(f"{prefix}__{cid}__touched", None)
            continue

        enabled = required_chain_ok

        if ctype == "single":
            opts = ctrl.get("options", []) or []
            opt_labels = [o.get("label") for o in opts]
            opt_keys = [o.get("key") for o in opts]

            # Strict: required singles start as unset
            if bool(ctrl.get("required", False)):
                opt_labels = ["— Select —"] + opt_labels
                opt_keys = ["__unset__"] + opt_keys
                form.setdefault(cid, "__unset__")

            default_idx = 0
            if cid in form and form[cid] in opt_keys:
                default_idx = opt_keys.index(form[cid])

            if len(opt_labels) <= 3:
                choice = st.radio(
                    label,
                    opt_labels,
                    index=default_idx,
                    key=widget_key,
                    horizontal=True,
                    disabled=not enabled,
                )
            else:
                choice = st.selectbox(label, opt_labels, index=default_idx, key=widget_key, disabled=not enabled)

            if enabled:
                form[cid] = opt_keys[opt_labels.index(choice)]

        elif ctype == "number":
            min_v = ctrl.get("min", 0)
            saved = form.get(cid)

            touched_key = f"{prefix}__{cid}__touched"
            prev_val = st.session_state.get(f"{prefix}__{cid}__prev")

            is_int = cid in ("quantity", "divider_count", "product_touches", "pegs_count")
            if is_int:
                default = int(saved) if saved is not None else (max(1, int(min_v)) if cid == "quantity" else int(min_v))
                val = st.number_input(
                    label,
                    min_value=int(min_v),
                    step=1,
                    value=int(default),
                    key=widget_key,
                    disabled=not enabled,
                )
                if enabled:
                    form[cid] = int(val)
            else:
                default = float(saved) if saved is not None else float(min_v)
                val = st.number_input(
                    label,
                    min_value=float(min_v),
                    step=0.01,
                    value=float(default),
                    key=widget_key,
                    disabled=not enabled,
                )
                if enabled:
                    form[cid] = float(val)

            # Strict: mark touched only after user interaction changes the value
            if enabled:
                current = form.get(cid)
                if prev_val is None:
                    st.session_state[f"{prefix}__{cid}__prev"] = current
                else:
                    if current != prev_val:
                        st.session_state[touched_key] = True
                        st.session_state[f"{prefix}__{cid}__prev"] = current

        else:
            st.caption(f"Unsupported control type: {ctype} for `{cid}`")

        if required_chain_ok:
            required_chain_ok = _is_required_answered(ctrl, form, prefix=prefix)

        if not required_chain_ok:
            st.caption("Complete the current step to continue.")

    # Final completion check (only visible required fields are evaluated in-loop)
    return bool(required_chain_ok)


def _compute_and_render_totals(
    *,
    catalog: Dict,
    form: Dict,
    wc_key: str,
    wc_default: Tuple[int, int],
    unlocked: bool,
) -> None:
    """
    If unlocked=False:
      - WC grid and totals are visually present but non-interactive (locked message)
      - no pricing math is run
    """
    if not unlocked:
        st.markdown("#### Select Weight and Complexity Level")
        st.caption("Complete the steps above to continue.")
        st.markdown(
            "<div class='muted'>Totals will appear once all required fields are selected.</div>",
            unsafe_allow_html=True,
        )
        return

    policy = catalog.get("policy", {}) or {}

    st.markdown("#### Select Weight and Complexity Level")
    selected_rc = render_wc_grid(key=wc_key, size_px=360, default_rc=wc_default)

    fp_key = form.get("footprint")
    width_in, depth_in = cat.footprint_dims(catalog, fp_key) if fp_key else (None, None)

    resolved = pricing.resolve_parts_per_unit(catalog, form, footprint_dims=(width_in, depth_in))

    qty = int(form.get("quantity", 1) or 1)
    uf = pricing.unit_factor(policy, qty)

    per_unit_parts_subtotal = sum(pricing.parts_value(catalog, part_key) * q for part_key, q in resolved)
    per_unit_after_tier = per_unit_parts_subtotal * uf
    program_base = per_unit_after_tier * qty

    markup_pct = pricing.matrix_markup_pct(policy, selected_rc)
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

    st.markdown(
        "<div class='muted'>All values are placeholders until prices are updated in the catalog.</div>",
        unsafe_allow_html=True,
    )


# ---------- Header ----------
st.markdown("## Select the type of display")

# ---------- Rows: PDQs then Sidekicks ----------
for cat_name in ROW_ORDER:
    st.markdown(f"### {ROW_TITLES.get(cat_name, cat_name.title())}")

    tiles = gallery.scan_category_pngs(ASSETS_ROOT, cat_name, label_overrides=LABEL_OVERRIDES)
    if not tiles:
        st.caption(f"No images found in `{ASSETS_ROOT}/{cat_name}`.")
        continue

    cols = st.columns(4, gap="large")
    for i, t in enumerate(tiles[:4]):
        with cols[i]:
            gallery.render_tile(t, preview_w=640, preview_h=460)

selected_key: Optional[str] = st.session_state.get("selected_display_key")


# ---------- PDQ CONFIG ----------
def render_pdq_form() -> None:
    catalog = cat.load_catalog(CATALOG_PATH_PDQ)

    st.divider()
    display_label = (catalog.get("meta", {}) or {}).get("display_label", "PDQ Tray")
    st.subheader(f"{display_label.upper()} — Configuration")


    if "form" not in st.session_state:
        st.session_state.form = {}
    form: Dict = st.session_state.form

    _render_catalog_controls(catalog=catalog, form=form, prefix="pdq")
    _compute_and_render_totals(catalog=catalog, form=form, wc_key="wc_idx", wc_default=(2, 0))


# ---------- SIDEKICK CONFIG ----------
def render_sidekick_form(selected_stem: str) -> None:
    catalog_path = f"data/catalog/{selected_stem}.json"
    catalog = cat.load_catalog(catalog_path)

    st.divider()
    display_label = (catalog.get("meta", {}) or {}).get("display_label", "Sidekick")
    st.subheader(f"{display_label.upper()} — Configuration")


    if "sidekick_form" not in st.session_state:
        st.session_state.sidekick_form = {}
    form: Dict = st.session_state.sidekick_form

    st.markdown("<div class='pill'>Footprint: 24</div>", unsafe_allow_html=True)

    _render_catalog_controls(catalog=catalog, form=form, prefix="sidekick", fixed_footprint="fp-24")
    _compute_and_render_totals(catalog=catalog, form=form, wc_key="sidekick_wc_idx", wc_default=(2, 0))


# ---------- Router ----------
if selected_key and selected_key.startswith("pdq/"):
    render_pdq_form()
elif selected_key and selected_key.startswith("sidekick/"):
    stem = selected_key.split("/", 1)[1]
    render_sidekick_form(stem)
elif selected_key:
    st.divider()
    st.subheader("Configuration")
    st.caption("Fields for this display type will be added soon.")
else:
    st.caption("Select a display above to configure its details.")

st.divider()
st.page_link("Home.py", label="Back to Home", icon="🏠")
