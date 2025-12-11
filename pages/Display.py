# pages/Display.py
# Gallery-first Display page (assumes FOLDERS REVERSED for now):
# - Uses assets/thumbnails/ as raw reference photos (multi-drawing pages OK)
# - assets/references/ reserved for future generated thumbs (not used yet)
# - Preview defaults to the selected reference image for a client-friendly demo

from __future__ import annotations
import os
from datetime import datetime
from typing import Dict, Tuple, List

import streamlit as st
from streamlit.components.v1 import html
from PIL import Image

# ---------- Page config + font ----------
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
      .kkg-meta { color:#6b7280; font-size:13px; }
      .kkg-tile { border:1px solid #e5e7eb; border-radius:12px; padding:8px; }
      .kkg-title { font-weight:700; font-size:18px; margin:0 0 4px 0; }
      .kkg-cap { color:#6b7280; font-size:12px; margin-top:4px; }
      .kkg-btn { width:100%; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- State bootstrap ----------
ss = st.session_state
if "active_spec" not in ss:
    ss.active_spec = True  # allow direct access during build/demo
if "display" not in ss:
    ss.display = {"type":"pallet","size":"full","configuration":"pinwheel","pallet_size":"48"}
if "structure" not in ss:
    ss.structure = {"top":"topcap","header":"standard","header_depth":8,"corrugate":"oyster","shroud":"standard"}
if "selection" not in ss:
    ss.selection = {"variant_key": None, "source_path": None, "label": None}
if "preview_mode" not in ss:
    ss.preview_mode = "Reference Image"  # or "Simple SVG"

# ---------- Constants / options ----------
TYPE_OPTS   = {"pallet":"Pallet", "pdq":"PDQ Tray", "sidekick":"Sidekick / Powerwing"}
SIZE_OPTS   = {"full":"Full", "half":"Half", "quarter":"Quarter"}
CFG_OPTS    = {"complex":"Complex","pinwheel":"Pinwheel","back2back":"Back-to-Back"}
PALLET_OPTS = {"48": '48"', "40": '40"', "equal":"Equal Sides"}

TOP_OPTS    = {"cutback":"Cut Back","topcap":"Top Cap","open":"Open"}
HEADER_OPTS = {"premium":"Premium","standard":"Standard","gondola":"Gondola-Friendly"}
CORR_OPTS   = {"kemi":"Kemi (Coated)","oyster":"Oyster","kraft":"Kraft"}
SHROUD_OPTS = {"premium":"Premium","standard":"Standard","basic":"Basic"}

CORR_COLORS = {"kemi":"#dcdfe6","oyster":"#e8e6e0","kraft":"#d4b892"}
ACCENT, STROKE, SHADOW = "#4E5BA8", "#3b3f46", "rgba(0,0,0,0.10)"

# ---------- Helpers ----------
def find_reference_images(folder: str) -> List[str]:
    exts = (".png", ".jpg", ".jpeg", ".webp")
    if not os.path.isdir(folder):
        return []
    files = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.lower().endswith(exts)]
    return files

def label_from_filename(path: str) -> str:
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    name = name.replace("_", " ").replace("-", " ")
    name = " ".join(name.split())
    return name.title()

def _size_scale(size_key: str) -> float:
    return {"full": 1.0, "half": 0.8, "quarter": 0.62}[size_key]

def _path(points: List[Tuple[float,float]]) -> str:
    return " ".join([("M" if i==0 else "L")+f"{x:.1f},{y:.1f}" for i,(x,y) in enumerate(points)]) + " Z"

def _poly(points, fill, stroke=STROKE, sw=2.0):
    return f'<path d="{_path(points)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />'

def _line(x1,y1,x2,y2, dash=None, sw=1.2, color=STROKE):
    dashattr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{sw}"{dashattr}/>'

def make_simple_svg(display: Dict, structure: Dict) -> Tuple[str,int]:
    """A simple parametric SVG (placeholder until vectors are ready)."""
    s = _size_scale(display["size"])
    # Type presets for silhouette variety
    if display["type"] == "pallet":
        fw, fh, depth = 210*s, 200*s, 90*s
        style = "box"
    elif display["type"] == "pdq":
        fw, fh, depth = 240*s, 90*s, 70*s
        style = "tray"
    else:
        fw, fh, depth = 140*s, 260*s, 60*s
        style = "tower"

    dx, dy = depth, -depth*0.45
    topcap_h = 16*s if structure["top"] == "topcap" else 0
    hdr_h = {"premium":60, "standard":40, "gondola":28}[structure["header"]]*s if structure["header"] else 0

    M = 48
    w = int(max(520, fw + depth + M*2 + 40))
    h = int(fh + hdr_h + topcap_h + 120)
    ox, oy = M + 40, h - 50
    corr = CORR_COLORS.get(structure["corrugate"], "#e5e7eb")

    front = [(ox, oy), (ox+fw, oy), (ox+fw, oy-fh), (ox, oy-fh)]
    side  = [(ox+fw, oy), (ox+fw+dx, oy+dy), (ox+fw+dx, oy+dy-fh), (ox+fw, oy-fh)]

    svg = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    svg.append(f'<ellipse cx="{ox+fw*0.7:.1f}" cy="{oy+12:.1f}" rx="{(fw+depth)*0.55:.1f}" ry="12" fill="{SHADOW}"/>')

    # Shroud frame
    shroud_pad = {"premium":8, "standard":4, "basic":0}[structure["shroud"]] * s
    if shroud_pad > 0:
        p = shroud_pad
        frame_front = [(ox-p, oy+p), (ox+fw+p, oy+p), (ox+fw+p, oy-fh-p), (ox-p, oy-fh-p)]
        svg.append(_poly(frame_front, "none", ACCENT, 1.6))

    # Side + front
    svg.append(_poly(side, corr))
    if structure["top"] == "cutback" and style != "tray":
        cb = 22*s
        front_cb = [(ox, oy), (ox+fw, oy), (ox+fw, oy-fh+cb), (ox+fw-cb, oy-fh), (ox, oy-fh)]
        svg.append(_poly(front_cb, corr))
    else:
        svg.append(_poly(front, corr))

    # Top
    if structure["top"] == "open" and style != "tray":
        top_face = [(ox, oy-fh),(ox+fw, oy-fh),(ox+fw+dx, oy+dy-fh),(ox+dx, oy+dy-fh)]
        svg.append(_poly(top_face, corr))
    elif structure["top"] == "topcap":
        th = topcap_h if style != "tray" else 8*s
        top_face = [(ox, oy-fh),(ox+fw, oy-fh),(ox+fw+dx, oy+dy-fh-th),(ox+dx, oy+dy-fh-th)]
        svg.append(_poly(top_face, "#ffffff"))

    # Pallet deck
    if style == "box":
        deck_h = 14*s
        deck = [(ox-6*s, oy+deck_h), (ox+fw+6*s, oy+deck_h),
                (ox+fw+dx+6*s, oy+dy+deck_h), (ox+dx-6*s, oy+dy+deck_h)]
        svg.append(_poly(deck, "#e7e5e4", STROKE, 1.4))
        for i in range(5):
            t = (i+1)/6
            x1 = ox + fw*t
            svg.append(_line(x1, oy+deck_h, x1+dx, oy+dy+deck_h, sw=1, color="#b0aba5"))

    # Header
    if structure["header"]:
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

    # Config guides
    cfg = display["configuration"]
    if cfg in ("pinwheel","back2back","complex") and style != "tray":
        dash = "4,4" if cfg != "complex" else "2,3"
        svg.append(_line(ox+fw*0.5, oy, ox+fw*0.5, oy-fh, dash=dash))
        if cfg in ("pinwheel","complex"):
            svg.append(_line(ox, oy-fh*0.5, ox+fw, oy-fh*0.5, dash=dash))

    svg.append("</svg>")
    return "".join(svg), int(h+20)

# ---------- UI: Gallery + Controls + Preview ----------
st.markdown("## Display Library")
st.caption("Select a reference drawing from the book, then tweak options if needed. For today’s demo, the preview shows the selected image.")

left, right = st.columns([0.58, 0.42], gap="large")

with left:
    # FOLDERS REVERSED: we treat assets/thumbnails as our raw reference source
    source_folder = "assets/thumbnails"
    imgs = find_reference_images(source_folder)

    if not imgs:
        st.warning("No images found in `assets/thumbnails/`. Drop your book photos there and refresh.")
    else:
        cols = st.columns(3, gap="large")
        for i, path in enumerate(imgs):
            col = cols[i % 3]
            with col:
                try:
                    im = Image.open(path)
                    im.thumbnail((256, 256))
                except Exception:
                    continue
                st.markdown('<div class="kkg-tile">', unsafe_allow_html=True)
                st.image(im, use_column_width=True)
                label = label_from_filename(path)
                st.markdown(f'<div class="kkg-cap">{label}</div>', unsafe_allow_html=True)
                if st.button("Select", key=f"pick_{i}", use_container_width=True):
                    ss.selection = {"variant_key": label.lower().replace(" ", "-"),
                                    "source_path": path,
                                    "label": label}
                st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Fine-tune (optional)")
    c1, c2 = st.columns(2)
    ui_type = c1.selectbox("Type", list(TYPE_OPTS.values()), index=list(TYPE_OPTS).index(ss.display["type"]))
    ui_size = c2.selectbox("Size", list(SIZE_OPTS.values()), index=list(SIZE_OPTS).index(ss.display["size"]))
    c3, c4 = st.columns(2)
    ui_cfg = c3.selectbox("Configuration", list(CFG_OPTS.values()), index=list(CFG_OPTS).index(ss.display["configuration"]))
    ui_pallet = c4.selectbox("Pallet Size", list(PALLET_OPTS.values()), index=list(PALLET_OPTS).index(ss.display["pallet_size"]))
    c5, c6 = st.columns(2)
    ui_top = c5.selectbox("Top of Display", list(TOP_OPTS.values()), index=list(TOP_OPTS).index(ss.structure["top"]))
    ui_header = c6.selectbox("Header", list(HEADER_OPTS.values()), index=list(HEADER_OPTS).index(ss.structure["header"]))
    ui_header_depth = None
    if ui_header == "Gondola-Friendly":
        ui_header_depth = st.number_input("Max Header Depth (inches)", 1, 24, int(ss.structure.get("header_depth", 8)))
    c7, c8 = st.columns(2)
    ui_corr = c7.selectbox("Corrugate", list(CORR_OPTS.values()), index=list(CORR_OPTS).index(ss.structure["corrugate"]))
    ui_shroud = c8.selectbox("Shroud", list(SHROUD_OPTS.values()), index=list(SHROUD_OPTS).index(ss.structure["shroud"]))

# Sync selectors to state
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

with right:
    st.subheader("Preview")
    st.radio("Preview source", ["Reference Image", "Simple SVG"], key="preview_mode", horizontal=True)

    if ss.preview_mode == "Reference Image" and ss.selection.get("source_path"):
        try:
            im = Image.open(ss.selection["source_path"])
            st.image(im, use_column_width=True, caption=ss.selection.get("label") or "Selected reference")
        except Exception as e:
            st.error(f"Could not load selected image: {e}")
    else:
        svg_markup, html_h = make_simple_svg(ss.display, ss.structure)
        html(svg_markup, height=html_h)
        st.caption("This is a simplified SVG. We’ll replace it with polished vectors next.")

    # Quick summary
    t, s = ss.display, ss.structure
    st.markdown(
        f"**Selection:** {ss.selection.get('label') or '—'}  \n"
        f"**Type/Size:** {TYPE_OPTS[t['type']]} • {SIZE_OPTS[t['size']]}  \n"
        f"**Config/Pallet:** {CFG_OPTS[t['configuration']]} • {PALLET_OPTS[t['pallet_size']]}  \n"
        f"**Top/Header:** {TOP_OPTS[s['top']]} • {HEADER_OPTS[s['header']]}"
        + (f" ({s['header_depth']}\")" if s['header']=='gondola' and s.get('header_depth') else "")
        + f"  \n**Corrugate/Shroud:** {CORR_OPTS[s['corrugate']]} • {SHROUD_OPTS[s['shroud']]}"
    )

st.divider()
cL, cR = st.columns([1,1])
with cL:
    st.page_link("Home.py", label="Back to Home", icon="🏠")
with cR:
    ready = ss.selection.get("source_path") is not None
    st.button("Continue", type="primary", disabled=not ready, help="Enable once you pick a drawing.")
