# pages/Display.py
# Display + Structure page with a live 2D SVG preview (no external assets)

from __future__ import annotations
from datetime import datetime
from typing import Dict, Tuple

import streamlit as st
from streamlit.components.v1 import html

# ----- Page config + Raleway -----
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
      .kkg-meta { color:#6b7280; font-size:13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----- Bootstrap session state -----
if "active_spec" not in st.session_state:
    st.session_state.active_spec = False
if "display" not in st.session_state:
    st.session_state.display = {
        "type": "pallet",            # pallet|pdq|sidekick
        "size": "full",              # full|half|quarter
        "configuration": "pinwheel", # complex|pinwheel|back2back
        "pallet_size": "48",         # 48|40|equal
    }
if "structure" not in st.session_state:
    st.session_state.structure = {
        "top": "topcap",             # cutback|topcap|open
        "header": "standard",        # premium|standard|gondola
        "header_depth": 8,           # inches if gondola
        "corrugate": "oyster",       # kemi|oyster|kraft
        "shroud": "standard",        # premium|standard|basic
    }
if "validation" not in st.session_state:
    st.session_state.validation = {}

# ----- Gate: allow starting a spec from here if needed -----
if not st.session_state.active_spec:
    st.title("Display & Structure")
    st.caption("Start a spec to configure the display.")
    if st.button("Start New Spec", type="primary"):
        st.session_state.active_spec = True
        st.session_state["draft_id"] = datetime.utcnow().strftime("DRAFT-%Y%m%d-%H%M%S")
        st.rerun()
    st.page_link("Home.py", label="Back to Home", icon="🏠")
    st.stop()

# ----- Options (labels) -----
TYPE_OPTS = {"pallet": "Pallet", "pdq": "PDQ", "sidekick": "Sidekick / Powerwing"}
SIZE_OPTS = {"full": "Full", "half": "Half", "quarter": "Quarter"}
CFG_OPTS  = {"complex": "Complex", "pinwheel": "Pinwheel", "back2back": "Back-to-Back"}
PALLET_OPTS = {"48": '48"', "40": '40"', "equal": "Equal Sides"}

TOP_OPTS = {"cutback": "Cut Back", "topcap": "Top Cap", "open": "Open"}
HEADER_OPTS = {"premium": "Premium", "standard": "Standard", "gondola": "Gondola-Friendly"}
CORR_OPTS = {"kemi": "Kemi (Coated)", "oyster": "Oyster", "kraft": "Kraft"}
SHROUD_OPTS = {"premium": "Premium", "standard": "Standard", "basic": "Basic"}

# Corrugate fills (subtle, tweakable)
CORR_COLORS = {
    "kemi":   "#dcdfe6",
    "oyster": "#e8e6e0",
    "kraft":  "#d4b892",
}
ACCENT = "#4E5BA8"
STROKE = "#3b3f46"
SHADOW = "rgba(0,0,0,0.10)"

# ----- UI -----
st.markdown("## Display & Structure")
st.caption("Pick the chassis and structural features. The preview updates live.")

left, right = st.columns([0.55, 0.45], gap="large")

with left:
    st.subheader("Display")
    c1, c2 = st.columns(2)
    ui_type = st.selectbox(
        "Type",
        list(TYPE_OPTS.values()),
        index=list(TYPE_OPTS).index(st.session_state.display["type"]),
    )
    ui_size = st.selectbox(
        "Size",
        list(SIZE_OPTS.values()),
        index=list(SIZE_OPTS).index(st.session_state.display["size"]),
    )
    c3, c4 = st.columns(2)
    ui_cfg = st.selectbox(
        "Configuration",
        list(CFG_OPTS.values()),
        index=list(CFG_OPTS).index(st.session_state.display["configuration"]),
    )
    ui_pallet = st.selectbox(
        "Pallet Size",
        list(PALLET_OPTS.values()),
        index=list(PALLET_OPTS).index(st.session_state.display["pallet_size"]),
    )

    st.divider()
    st.subheader("Structure")
    c5, c6 = st.columns(2)
    ui_top = st.selectbox(
        "Top of Display",
        list(TOP_OPTS.values()),
        index=list(TOP_OPTS).index(st.session_state.structure["top"]),
    )
    ui_header = st.selectbox(
        "Header",
        list(HEADER_OPTS.values()),
        index=list(HEADER_OPTS).index(st.session_state.structure["header"]),
    )

    ui_header_depth = None
    if ui_header == "Gondola-Friendly":
        ui_header_depth = st.number_input(
            "Max Header Depth (inches)",
            min_value=1,
            max_value=24,
            step=1,
            value=int(st.session_state.structure.get("header_depth", 8)),
        )

    c7, c8 = st.columns(2)
    ui_corr = st.selectbox(
        "Corrugate Material",
        list(CORR_OPTS.values()),
        index=list(CORR_OPTS).index(st.session_state.structure["corrugate"]),
    )
    ui_shroud = st.selectbox(
        "Shroud",
        list(SHROUD_OPTS.values()),
        index=list(SHROUD_OPTS).index(st.session_state.structure["shroud"]),
    )

# ----- Sync selections back to stable keys -----
rev = lambda d: {v: k for k, v in d.items()}
st.session_state.display.update({
    "type": rev(TYPE_OPTS)[ui_type],
    "size": rev(SIZE_OPTS)[ui_size],
    "configuration": rev(CFG_OPTS)[ui_cfg],
    "pallet_size": rev(PALLET_OPTS)[ui_pallet],
})
st.session_state.structure.update({
    "top": rev(TOP_OPTS)[ui_top],
    "header": rev(HEADER_OPTS)[ui_header],
    "corrugate": rev(CORR_OPTS)[ui_corr],
    "shroud": rev(SHROUD_OPTS)[ui_shroud],
})
if st.session_state.structure["header"] == "gondola":
    st.session_state.structure["header_depth"] = int(ui_header_depth or 8)
else:
    st.session_state.structure["header_depth"] = None

# ----- Renderer (parametric SVG) -----
def _size_scale(size_key: str) -> float:
    return {"full": 1.0, "half": 0.8, "quarter": 0.6}[size_key]

def _path(points: list[Tuple[float, float]]) -> str:
    return " ".join([("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(points)]) + " Z"

def _poly(points: list[Tuple[float, float]], fill: str, stroke: str = STROKE, sw: float = 2.0) -> str:
    return f'<path d="{_path(points)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />'

def make_svg(display: Dict, structure: Dict, w: int = 520, h: int = 440) -> str:
    s = _size_scale(display["size"])
    fw, fh = 210 * s, 200 * s       # front width/height
    depth = 90 * s                  # side depth
    ox, oy = 150, 190               # origin (front-bottom-left)
    dx, dy = depth, -depth * 0.45   # iso offsets
    corr = CORR_COLORS.get(structure["corrugate"], "#e5e7eb")

    front = [(ox, oy), (ox + fw, oy), (ox + fw, oy - fh), (ox, oy - fh)]
    side  = [(ox + fw, oy), (ox + fw + dx, oy + dy), (ox + fw + dx, oy + dy - fh), (ox + fw, oy - fh)]

    topcap_h = 16 * s if structure["top"] == "topcap" else 0
    cutback = structure["top"] == "cutback"

    hdr_heights = {"premium": 60, "standard": 40, "gondola": 28}
    hdr_h = hdr_heights[structure["header"]] * s
    hdr_depth = (structure.get("header_depth") or 10) * (1.8 * s if structure["header"] == "gondola" else 1.2 * s)

    shroud_pad = {"premium": 8, "standard": 4, "basic": 0}[structure["shroud"]] * s

    svg = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    svg.append(f'<ellipse cx="{ox+fw*0.7:.1f}" cy="{oy+10:.1f}" rx="{(fw+depth)*0.55:.1f}" ry="11" fill="{SHADOW}"/>')

    if shroud_pad > 0:
        p = shroud_pad
        frame_front = [(ox - p, oy + p), (ox + fw + p, oy + p), (ox + fw + p, oy - fh - p), (ox - p, oy - fh - p)]
        svg.append(_poly(frame_front, "none", ACCENT, 1.6))

    svg.append(_poly(side, corr, STROKE, 2))

    if cutback:
        cb = 22 * s
        front_cb = [(ox, oy), (ox + fw, oy), (ox + fw, oy - fh + cb), (ox + fw - cb, oy - fh), (ox, oy - fh)]
        svg.append(_poly(front_cb, corr, STROKE, 2))
    else:
        svg.append(_poly(front, corr, STROKE, 2))

    if topcap_h > 0 or structure["top"] == "open":
        th = topcap_h
        top_face = [
            (ox, oy - fh),
            (ox + fw, oy - fh),
            (ox + fw + dx, oy + dy - fh - th),
            (ox + dx, oy + dy - fh - th),
        ]
        fill_top = corr if structure["top"] == "open" else "#ffffff"
        svg.append(_poly(top_face, fill_top, STROKE, 2))

    hx1, hy1 = ox, oy - fh - (hdr_h if structure["header"] else 0)
    hx2, hy2 = ox + fw, oy - fh
    header_front = [(hx1, hy2), (hx2, hy2), (hx2, hy1), (hx1, hy1)]
    if structure["header"]:
        svg.append(_poly(header_front, "#ffffff", STROKE, 2))
        header_side = [(hx2, hy2), (hx2 + dx, hy2 + dy), (hx2 + dx, hy2 + dy - hdr_h * 0.98), (hx2, hy1)]
        svg.append(_poly(header_side, "#f5f7fb", STROKE, 2))
        if structure["header"] == "gondola":
            gx1 = ox + fw + min(dx, hdr_depth)
            gy1 = oy + dy - fh - topcap_h
            svg.append(f'<line x1="{ox+fw}" y1="{oy - fh}" x2="{gx1:.1f}" y2="{gy1:.1f}" stroke="{ACCENT}" stroke-width="2" stroke-dasharray="5,4"/>')

    if display["configuration"] in ("pinwheel", "back2back", "complex"):
        dash = "4,4" if display["configuration"] != "complex" else "2,3"
        svg.append(f'<line x1="{ox+fw*0.5:.1f}" y1="{oy:.1f}" x2="{ox+fw*0.5:.1f}" y2="{oy-fh:.1f}" stroke="{STROKE}" stroke-width="1.2" stroke-dasharray="{dash}"/>')
        if display["configuration"] in ("pinwheel", "complex"):
            svg.append(f'<line x1="{ox:.1f}" y1="{oy-fh*0.5:.1f}" x2="{ox+fw:.1f}" y2="{oy-fh*0.5:.1f}" stroke="{STROKE}" stroke-width="1.2" stroke-dasharray="{dash}"/>')

    svg.append(f'<text x="{ox:.1f}" y="{oy - fh - hdr_h - 10:.1f}" font-family="Raleway, sans-serif" font-size="12" fill="{STROKE}">{TYPE_OPTS[display["type"]]} • {SIZE_OPTS[display["size"]]}</text>')
    svg.append("</svg>")
    return "".join(svg)

svg_markup = make_svg(st.session_state.display, st.session_state.structure)

with right:
    st.subheader("Preview")
    html(svg_markup, height=460)
    t = st.session_state.display
    s = st.session_state.structure
    st.caption(
        f'**Type:** {TYPE_OPTS[t["type"]]} · **Size:** {SIZE_OPTS[t["size"]]} · '
        f'**Config:** {CFG_OPTS[t["configuration"]]} · **Pallet:** {PALLET_OPTS[t["pallet_size"]]}'
    )
    st.caption(
        f'**Top:** {TOP_OPTS[s["top"]]} · **Header:** {HEADER_OPTS[s["header"]]}'
        + (f' ({s["header_depth"]}" max depth)' if s["header"] == "gondola" and s.get("header_depth") else "")
        + f' · **Corrugate:** {CORR_OPTS[s["corrugate"]]} · **Shroud:** {SHROUD_OPTS[s["shroud"]]}'
    )

st.divider()

# ----- Validation + nav stubs -----
valid = all([
    st.session_state.display["type"],
    st.session_state.display["size"],
    st.session_state.display["configuration"],
    st.session_state.display["pallet_size"],
    st.session_state.structure["top"],
    st.session_state.structure["header"],
    st.session_state.structure["corrugate"],
    st.session_state.structure["shroud"],
]) and (st.session_state.structure["header"] != "gondola" or (st.session_state.structure.get("header_depth") and st.session_state.structure["header_depth"] > 0))

cL, cR = st.columns([1, 1])
with cL:
    st.page_link("Home.py", label="Back to Home", icon="🏠")
with cR:
    st.button("Continue", type="primary", disabled=not valid, help="Wire this to the next page when it exists.")
