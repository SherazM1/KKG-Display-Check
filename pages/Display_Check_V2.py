"""Direct Streamlit page entry for Display Check v2."""

import streamlit as st

from app.v2.page import render_page


st.set_page_config(
    page_title="Display Check 2.0",
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_page()
