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

ROW_ORDER = ["pdq", "sidekick", "halfpallet", "dumpbin"]
ROW_TITLES = {"pdq": "PDQs", "sidekick": "Sidekicks", "halfpallet": "Half Pallets", "dumpbin": "Dump Bins"}

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


    # --- Half Pallets --- 
    "frontfaced_hp": "Front-Faced Half Pallet",
    "threesided_hp": "Three-Sided Half Pallet",

    # --- Dump Bins ---
    "dump_bin": "Half Pallet Dump Bin",
}

PDQ_CATALOG_BY_STEM = {
    "clipped_pdq_tray": "data/catalog/pdq.json",
    "digital_pdq_tray": "data/catalog/pdq.json",
    "square_pdq_tray": "data/catalog/pdq.json",
    "standardclub_pdq_tray": "data/catalog/pdq.json",
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
            font-weight: 900;
            font-size: 22px;         /* <-- bigger Weight */
            color: #111827;
            transform: rotate(-90deg);
            white-space: nowrap;
            user-select: none;
            margin-top: 180px;        /* <-- move Weight DOWN (adjust as needed) */
          }}
          .wc-axis-bottom {{
            text-align: center;
            font-weight: 900;
            font-size: 22px;         /* <-- bigger Complexity */
            margin-top: 14px;        /* keep spacing nice */
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
    qty = int(form.get("quantity") or 1)
    qty = max(qty, 1)


    def _parts_value_with_qty(part_key: str) -> float:
        """
        Backward-compatible call path:
        - Prefer break-aware pricing via `program_qty`.
        - Fallback for older pricing modules that don't accept this kwarg.
        """
        try:
            return float(pricing.parts_value(catalog, part_key, program_qty=qty))
        except TypeError as exc:
            msg = str(exc)
            if "program_qty" in msg and "unexpected keyword" in msg:
                return float(pricing.parts_value(catalog, part_key))
            raise

    per_unit_parts_subtotal = sum(
        _parts_value_with_qty(part_key) * q
        for part_key, q in resolved
    )
    program_base = per_unit_parts_subtotal * qty
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

def _generic_catalog_for_selected_tile(
    *,
    category: str,
    stem: str,
    label: str,
    hero_image: str,
) -> Dict:
    """
    Minimal catalog that works with _render_catalog_controls + _compute_and_render_totals.
    Prices are placeholders (0) until real dictionaries exist.
    """
    return {
        "meta": {
            "category": category,
            "display_label": label,
            "hero_image": hero_image,
            "id": f"{category}-{stem}",
        },
        "controls": [
            {
                "id": "footprint",
                "label": "Footprint",
                "type": "single",
                "required": True,
                "options": [
                    {
                        "key": "fp-generic",
                        "label": "Generic",
                        "base_value": 0,
                        "dims": {"width_in": 24, "depth_in": 24},
                        "rules": {"header_allowed": True, "shipper_allowed": True},
                    }
                ],
                "notes": "Placeholder until parts are defined.",
            },
            {
                "id": "header",
                "label": "Header",
                "type": "single",
                "required": True,
                "options": [
                    {"key": "header-yes", "label": "Yes", "base_value": 0},
                    {"key": "header-no", "label": "No", "base_value": 0},
                ],
                "notes": "Placeholder switch.",
            },
            {
                "id": "shipper",
                "label": "Shipper",
                "type": "single",
                "required": True,
                "options": [
                    {"key": "shipper-yes", "label": "Yes", "base_value": 0},
                    {"key": "shipper-no", "label": "No", "base_value": 0},
                ],
                "notes": "Placeholder switch.",
            },
            {
                "id": "assembly",
                "label": "Assembly",
                "type": "single",
                "required": True,
                "options": [
                    {"key": "assembly-kdf", "label": "KDF", "base_value": 0},
                    {"key": "assembly-turnkey", "label": "Turnkey", "base_value": 0},
                ],
                "notes": "Placeholder switch.",
            },
            {
                "id": "product_touches",
                "label": "Product Touches",
                "type": "number",
                "required": False,
                "min": 0,
                "notes": "Placeholder; only used when Assembly = Turnkey.",
            },
            {
                "id": "quantity",
                "label": "Quantity",
                "type": "number",
                "required": True,
                "min": 1,
                "notes": "Used for unit tiers and program total.",
            },
        ],
        "parts": {
            "footprint-fp-generic": {"label": f"{label} Base", "base_value": 0},
            "header-unit": {"label": "Header", "base_value": 0},
            "header-none": {"label": "No Header", "base_value": 0},
            "shipper-unit": {"label": "Shipper", "base_value": 0},
            "assembly-touch-unit": {"label": "Assembly Touch (per touch)", "base_value": 0},
        },
        "rules": {
            "resolve_footprint_base": {
                "based_on_control": "footprint",
                "map": {"fp-generic": "footprint-fp-generic"},
            },
            "resolve_header": {
                "when_control": "header",
                "when_value": "header-yes",
                "based_on_control": "footprint",
                "match_on_dim": "width_in",
                "map": {"24": "header-unit"},
                "else": "header-none",
            },
            "resolve_shipper": {
                "when_control": "shipper",
                "when_value": "shipper-yes",
                "based_on_control": "footprint",
                "map": {"fp-generic": "shipper-unit"},
                "else": None,
            },
            "resolve_assembly_touches": {
                "when_control": "assembly",
                "when_value": "assembly-turnkey",
                "quantity_control": "product_touches",
                "min_quantity": 1,
                "part": "assembly-touch-unit",
                "pricing": "linear",
                "else": None,
            },
        },
        "policy": {
            "matrix_markups": [
                [0.35, 0.4, 0.45],
                [0.3, 0.35, 0.4],
                [0.25, 0.3, 0.35],
            ],
            "unit_tiers": [
                {"min_qty": 1, "max_qty": 199, "factor": 1.0},
                {"min_qty": 200, "max_qty": 499, "factor": 0.98},
                {"min_qty": 500, "max_qty": 999, "factor": 0.96},
                {"min_qty": 1000, "max_qty": 1999, "factor": 0.94},
                {"min_qty": 2000, "max_qty": 2999, "factor": 0.92},
                {"min_qty": 3000, "max_qty": None, "factor": 0.9},
            ],
            "tier_boundary": "inclusive",
            "display_weight_round": 0.01,
            "markup_application": "program_total",
        },
    }


# ---------- PDQ CONFIG ----------
def render_pdq_form(selected_stem: str) -> None:
    catalog_path = PDQ_CATALOG_BY_STEM.get(selected_stem, "data/catalog/pdq.json")
    catalog = cat.load_catalog(catalog_path)
    st.write("DEBUG smoothing policy:", ((catalog.get("policy", {}) or {}).get("break_pricing", {}) or {}).get("sub_100_smoothing", {}))
    st.write("DEBUG pdq derived:", ((catalog.get("parts", {}) or {}).get("pdq-fp-36x12x12", {}) or {}).get("derived_breaks"))
    st.write("DEBUG qty99 pdq price:", pricing.parts_value(catalog, "pdq-fp-36x12x12", program_qty=99))

    st.divider()
    display_label = (catalog.get("meta", {}) or {}).get("display_label", "PDQ Tray")
    st.subheader(f"{display_label.upper()} — Configuration")

    if "form" not in st.session_state:
        st.session_state.form = {}
    form: Dict = st.session_state.form

    unlocked = _render_catalog_controls(catalog=catalog, form=form, prefix="pdq")

    _compute_and_render_totals(
        catalog=catalog,
        form=form,
        wc_key="wc_idx",
        wc_default=(2, 0),
        unlocked=unlocked,
    )


# ---------- SIDEKICK CONFIG ----------
def _pick_sidekick_fixed_footprint(catalog: Dict, form: Dict, *, prefix: str = "sidekick") -> str:
    """
    Returns the footprint option key that should be forced into `form["footprint"]`.

    Supports:
      - Pegged catalogs: footprint has exactly 1 option (fp-24 or fp-48) => use it.
      - Shelved catalogs: footprint has multiple options AND an `edge` control.
        Convention: footprint option keys contain "-raw" / "-clean" (or end with those).
        If edge is unset, default to raw footprint when available.
    """
    fp_ctrl = cat.find_control(catalog, "footprint") or {}
    fp_opts = fp_ctrl.get("options", []) or []

    if not fp_opts:
        return "fp-24"  # safe fallback

    if len(fp_opts) == 1:
        return str(fp_opts[0].get("key") or "fp-24")

    # Shelved case: multiple footprint options, keyed by edge
    # Prefer the current widget selection (label) over stale form state.
    edge = form.get("edge")
    widget_key = f"{prefix}__edge"
    if widget_key in st.session_state:
        edge_ctrl = cat.find_control(catalog, "edge") or {}
        edge_opts = edge_ctrl.get("options", []) or []
        label_to_key = {
            str(o.get("label")): str(o.get("key"))
            for o in edge_opts
            if o.get("label") is not None and o.get("key") is not None
        }
        edge = label_to_key.get(str(st.session_state.get(widget_key)))

    edge = None if edge in (None, "", "__unset__") else str(edge)

    keys = [str(o.get("key") or "") for o in fp_opts if o.get("key")]

    def _match_edge(k: str, e: str) -> bool:
        kl = k.lower()
        el = e.lower()
        return kl.endswith(f"-{el}") or f"-{el}-" in kl or kl.endswith(el)

    if edge:
        for k in keys:
            if _match_edge(k, edge):
                return k

    # Default edge to raw if present
    for k in keys:
        if _match_edge(k, "raw"):
            return k

    return keys[0] if keys else "fp-24"


def _sidekick_footprint_pill(catalog: Dict, fp_key: str) -> str:
    """
    Builds the pill text (e.g., 'Footprint: 24', 'Footprint: 48', 'Footprint: 24 (Raw)').
    Uses footprint dims when present; falls back to the key.
    """
    fp_ctrl = cat.find_control(catalog, "footprint") or {}
    fp_opts = fp_ctrl.get("options", []) or []

    opt = next((o for o in fp_opts if o.get("key") == fp_key), None) or {}
    dims = opt.get("dims", {}) or {}
    w = dims.get("width_in")

    label = f"{w}" if w is not None else str(opt.get("label") or fp_key)

    fp_key_l = fp_key.lower()
    if "raw" in fp_key_l:
        return f"Footprint: {label} (Raw)"
    if "clean" in fp_key_l:
        return f"Footprint: {label} (Clean)"
    return f"Footprint: {label}"


def render_sidekick_form(selected_stem: str) -> None:
    catalog_path = f"data/catalog/{selected_stem}.json"
    catalog = cat.load_catalog(catalog_path)

    st.divider()
    display_label = (catalog.get("meta", {}) or {}).get("display_label", "Sidekick")
    st.subheader(f"{display_label.upper()} — Configuration")

    if "sidekick_form" not in st.session_state:
        st.session_state.sidekick_form = {}
    form: Dict = st.session_state.sidekick_form

    fixed_fp_key = _pick_sidekick_fixed_footprint(catalog, form, prefix="sidekick")
    st.markdown(f"<div class='pill'>{_sidekick_footprint_pill(catalog, fixed_fp_key)}</div>", unsafe_allow_html=True)

    unlocked = _render_catalog_controls(
        catalog=catalog,
        form=form,
        prefix="sidekick",
        fixed_footprint=fixed_fp_key,
    )

    _compute_and_render_totals(
        catalog=catalog,
        form=form,
        wc_key="sidekick_wc_idx",
        wc_default=(2, 0),
        unlocked=unlocked,
    )

def _selected_tile_meta(selected_key: str) -> Tuple[str, str, str, str]:
    """
    Returns (category, stem, label, hero_image) for the selected tile.
    """
    category, stem = selected_key.split("/", 1)
    label = LABEL_OVERRIDES.get(stem, stem.replace("_", " ").replace("-", " ").title())
    hero_image = f"{ASSETS_ROOT}/{category}/{stem}.png"
    return category, stem, label, hero_image


def render_generic_display_form(*, selected_key: str, prefix: str) -> None:
    category, stem, label, hero_image = _selected_tile_meta(selected_key)

    catalog = _generic_catalog_for_selected_tile(
        category=category,
        stem=stem,
        label=label,
        hero_image=hero_image,
    )

    st.divider()
    st.subheader(f"{label.upper()} — Configuration")
    st.caption("Placeholder configuration until pricing dictionaries are created.")

    state_key = f"{prefix}_form"
    if state_key not in st.session_state:
        st.session_state[state_key] = {}
    form: Dict = st.session_state[state_key]

    unlocked = _render_catalog_controls(catalog=catalog, form=form, prefix=prefix)

    _compute_and_render_totals(
        catalog=catalog,
        form=form,
        wc_key=f"{prefix}_wc_idx",
        wc_default=(2, 0),
        unlocked=unlocked,
    )



# ---------- Router ----------
# ---------- Router ----------
if selected_key and selected_key.startswith("pdq/"):
    stem = selected_key.split("/", 1)[1]
    render_pdq_form(stem)

elif selected_key and selected_key.startswith("sidekick/"):
    stem = selected_key.split("/", 1)[1]
    render_sidekick_form(stem)

elif selected_key and (
    selected_key.startswith("halfpallet/")
    or selected_key.startswith("dumpbin/")
):
    # Generic placeholder config for now (no JSON dictionaries yet)
    prefix = selected_key.split("/", 1)[0]
    render_generic_display_form(selected_key=selected_key, prefix=prefix)

elif selected_key:
    st.divider()
    st.subheader("Configuration")
    st.caption("Fields for this display type will be added soon.")
else:
    st.caption("Select a display above to configure its details.")
