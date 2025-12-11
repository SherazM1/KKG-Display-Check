# pages/Display.py
# Single-variant gallery + live vector render: "48″ Sidekick with Shelves"
from __future__ import annotations
import os
from typing import List, Tuple, Callable, Dict

import streamlit as st
from streamlit.components.v1 import html
from PIL import Image

# ---------- Page setup ----------
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
      .kkg-tile { border:1px solid #e5e7eb; border-radius:12px; padding:10px; }
      .kkg-cap { color:#6b7280; font-size:12px; margin-top:6px; }
      .kkg-label { text-align:center; font-weight:700; font-size:18px; color:#3b3f46; margin-top:12px; }
      .kkg-sub { text-align:center; color:#6b7280; margin-top:2px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Colors / drawing helpers ----------
ACCENT = "#4E5BA8"
STROKE = "#3b3f46"
FILL_FACE = "#E8E6E0"  # oyster-like neutral
FILL_TOP  = "#F5F7FB"
SHADE     = "#f1f3f6"
SHADOW    = "rgba(0,0,0,0.10)"

def _path(points: List[Tuple[float, float]]) -> str:
    return " ".join([("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(points)]) + " Z"

def _poly(points, fill, stroke=STROKE, sw=2.0, extra=""):
    return f'<path d="{_path(points)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'

def _line(x1,y1,x2,y2, dash=None, sw=1.4, color=STROKE):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{sw}"{d}/>'

def _curve_lip(x, y, w, h, bulge=10, stroke=STROKE):
    """Bowed shelf lip (why: matches the book’s curved front)."""
    cx1 = x + w * 0.22; cx2 = x + w * 0.78
    d = (
        f'M{x:.1f},{y:.1f} '
        f'L{x + w:.1f},{y:.1f} '
        f'L{x + w:.1f},{y + h:.1f} '
        f'C{cx2:.1f},{y + h + bulge:.1f} {cx1:.1f},{y + h + bulge:.1f} {x:.1f},{y + h:.1f} Z'
    )
    return f'<path d="{d}" fill="#ffffff" stroke="{stroke}" stroke-width="2"/>'

# ---------- Renderer: 48″ Sidekick with Shelves ----------
def render_sidekick_48_shelves(w: int = 540, h: int = 560) -> str:
    fw, fh = 170, 430            # front width/height (tall & narrow)
    depth = 55
    dx, dy = depth, -depth * 0.45
    ox, oy = 160, 470            # origin at front-bottom-left
    header_h = 44
    shelf_count = 4
    shelf_gap = (fh - 60) / shelf_count
    lip_h = 24
    cavity_h = shelf_gap - lip_h - 10

    front = [(ox, oy), (ox + fw, oy), (ox + fw, oy - fh), (ox, oy - fh)]
    side  = [(ox + fw, oy), (ox + fw + dx, oy + dy), (ox + fw + dx, oy + dy - fh), (ox + fw, oy - fh)]
    top_face = [(ox, oy - fh), (ox + fw, oy - fh), (ox + fw + dx, oy + dy - fh), (ox + dx, oy + dy - fh)]

    svg = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    svg.append(f'<ellipse cx="{ox+fw*0.6:.1f}" cy="{oy+12:.1f}" rx="{(fw+depth)*0.55:.1f}" ry="12" fill="{SHADOW}"/>')

    # Chassis
    svg.append(_poly(side, FILL_FACE))
    svg.append(_poly(front, FILL_FACE))
    svg.append(_poly(top_face, FILL_TOP, sw=1.8))

    # Header
    hx1, hy1 = ox, oy - fh - header_h
    hx2, hy2 = ox + fw, oy - fh
    header_front = [(hx1, hy2), (hx2, hy2), (hx2, hy1), (hx1, hy1)]
    header_side  = [(hx2, hy2), (hx2 + dx, hy2 + dy), (hx2 + dx, hy2 + dy - header_h * 0.98), (hx2, hy1)]
    svg.append(_poly(header_front, "#ffffff"))
    svg.append(_poly(header_side, "#f5f7fb"))

    # Shelves (4): cavity + curved lip + subtle interior line
    x_pad = 12; right_pad = 10
    for i in range(shelf_count):
        y_top = oy - 48 - i * shelf_gap
        cav_x = ox + x_pad
        cav_y = y_top - cavity_h
        cav_w = fw - x_pad - right_pad
        cav_h = cavity_h
        svg.append(_poly(
            [(cav_x, cav_y + cav_h), (cav_x + cav_w, cav_y + cav_h),
             (cav_x + cav_w, cav_y), (cav_x, cav_y)],
            SHADE, sw=1.6
        ))
        lip_x = ox + x_pad - 2
        lip_y = cav_y + cav_h + 2
        lip_w = fw - x_pad - right_pad + 4
        svg.append(_curve_lip(lip_x, lip_y, lip_w, lip_h, bulge=10))
        svg.append(_line(cav_x, cav_y, cav_x + cav_w*0.35, cav_y + cav_h*0.35, sw=1, color="#c7c7c7"))

    # Inner vertical detail
    svg.append(_line(ox + fw*0.32, oy, ox + fw*0.32, oy - fh, sw=1.6, color="#7a7f87"))

    svg.append("</svg>")
    return "".join(svg)

# ---------- Variant registry (add more later) ----------
Variant = Dict[str, object]
VARIANTS: List[Variant] = [
    {
        "key": "sidekick-48-shelves",
        "label": "48″ Sidekick with Shelves",
        "renderer": render_sidekick_48_shelves,
        "ref_path": "assets/references/sidekick-48-shelves.png",  # optional; show if exists
    },
]

# ---------- UI ----------
st.markdown("## Display Library")
st.caption("Select a drawing. Right side shows a clean vector preview; optional reference appears if provided.")

left, right = st.columns([0.58, 0.42], gap="large")

# Ensure selection exists
if "selected_variant_key" not in st.session_state:
    st.session_state.selected_variant_key = VARIANTS[0]["key"]

with left:
    cols = st.columns(3, gap="large")
    for i, v in enumerate(VARIANTS):
        col = cols[i % 3]
        with col:
            st.markdown('<div class="kkg-tile">', unsafe_allow_html=True)
            # If you placed an image at assets/references/{key}.png, show it small under the tile
            ref_path = v.get("ref_path")
            if ref_path and os.path.isfile(ref_path):
                st.image(Image.open(ref_path), use_column_width=True)
            st.caption(v["label"])
            chosen = st.button("Select", key=f"sel_{v['key']}", use_container_width=True)
            if chosen:
                st.session_state.selected_variant_key = v["key"]
            st.markdown('</div>', unsafe_allow_html=True)

with right:
    # Find active variant
    active = next(v for v in VARIANTS if v["key"] == st.session_state.selected_variant_key)
    st.subheader("Preview")
    svg_markup = active["renderer"]()  # type: ignore[arg-type]
    html(svg_markup, height=600)
    st.markdown(f'<div class="kkg-label">{active["label"]}</div>', unsafe_allow_html=True)
    # Optional reference side-by-side below
    if active.get("ref_path") and os.path.isfile(active["ref_path"]):  # type: ignore[index]
        st.image(Image.open(active["ref_path"]), use_column_width=True, caption="Reference (optional)")

st.divider()
st.page_link("Home.py", label="Back to Home", icon="🏠")
