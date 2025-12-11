# Home.py
# Streamlit landing page with Raleway font + KKG logo (assets/KKG-Logo-02.png)

import streamlit as st
from datetime import datetime

st.set_page_config(page_title="KKG Display Check", layout="wide")

# --- Raleway + basic CSS (kept inline for simplicity) ---
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      :root { --kkg-primary: #4E5BA8; }
      html, body, [class*="css"]  { font-family: 'Raleway', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; }
      /* Centered hero */
      .kkg-hero { display:flex; flex-direction:column; align-items:center; gap:12px; margin-top:12px; margin-bottom:24px; }
      .kkg-title { font-weight:700; font-size:32px; letter-spacing:0.3px; margin:0; }
      .kkg-sub { color:#5f6368; margin:0; font-size:16px; }
      /* CTA buttons */
      .kkg-ctas { display:flex; gap:12px; justify-content:center; margin:18px 0 8px; }
      /* Hide Streamlit chrome */
      header[data-testid="stHeader"] { background: transparent; }
      footer { visibility: hidden; }
      #MainMenu { visibility: hidden; }
      /* Cards */
      .kkg-card { border:1px solid #e6e8eb; border-radius:14px; padding:16px 18px; }
      .kkg-meta { color:#6b7280; font-size:13px; margin-top:2px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Hero with logo ---
with st.container():
    st.markdown('<div class="kkg-hero">', unsafe_allow_html=True)
    st.image("assets/KKG-Logo-02.png", width=160)  # ensure this file is in your repo
    st.markdown('<h1 class="kkg-title">Display Check Builder</h1>', unsafe_allow_html=True)
    st.markdown('<p class="kkg-sub">Assemble a client-ready spec in minutes.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Primary CTAs ---
colA, colB, colC = st.columns([1,1,1], gap="large")
with colB:
    start = st.button("Start New Spec", type="primary", use_container_width=True)
   

# Placeholder interactions (wire to pages later)
if start:
    # Minimal session defaults (extend later)
    st.session_state["draft_id"] = datetime.utcnow().strftime("DRAFT-%Y%m%d-%H%M%S")
    st.session_state.setdefault("project", {})
    st.success("New spec started. (Navigation to the next page will be wired up next.)")


# --- Recent Projects (placeholder card) ---
st.markdown("### Recent Projects")
st.markdown(
    """
    <div class="kkg-card">
      <div class="kkg-meta">No recent projects yet. Your latest items will appear here after you save a draft.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Footer blurb ---
st.markdown(
    "<div class='kkg-meta' style='text-align:center;margin-top:18px;'>"
    "v0.1 — Kendal King Group"
    "</div>",
    unsafe_allow_html=True,
)
