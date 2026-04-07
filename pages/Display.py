# pages/Display.py
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
ROW_TITLES = {
    "pdq": "PDQs",
    "sidekick": "Sidekicks",
    "halfpallet": "Half Pallets",
    "dumpbin": "Dump Bins",
}

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

PDQ_TYPE_BY_STEM = {
    "digital_pdq_tray": "angled",
    "clipped_pdq_tray": "clipped",
    "square_pdq_tray": "square",
    "standardclub_pdq_tray": "standard",
}

PDQ_TYPE_LABELS = {
    "angled": "Angled PDQ",
    "clipped": "Clipped PDQ",
    "square": "Square PDQ",
    "standard": "Standard Club PDQ",
}

PDQ_MULTIPLIER_BY_TYPE = {
    "angled": 1.00,
    "clipped": 1.10,
    "square": 1.15,
    "standard": 1.20,
}

HALFPALLET_CATALOG_BY_STEM = {
    "frontfaced_hp": "data/catalog/frontfaced_hp.json",
    "threesided_hp": "data/catalog/threesided_hp.json",
}

DUMPBIN_CATALOG_BY_STEM = {
    "dump_bin": "data/catalog/dump_bin.json",
}

SIDEKICK_SHARED_CATALOG_PATH = "data/catalog/sidekick.json"
SIDEKICK_HOOKS_FP_BY_STEM = {
    "sidekickpeg24": "sk-24-hooks",
    "sidekickpeg48": "sk-48-hooks",
}
SIDEKICK_SHELVES_FP_BY_STEM_AND_STYLE = {
    ("sidekickshelves24", "Rolled Sides"): "sk-24-shelves-rolled",
    ("sidekickshelves24", "Built-in Shelves"): "sk-24-shelves-built",
    ("sidekickshelves48", "Rolled Sides"): "sk-48-shelves-rolled",
    ("sidekickshelves48", "Built-in Shelves"): "sk-48-shelves-built",
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
            font-size: 22px;
            color: #111827;
            transform: rotate(-90deg);
            white-space: nowrap;
            user-select: none;
            margin-top: 180px;
          }}
          .wc-axis-bottom {{
            text-align: center;
            font-weight: 900;
            font-size: 22px;
            margin-top: 14px;
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
    """
    required_chain_ok = True

    if fixed_footprint:
        form["footprint"] = fixed_footprint

    def _pdq_fulfillment_caption(ctrl_id: str) -> None:
        """
        PDQ-only: show per-display (pre-markup) fulfillment/assembly lines under the relevant fields.
        Displayed only when the computed per-display amount is > 0.00.
        """
        try:
            if prefix != "pdq":
                return
            meta = catalog.get("meta", {}) or {}
            if meta.get("category") != "pdq":
                return
            if form.get("assembly") != "assembly-turnkey":
                return

            fp_key = form.get("footprint")
            if not fp_key:
                return

            program_qty = int(form.get("quantity") or 1)
            program_qty = max(program_qty, 1)
            production_multiplier = float(
                form.get("pdq_multiplier")
                or pricing.pdq_production_multiplier(str(form.get("pdq_type") or "angled"))
            )
            rules = catalog.get("rules", {}) or {}

            if ctrl_id == "divider_count":
                divider_count = int(form.get("divider_count") or 0)
                if divider_count <= 0:
                    return
                r = rules.get("resolve_fulfillment_divider_assembly", {}) or {}
                part_key = (r.get("map", {}) or {}).get(fp_key)
                if not part_key:
                    return
                per_display = float(
                    pricing.parts_value(
                        catalog,
                        part_key,
                        program_qty=program_qty,
                        item_qty=divider_count,
                        production_multiplier=production_multiplier,
                    )
                )
                if per_display <= 0.0:
                    return
                total = per_display * program_qty
                st.caption(
                    f"Divider assembly applied (pre-markup): Adding assembly for {divider_count} dividers adds "
                    f"${per_display:,.2f} per display (× {program_qty:,} displays = ${total:,.2f})."
                )
                return

            if ctrl_id == "product_touches":
                touches = int(form.get("product_touches") or 0)
                if touches <= 0:
                    return
                r = rules.get("resolve_assembly_touches", {}) or {}
                part_key = (r.get("map", {}) or {}).get(fp_key) or r.get("part")
                if not part_key:
                    return
                per_display = float(
                    pricing.parts_value(
                        catalog,
                        part_key,
                        program_qty=program_qty,
                        item_qty=touches,
                        production_multiplier=production_multiplier,
                    )
                )
                if per_display <= 0.0:
                    return
                total = per_display * program_qty
                st.caption(
                    f"Product fill applied (pre-markup): Adding {touches} product fills adds "
                    f"${per_display:,.2f} per display (× {program_qty:,} displays = ${total:,.2f})."
                )
                return

            if ctrl_id == "header":
                if form.get("header") != "header-yes":
                    return
                r = rules.get("resolve_fulfillment_packout_header", {}) or {}
                part_key = (r.get("map", {}) or {}).get(fp_key)
                if not part_key:
                    return
                per_display = float(
                    pricing.parts_value(
                        catalog,
                        part_key,
                        program_qty=program_qty,
                        production_multiplier=production_multiplier,
                    )
                )
                if per_display <= 0.0:
                    return
                total = per_display * program_qty
                st.caption(
                    "Header pack-out applied (pre-markup): Because Header = Yes, header pack-out adds "
                    f"${per_display:,.2f} per display (× {program_qty:,} displays = ${total:,.2f})."
                )
        except Exception:
            return

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
                if cid == "header":
                    _pdq_fulfillment_caption("header")

        elif ctype == "number":
            min_v = ctrl.get("min", 0)
            saved = form.get(cid)

            touched_key = f"{prefix}__{cid}__touched"
            prev_val = st.session_state.get(f"{prefix}__{cid}__prev")

            is_int = cid in (
                "quantity",
                "divider_count",
                "product_touches",
                "pegs_count",
                "shelf_count",
                "shelves_count",
            )
            number_label = label
            if prefix == "sidekick" and cid == "shelves_count":
                selected_key = str(st.session_state.get("selected_display_key") or "")
                sidekick_mode = st.session_state.get("sidekick_mode")
                is_hooks = sidekick_mode == "hooks" or selected_key.startswith("sidekick/sidekickpeg")
                number_label = "Number of Pegs" if is_hooks else "Number of Shelves"
            if is_int:
                default = int(saved) if saved is not None else (max(1, int(min_v)) if cid == "quantity" else int(min_v))
                val = st.number_input(
                    number_label,
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
                    number_label,
                    min_value=float(min_v),
                    step=0.01,
                    value=float(default),
                    key=widget_key,
                    disabled=not enabled,
                )
                if enabled:
                    form[cid] = float(val)

            if enabled:
                current = form.get(cid)
                if prev_val is None:
                    st.session_state[f"{prefix}__{cid}__prev"] = current
                else:
                    if current != prev_val:
                        st.session_state[touched_key] = True
                        st.session_state[f"{prefix}__{cid}__prev"] = current

                if cid in ("divider_count", "product_touches"):
                    _pdq_fulfillment_caption(cid)

        else:
            st.caption(f"Unsupported control type: {ctype} for `{cid}`")

        if required_chain_ok:
            required_chain_ok = _is_required_answered(ctrl, form, prefix=prefix)

        if not required_chain_ok:
            st.caption("Complete the current step to continue.")

    return bool(required_chain_ok)


def _compute_and_render_totals(
    *,
    catalog: Dict,
    form: Dict,
    wc_key: str,
    wc_default: Tuple[int, int],
    unlocked: bool,
    catalog_path: Optional[str] = None,
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
    pdq_multiplier = (
        float(
            form.get("pdq_multiplier")
            or pricing.pdq_production_multiplier(str(form.get("pdq_type") or "angled"))
        )
        if (catalog.get("meta", {}) or {}).get("category") == "pdq"
        else 1.0
    )

    parts = catalog.get("parts", {}) or {}

    def _parts_value_with_qty(part_key: str, *, item_qty: int | None = None) -> float:
        """
        Prefer break-aware pricing via `program_qty`.
        For adder-cap fulfillment parts, pass the entered count via `item_qty`
        so pricing can compute base+adders.
        """
        try:
            return float(
                pricing.parts_value(
                    catalog,
                    part_key,
                    program_qty=qty,
                    item_qty=item_qty,
                    production_multiplier=pdq_multiplier,
                )
            )
        except TypeError as exc:
            msg = str(exc)
            if "unexpected keyword" in msg:
                if item_qty is not None:
                    try:
                        return float(
                            pricing.parts_value(
                                catalog,
                                part_key,
                                program_qty=qty,
                                production_multiplier=pdq_multiplier,
                            )
                        )
                    except TypeError:
                        pass
                try:
                    return float(
                        pricing.parts_value(catalog, part_key, production_multiplier=pdq_multiplier)
                    )
                except Exception:
                    return 0.0
            raise

    per_unit_parts_subtotal = 0.0
    for part_key, q_per_display in resolved:
        part_spec = parts.get(part_key, {}) or {}
        pricing_family = str(part_spec.get("pricing_family") or "").strip()

        if pricing_family == "fulfillment_adder_cap":
            per_unit_parts_subtotal += _parts_value_with_qty(part_key, item_qty=int(q_per_display))
        else:
            per_unit_parts_subtotal += _parts_value_with_qty(part_key) * int(q_per_display)

    program_base = per_unit_parts_subtotal * qty
    markup_pct = pricing.matrix_markup_pct(policy, selected_rc)
    final_total = program_base * (1.0 + markup_pct)
    final_per_unit = final_total / max(qty, 1)
    meta = catalog.get("meta", {}) or {}

    if debug_mode and meta.get("category") == "sidekick":
        selected_key = str(st.session_state.get("selected_display_key") or "")
        selected_category = ""
        selected_stem = ""
        if "/" in selected_key:
            selected_category, selected_stem = selected_key.split("/", 1)

        any_fulfillment = any(str(part_key).startswith("fulfill-") for part_key, _ in resolved)
        any_adder_cap = any(
            str((parts.get(part_key, {}) or {}).get("pricing_family") or "").strip() == "fulfillment_adder_cap"
            for part_key, _ in resolved
        )

        rows = []
        for part_key, q_per_display in resolved:
            part_spec = parts.get(part_key, {}) or {}
            pricing_family = str(part_spec.get("pricing_family") or "").strip()
            q_int = int(q_per_display)
            if pricing_family == "fulfillment_adder_cap":
                per_display_value = _parts_value_with_qty(part_key, item_qty=q_int)
            else:
                per_display_value = _parts_value_with_qty(part_key) * q_int

            rows.append(
                {
                    "part_key": part_key,
                    "qty_per_display": q_per_display,
                    "pricing_family": pricing_family or None,
                    "per_display_value": round(float(per_display_value), 4),
                    "program_value": round(float(per_display_value) * qty, 4),
                    "label": part_spec.get("label"),
                }
            )

        with st.expander("DEBUG (Sidekick): footprint + resolved parts", expanded=False):
            st.write("selected_display_key:", selected_key or None)
            st.write("selected_stem:", selected_stem or None)
            st.write("selected_category:", selected_category or None)
            if catalog_path:
                st.write("catalog_path:", catalog_path)
            st.write("form.footprint:", form.get("footprint"))
            st.write("width_in:", width_in, "depth_in:", depth_in)
            st.write("qty:", qty)
            st.json(form)
            st.write("resolved_line_count:", len(resolved))
            st.write("any_fulfillment:", any_fulfillment)
            st.write("any_adder_cap:", any_adder_cap)
            st.dataframe(rows, use_container_width=True)
            st.write("per_unit_parts_subtotal:", per_unit_parts_subtotal)
            st.write("program_base:", program_base)
            st.write("markup_pct:", markup_pct)
            st.write("final_total:", final_total)
            st.write("final_per_unit:", final_per_unit)

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
    if (catalog.get("meta", {}) or {}).get("category") == "pdq":
        st.caption(
            f"PDQ production uplift: {(pdq_multiplier - 1.0) * 100:.0f}% "
            "(applied to production unit prices only; fulfillment is unchanged)."
        )
    st.caption("Note: Markup will be applied at the end.")
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

    if meta.get("category") != "pdq":
        st.markdown(
            "<div class='muted'>All values are placeholders until prices are updated in the catalog.</div>",
            unsafe_allow_html=True,
        )


# ---------- Header ----------
st.markdown("## Select the type of display")
debug_mode = st.sidebar.checkbox("Debug pricing (temporary)", value=False, key="debug_pricing")

# ---------- Rows ----------
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


def _selected_tile_meta(selected_key: str) -> Tuple[str, str, str, str]:
    """
    Returns (category, stem, label, hero_image) for the selected tile.
    """
    category, stem = selected_key.split("/", 1)
    label = LABEL_OVERRIDES.get(stem, stem.replace("_", " ").replace("-", " ").title())
    hero_image = f"{ASSETS_ROOT}/{category}/{stem}.png"
    return category, stem, label, hero_image


def _catalog_path_for_tile(category: str, stem: str) -> Optional[str]:
    """
    Returns a catalog path for tiles that have real JSON dictionaries,
    otherwise None to indicate fallback to generic placeholder.
    """
    if category == "pdq":
        return PDQ_CATALOG_BY_STEM.get(stem, "data/catalog/pdq.json")
    if category == "sidekick":
        return SIDEKICK_SHARED_CATALOG_PATH
    if category == "halfpallet":
        return HALFPALLET_CATALOG_BY_STEM.get(stem)
    if category == "dumpbin":
        return DUMPBIN_CATALOG_BY_STEM.get(stem)
    return None


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

    st.divider()
    display_label = (catalog.get("meta", {}) or {}).get("display_label", "PDQ Tray")
    st.subheader(f"{display_label.upper()} — Configuration")

    if "form" not in st.session_state:
        st.session_state.form = {}
    form: Dict = st.session_state.form
    pdq_type = str(st.session_state.get("pdq_type") or PDQ_TYPE_BY_STEM.get(selected_stem, "angled"))
    pdq_multiplier = float(
        st.session_state.get("pdq_multiplier")
        or PDQ_MULTIPLIER_BY_TYPE.get(pdq_type, 1.00)
    )
    form["pdq_type"] = pdq_type
    form["pdq_multiplier"] = pdq_multiplier
    st.caption(
        f"Selected PDQ type: {PDQ_TYPE_LABELS.get(pdq_type, pdq_type.title())} "
        f"(production multiplier {pdq_multiplier:.2f}x)."
    )

    unlocked = _render_catalog_controls(catalog=catalog, form=form, prefix="pdq")

    _compute_and_render_totals(
        catalog=catalog,
        form=form,
        wc_key="wc_idx",
        wc_default=(2, 0),
        unlocked=unlocked,
        catalog_path=catalog_path,
    )


# ---------- SIDEKICK CONFIG ----------
def render_sidekick_form(selected_stem: str) -> None:
    catalog_path = str(st.session_state.get("selected_catalog_override_path") or "").strip() or SIDEKICK_SHARED_CATALOG_PATH
    catalog = cat.load_catalog(catalog_path)

    st.divider()
    display_label = LABEL_OVERRIDES.get(selected_stem, (catalog.get("meta", {}) or {}).get("display_label", "Sidekick"))
    st.subheader(f"{display_label.upper()} — Configuration")

    if "sidekick_form" not in st.session_state:
        st.session_state.sidekick_form = {}
    form: Dict = st.session_state.sidekick_form

    sidekick_mode = st.session_state.get("sidekick_mode")
    if sidekick_mode is None:
        sidekick_mode = "hooks" if selected_stem in SIDEKICK_HOOKS_FP_BY_STEM else "shelves"

    if sidekick_mode == "hooks":
        fixed_fp_key = str(st.session_state.get("sidekick_footprint_preset") or "").strip() or SIDEKICK_HOOKS_FP_BY_STEM.get(selected_stem, "")
    else:
        shelves_style = str(st.session_state.get("sidekick_shelves_style") or "Rolled Sides")
        shelves_style = st.radio(
            "Shelves Style",
            ["Rolled Sides", "Built-in Shelves"],
            index=0 if shelves_style != "Built-in Shelves" else 1,
            key="sidekick_shelves_style",
            horizontal=True,
        )
        fixed_fp_key = SIDEKICK_SHELVES_FP_BY_STEM_AND_STYLE.get((selected_stem, shelves_style), "")

    unlocked = _render_catalog_controls(
        catalog=catalog,
        form=form,
        prefix="sidekick",
        fixed_footprint=fixed_fp_key or None,
    )

    _compute_and_render_totals(
        catalog=catalog,
        form=form,
        wc_key="sidekick_wc_idx",
        wc_default=(2, 0),
        unlocked=unlocked,
        catalog_path=catalog_path,
    )

def render_generic_display_form(*, selected_key: str) -> None:
    category, stem, label, hero_image = _selected_tile_meta(selected_key)

    catalog_path = _catalog_path_for_tile(category, stem)
    if catalog_path:
        catalog = cat.load_catalog(catalog_path)
        display_label = (catalog.get("meta", {}) or {}).get("display_label", label)
    else:
        catalog = _generic_catalog_for_selected_tile(
            category=category,
            stem=stem,
            label=label,
            hero_image=hero_image,
        )
        display_label = label

    st.divider()
    st.subheader(f"{display_label.upper()} — Configuration")
    if not catalog_path:
        st.caption("Placeholder configuration until pricing dictionaries are created.")

    state_key = f"{category}_{stem}_form"
    if state_key not in st.session_state:
        st.session_state[state_key] = {}
    form: Dict = st.session_state[state_key]

    prefix = f"{category}_{stem}"

    unlocked = _render_catalog_controls(catalog=catalog, form=form, prefix=prefix)

    _compute_and_render_totals(
        catalog=catalog,
        form=form,
        wc_key=f"{category}_{stem}_wc_idx",
        wc_default=(2, 0),
        unlocked=unlocked,
        catalog_path=catalog_path,
    )


# ---------- Router ----------
if selected_key and selected_key.startswith("pdq/"):
    stem = selected_key.split("/", 1)[1]
    render_pdq_form(stem)

elif selected_key and selected_key.startswith("sidekick/"):
    stem = selected_key.split("/", 1)[1]
    render_sidekick_form(stem)

elif selected_key and (selected_key.startswith("halfpallet/") or selected_key.startswith("dumpbin/")):
    render_generic_display_form(selected_key=selected_key)

elif selected_key:
    st.divider()
    st.subheader("Configuration")
    st.caption("Fields for this display type will be added soon.")
else:
    st.caption("Select a display above to configure its details.")

