"""Inject shared app CSS once from app.py (or callers)."""
from __future__ import annotations

import streamlit as st

from utils.paths import style_css_path


def inject_app_css() -> None:
    path = style_css_path()
    try:
        with open(path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except OSError:
        pass
