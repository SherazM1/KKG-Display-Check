# pages/Display.py
# Distinct silhouettes for Pallet, PDQ tray, Sidekick/Powerwing with live isometric SVG

from __future__ import annotations
from datetime import datetime
from typing import Dict, Tuple, List
import streamlit as st
from streamlit.components.v1 import html

# ---------- Page config + font ----------
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Bootstrap ----------
ss = st.session_state
if "active_spec" not in ss: ss.active_spec = True  # allow direct access during build
if "display" not in ss:
    ss.display = {"type":"pallet","size":"full","configuration":"pinwheel","pallet_size":"48"}
if "structure" not in ss:
    ss.structure = {"top":"topcap","header":"standard","header_depth":8,"corrugate":"oyster","shroud":"standard"}
if "validation" not in ss: ss.validation = {}

# ---------- Options ----------
TYPE_OPTS   = {"pallet":"Pallet","pdq":"PDQ Tray","sidekick":"Sidekick / Powerwing"}
SIZE_OPTS   = {"full":"Full","half":"Half","quarter":"Quarter"}
CFG_OPTS    = {"complex":"Complex","pinwheel":"Pinwheel","back2back":"Back-to-Back"}
PALLET_OPTS = {"48": '48"', "40": '40"', "equal":"Equal Sides"}
TOP_OPTS    = {"cutback":"Cut Back","topcap":"Top Cap","open":"Open"}
HEADER_OPTS = {"premium":"Premium","standard":"Standard","gondola":"Gondola-Friendly"}
CORR_OPTS   = {"kemi":"Kemi (Coated)","oyster":"Oyster","kraft":"Kraft"}
SHROUD_OPTS = {"premium":"Premium","standard":"Standard","basic":"Basic"}

CORR_COLORS = {"kemi":"#dcdfe6","oyster":"#e8e6e0","kraft":"#d4b892"}
ACCENT, STROKE, SHADOW = "#4E5BA8", "#3b3f46", "rgba(0,0,0,0.10)"

# ---------- UI ----------
st.header("Display & Structure")
left, right = st.columns([0.55, 0.45], gap="large")

with left:
    st.subheader("Display")
    c1, c2 = st.columns(2)
    ui_type = st.selectbox("Type", list(TYPE_OPTS.values()),
                           index=list(TYPE_OPTS).index(ss.display["type"]))
    ui_size = st.selectbox("Size", list(SIZE_OPTS.values()),
                           index=list(SIZE_OPTS).index(ss.display["size"]))
    c3, c4 = st.columns(2)
    ui_cfg = st.selectbox("Configuration", list(CFG_OPTS.values()),
                          index=list(CFG_OPTS).index(ss.display["configuration"]))
    ui_pallet = st.selectbox("Pallet Size", list(PALLET_OPTS.values()),
                             index=list(PALLET_OPTS).index(ss.display["pallet_size"]))

    st.divider()
    st.subheader("Structure")
    c5, c6 = st.columns(2)
    ui_top = st.selectbox("Top of Display", list(TOP_OPTS.values()),
                          index=list(TOP_OPTS).index(ss.structure["top"]))
    ui_header = st.selectbox("Header", list(HEADER_OPTS.values()),
                             index=list(HEADER_OPTS).index(ss.structure["header"]))
    ui_header_depth = None
    if ui_header == "Gondola-Friendly":
        ui_header_depth = st.number_input("Max Header Depth (inches)", 1, 24, int(ss.structure.get("header_depth", 8)))
    c7, c8 = st.columns(2)
    ui_corr = st.selectbox("Corrugate Material", list(CORR_OPTS.values()),
                           index=list(CORR_OPTS).index(ss.structure["corrugate"]))
    ui_shroud = st.selectbox("Shroud", list(SHROUD_OPTS.values()),
                             index=list(SHROUD_OPTS).index(ss.structure["shroud"]))

# Sync to state
rev = lambda d: {v:k for k,v in d.items()}
ss.display.update({
    "type": rev(TYPE_OPTS)[ui_type],
    "size": rev(SIZE_OPTS)[ui_size],
    "configuration": rev(CFG_OPTS)[ui_cfg],
    "pallet_size": rev(PALLET_OPTS)[ui_pallet],
})
ss.structure.update({
    "top": rev(TOP_OPTS)[ui_top],
    "header": rev(HEADER_OPTS)[ui_header],
    "corrugate": rev(CORR_OPTS)[ui_corr],
    "shroud": rev(SHROUD_OPTS)[ui_shroud],
})
ss.structure["header_depth"] = int(ui_header_depth or 8) if ss.structure["header"] == "gondola" else None

# ---------- Renderer ----------
def _size_scale(size_key: str) -> float:
    return {"full": 1.0, "half": 0.8, "quarter": 0.62}[size_key]

def _path(points: List[Tuple[float,float]]) -> str:
    return " ".join([("M" if i==0 else "L")+f"{x:.1f},{y:.1f}" for i,(x,y) in enumerate(points)]) + " Z"

def _poly(points, fill, stroke=STROKE, sw=2.0):
    return f'<path d="{_path(points)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />'

def _line(x1,y1,x2,y2, dash=None, sw=1.2, color=STROKE):
    dashattr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{sw}"{dashattr}/>'
    
def make_svg(display: Dict, structure: Dict) -> Tuple[str,int]:
    s = _size_scale(display["size"])

    # ---- Type presets (distinct silhouettes) ----
    # base front width/height and side depth per type
    if display["type"] == "pallet":
        fw, fh, depth = 210*s, 200*s, 90*s
        body_style = "box"
    elif display["type"] == "pdq":
        fw, fh, depth = 240*s, 90*s, 70*s      # low height, wider tray
        body_style = "tray"
    else:  # sidekick/powerwing
        fw, fh, depth = 140*s, 260*s, 60*s     # tall & narrow
        body_style = "tower"

    # isometric offsets
    dx, dy = depth, -depth*0.45

    # top/header dimensions
    topcap_h = 16*s if structure["top"] == "topcap" else 0
    cutback = structure["top"] == "cutback"
    hdr_heights = {"premium": 60, "standard": 40, "gondola": 28}
    hdr_h = hdr_heights[structure["header"]]*s if structure["header"] else 0

    # dynamic canvas margins to prevent clipping
    M = 48
    w = int(max(520, fw + depth + M*2 + 40))
    h = int(fh + hdr_h + topcap_h + 120)  # extra for shadow
    ox, oy = M + 40, h - 50               # origin near bottom

    corr = CORR_COLORS.get(structure["corrugate"], "#e5e7eb")
    svg = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    svg.append(f'<ellipse cx="{ox+fw*0.7:.1f}" cy="{oy+12:.1f}" rx="{(fw+depth)*0.55:.1f}" ry="12" fill="{SHADOW}"/>')

    # ---- Shroud frame ----
    shroud_pad = {"premium":8, "standard":4, "basic":0}[structure["shroud"]] * s
    if shroud_pad > 0:
        p = shroud_pad
        frame_front = [(ox-p, oy+p), (ox+fw+p, oy+p), (ox+fw+p, oy-fh-p), (ox-p, oy-fh-p)]
        svg.append(_poly(frame_front, "none", ACCENT, 1.6))

    # ---- Base geometry by style ----
    # common faces (we’ll mutate for tray/tower)
    front = [(ox, oy), (ox+fw, oy), (ox+fw, oy-fh), (ox, oy-fh)]
    side  = [(ox+fw, oy), (ox+fw+dx, oy+dy), (ox+fw+dx, oy+dy-fh), (ox+fw, oy-fh)]

    if body_style == "tray":
        # PDQ tray: low back wall = fh, front wall much lower, open top lip
        wall_front = max(20*s, fh*0.28)
        front = [(ox, oy), (ox+fw, oy), (ox+fw, oy-wall_front), (ox, oy-wall_front)]
        side  = [(ox+fw, oy), (ox+fw+dx, oy+dy), (ox+fw+dx, oy+dy-wall_front), (ox+fw, oy-wall_front)]
        # back wall (taller) as inner face for depth
        back_front = [(ox, oy-fh), (ox+fw, oy-fh), (ox+fw, oy-fh-4), (ox, oy-fh-4)]
        svg.append(_poly(back_front, corr, STROKE, 2))
        # tray inner floor
        floor = [(ox, oy), (ox+fw, oy), (ox+fw+dx, oy+dy), (ox+dx, oy+dy)]
        svg.append(_poly(floor, "#f7f7f7", STROKE, 1.6))

    # side then front for correct z-order
    svg.append(_poly(side, corr))
    # cutback applies to front top-right corner (not for tray low front)
    if cutback and body_style != "tray":
        cb = 22*s
        front_cb = [(ox, oy), (ox+fw, oy), (ox+fw, oy-fh+cb), (ox+fw-cb, oy-fh), (ox, oy-fh)]
        svg.append(_poly(front_cb, corr))
    else:
        svg.append(_poly(front, corr))

    # top / cap (skip for tray low front; use a thin lip if topcap)
    if structure["top"] == "open" and body_style != "tray":
        top_face = [(ox, oy-fh), (ox+fw, oy-fh), (ox+fw+dx, oy+dy-fh), (ox+dx, oy+dy-fh)]
        svg.append(_poly(top_face, corr))
    elif structure["top"] == "topcap":
        th = topcap_h if body_style != "tray" else 8*s
        top_face = [(ox, oy-fh), (ox+fw, oy-fh), (ox+fw+dx, oy+dy-fh-th), (ox+dx, oy+dy-fh-th)]
        svg.append(_poly(top_face, "#ffffff"))

    # Pallet deck (only for pallet type)
    if body_style == "box":
        deck_h = 14*s
        deck = [(ox-6*s, oy+deck_h), (ox+fw+6*s, oy+deck_h),
                (ox+fw+dx+6*s, oy+dy+deck_h), (ox+dx-6*s, oy+dy+deck_h)]
        svg.append(_poly(deck, "#e7e5e4", STROKE, 1.4))
        # slats (why: conveys “pallet” quickly)
        slats = 5
        for i in range(slats):
            t = (i+1)/(slats+1)
            x1 = ox + fw*t
            svg.append(_line(x1, oy+deck_h, x1+dx, oy+dy+deck_h, sw=1, color="#b0aba5"))

    # Sidekick mount pad (subtle) to imply powerwing bracket
    if body_style == "tower":
        pad_h = 20*s
        pad = [(ox-10*s, oy), (ox, oy), (ox, oy-pad_h), (ox-10*s, oy-pad_h)]
        svg.append(_poly(pad, "#efefef", STROKE, 1))

    # Header (always above front)
    if structure["header"]:
        hdr_h = hdr_heights[structure["header"]]*s
        hx1, hy1 = ox, oy - fh - hdr_h
        hx2, hy2 = ox + fw, oy - fh
        header_front = [(hx1, hy2), (hx2, hy2), (hx2, hy1), (hx1, hy1)]
        svg.append(_poly(header_front, "#ffffff"))
        header_side = [(hx2, hy2), (hx2+dx, hy2+dy), (hx2+dx, hy2+dy-hdr_h*0.98), (hx2, hy1)]
        svg.append(_poly(header_side, "#f5f7fb"))
        if structure["header"] == "gondola":
            hdr_depth = (structure.get("header_depth") or 10) * (1.8*s)
            gx1 = ox + fw + min(dx, hdr_depth)
            gy1 = oy + dy - fh - (8 if structure["top"]=="topcap" else 0)
            svg.append(_line(ox+fw, oy-fh, gx1, gy1, dash="5,4", sw=2, color=ACCENT))

    # Configuration guides (subtle)
    cfg = display["configuration"]
    if cfg in ("pinwheel","back2back","complex") and body_style != "tray":
        dash = "4,4" if cfg != "complex" else "2,3"
        svg.append(_line(ox+fw*0.5, oy, ox+fw*0.5, oy-fh, dash=dash))
        if cfg in ("pinwheel","complex"):
            svg.append(_line(ox, oy-fh*0.5, ox+fw, oy-fh*0.5, dash=dash))

    svg.append("</svg>")
    return "".join(svg), int(h+20)

svg_markup, html_h = make_svg(ss.display, ss.structure)

with right:
    st.subheader("Preview")
    html(svg_markup, height=html_h)
    t, s = ss.display, ss.structure
    st.caption(f'**Type:** {TYPE_OPTS[t["type"]]} · **Size:** {SIZE_OPTS[t["size"]]} · **Config:** {CFG_OPTS[t["configuration"]]} · **Pallet:** {PALLET_OPTS[t["pallet_size"]]}')
    st.caption(f'**Top:** {TOP_OPTS[s["top"]]} · **Header:** {HEADER_OPTS[s["header"]]}'
               + (f' ({s["header_depth"]}" max depth)' if s["header"]=="gondola" and s.get("header_depth") else "")
               + f' · **Corrugate:** {CORR_OPTS[s["corrugate"]]} · **Shroud:** {SHROUD_OPTS[s["shroud"]]}')

st.divider()
valid = all([ss.display["type"], ss.display["size"], ss.display["configuration"], ss.display["pallet_size"],
             ss.structure["top"], ss.structure["header"], ss.structure["corrugate"], ss.structure["shroud"]]) and \
        (ss.structure["header"]!="gondola" or (ss.structure.get("header_depth") and ss.structure["header_depth"]>0))
cL, cR = st.columns([1,1])
with cL: st.page_link("Home.py", label="Back to Home", icon="🏠")
with cR: st.button("Continue", type="primary", disabled=not valid, help="Wire to next page when ready.")
