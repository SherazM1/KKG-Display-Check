# pages/Display.py
# Catalog-driven PDQ UI + rule resolution + preview
# Markup is driven strictly by policy.matrix_markups[row][col] from the 3x3 grid selection.

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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
          .kkg-table th, .kkg-table td { padding:6px 8px; border-bottom:1px solid #f1f5f9; }
          .kkg-table th { text-align:left; color:#475569; font-weight:600; }
          .muted { color:#6b7280; }
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


# ---------- Catalog helpers ----------
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
    """Fixed-size preview without stretching (contain + pad)."""
    img = Image.open(path).convert("RGBA")
    contained = ImageOps.contain(img, (target_w, target_h))
    padded = ImageOps.pad(contained, (target_w, target_h), color=(255, 255, 255))
    return padded.convert("RGB")


# ---------- Query param + matrix component ----------
def _get_query_param(name: str) -> Optional[str]:
    try:
        qp = st.query_params
        if name not in qp:
            return None
        v = qp.get(name)
        if isinstance(v, list):
            return v[0] if v else None
        return str(v) if v is not None else None
    except Exception:
        try:
            qp = st.experimental_get_query_params()
            v = qp.get(name)
            return v[0] if isinstance(v, list) and v else None
        except Exception:
            return None


def _parse_rc(value: str) -> Optional[Tuple[int, int]]:
    try:
        r_s, c_s = [p.strip() for p in value.split(",")]
        r, c = int(r_s), int(c_s)
        if r in (0, 1, 2) and c in (0, 1, 2):
            return r, c
        return None
    except Exception:
        return None

def render_weight_complexity_matrix_component(
    key: str = "wc",
    default: Tuple[int, int] = (2, 0),  # bottom-left
    size_px: int = 420,
) -> Tuple[int, int]:
    """
    Pixel-perfect clickable 3x3 matrix with persistence via URL query params.

    - Uses anchor navigation (?{key}=r,c) with target="_top" so Streamlit reruns on click.
    - No % labels rendered (blank cells).
    - Selected cell gets highlight.
    """
    qp_val = _get_query_param(key)
    qp_rc = _parse_rc(qp_val) if qp_val else None

    if key not in st.session_state:
        st.session_state[key] = qp_rc if qp_rc is not None else default
    elif qp_rc is not None and tuple(st.session_state[key]) != qp_rc:
        st.session_state[key] = qp_rc

    r_sel, c_sel = st.session_state[key]

    def cell_html(r: int, c: int) -> str:
        selected_cls = " wc-selected" if (r == r_sel and c == c_sel) else ""
        href = f"?{key}={r},{c}"
        return f'<a class="wc-cell{selected_cls}" data-r="{r}" data-c="{c}" href="{href}" target="_top" aria-label="Select {r},{c}"></a>'

    height_px = size_px + 70
    html = textwrap.dedent(
        f"""
        <div class="wc-wrap" style="--size:{size_px}px;">
          <div class="wc-y">Weight</div>

          <div class="wc-mid">
            <div class="wc-square" role="grid" aria-label="Weight vs Complexity">
              {cell_html(0,0)}{cell_html(0,1)}{cell_html(0,2)}
              {cell_html(1,0)}{cell_html(1,1)}{cell_html(1,2)}
              {cell_html(2,0)}{cell_html(2,1)}{cell_html(2,2)}
            </div>

            <div class="wc-x">Complexity</div>
          </div>
        </div>

        <style>
          .wc-wrap {{
            display:flex;
            align-items:stretch;
            gap:14px;
            width: 100%;
            margin: 8px 0 6px;
            font-family: 'Raleway', ui-sans-serif, system-ui;
          }}
          .wc-y {{
            display:flex;
            align-items:center;
            justify-content:center;
            font-weight:700;
            color:#111827;
            writing-mode: vertical-rl;
            transform: rotate(180deg);
            user-select:none;
            padding: 0 6px;
          }}
          .wc-mid {{
            display:flex;
            flex-direction:column;
            align-items:flex-start;
          }}
          .wc-square {{
            width: var(--size);
            height: var(--size);
            max-width: 100%;
            border: 2px solid #111827;
            background:#fff;
            display:grid;
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: repeat(3, 1fr);
            box-sizing:border-box;
          }}
          .wc-cell {{
            border-right: 2px solid #111827;
            border-bottom: 2px solid #111827;
            box-sizing:border-box;
            background:#ffffff;
            cursor:pointer;
            display:block;
            text-decoration:none;
          }}
          .wc-cell[data-c="2"] {{ border-right: none; }}
          .wc-cell[data-r="2"] {{ border-bottom: none; }}

          .wc-cell:hover {{ background:#f3f4f6; }}

          .wc-cell.wc-selected {{
            background:#e5e7eb;
            outline: 2px solid #111827;
            outline-offset: -2px;
          }}

          .wc-x {{
            width: var(--size);
            max-width: 100%;
            text-align:center;
            margin-top: 10px;
            font-weight:700;
            color:#111827;
            user-select:none;
          }}

          @media (max-width: 520px) {{
            .wc-wrap {{ gap:10px; }}
            .wc-square {{ width: 100%; height: auto; aspect-ratio: 1 / 1; }}
            .wc-x {{ width: 100%; }}
          }}
        </style>
        """
    )

    components.html(html, height=height_px, scrolling=False)
    return st.session_state[key]

# ---------- Pricing helpers ----------
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


def _matrix_markup_pct(policy: Dict, rc: Tuple[int, int], fallback: float = 0.35) -> float:
    """
    Reads markup strictly from policy.matrix_markups[r][c].
    Expects decimals (0.35 == 35%).
    """
    r, c = rc
    grid = policy.get("matrix_markups")
    if not isinstance(grid, list) or len(grid) != 3:
        return fallback

    try:
        row = grid[r]
        if not isinstance(row, list) or len(row) != 3:
            return fallback
        val = float(row[c])
        if val < 0:
            return fallback
        return val
    except Exception:
        return fallback


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

    # ---- Grid-driven markup (ONLY source of markup) ----
    st.markdown("#### Select Weight Tier and Complexity Level")
    selected_rc = render_weight_complexity_matrix_component(key="wc", default=(1, 1), size_px=420)

    # ---- Resolve parts and compute totals ----
    resolved = _resolve_parts_per_unit(catalog, form)

    qty = int(form.get("quantity", 1) or 1)
    unit_factor = _unit_factor(policy, qty)

    per_unit_parts_subtotal = sum(_parts_value(catalog, part_key) * q for part_key, q in resolved)
    per_unit_after_tier = per_unit_parts_subtotal * unit_factor

    program_base = per_unit_after_tier * qty

    markup_pct = _matrix_markup_pct(policy, tuple(selected_rc), fallback=0.35)
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
            st.table(pd.DataFrame(rows, columns=["Part", "Qty", "Unit $", "Line $"]))

    with right:
        st.markdown("#### Totals")
        st.write(f"Per-unit price (before quantity discount): **${per_unit_parts_subtotal:,.2f}**")
        st.write(f"Per-unit price (after quantity discount): **${per_unit_after_tier:,.2f}**")
        st.write(f"Program base (before markup): **${program_base:,.2f}**")
        st.write(f"Final price (after markup): **${final_total:,.2f}**")

    st.markdown(
        "<div class='muted'>All values are placeholders until prices are updated in the catalog.</div>",
        unsafe_allow_html=True,
    )


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
