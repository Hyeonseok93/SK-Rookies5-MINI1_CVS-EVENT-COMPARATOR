"""Shared product card grid + pagination."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.brand import get_brand_color
from utils.cart import render_cart_button
from utils.html_safe import esc, safe_img_url


def paginate(
    df: pd.DataFrame,
    *,
    page_key: str,
    query_hash: str,
    items_per_page: int = 30,
) -> tuple[pd.DataFrame, int]:
    total_pages = max((len(df) // items_per_page) + (1 if len(df) % items_per_page else 0), 1)
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    hash_key = f"{page_key}_query"
    if hash_key not in st.session_state or st.session_state[hash_key] != query_hash:
        st.session_state[page_key] = 1
        st.session_state[hash_key] = query_hash

    page = st.session_state[page_key]
    start = (page - 1) * items_per_page
    return df.iloc[start : start + items_per_page], total_pages


def product_card_html(row) -> str:
    img_url = safe_img_url(row["img_url"]) if pd.notna(row.get("img_url")) else ""
    name = esc(row.get("name", ""))
    brand = esc(row.get("brand", ""))
    event = esc(row.get("event", ""))
    color = get_brand_color(row.get("brand", ""))
    price = int(row.get("price", 0) or 0)
    unit = int(row.get("unit_price", price) or 0)
    rate = esc(row.get("discount_rate", "0%"))
    return f"""
        <div class="product-card">
            <div class="img-container"><img src="{img_url}"></div>
            <div class="product-name">{name}</div>
            <div style="margin-top: 8px;">
                <span style="font-size: 1.2rem; font-weight: 800; color: #ffffff;">{price:,}원</span>
                <span style="font-size: 0.85rem; color: #ff6b6b; font-weight: bold; margin-left: 5px;">({rate}↓)</span>
            </div>
            <div class="unit-price-text">개당 <b>{unit:,}원</b></div>
            <div style="margin-top: 5px;">
                <span style="color:{color}; background:{color}15; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:0.8rem;">📍 {brand}</span>
                <span class="event-tag" style="margin-left: 5px;">{event}</span>
            </div>
        </div>
    """


def render_product_grid(
    display_df: pd.DataFrame,
    *,
    cart_prefix: str,
    columns: int = 5,
    show_cart: bool = True,
) -> None:
    if display_df.empty:
        st.warning("결과가 없습니다.")
        return
    cols = st.columns(columns)
    for idx, (_, row) in enumerate(display_df.iterrows()):
        with cols[idx % columns]:
            st.markdown(product_card_html(row), unsafe_allow_html=True)
            if show_cart:
                render_cart_button(row, f"{cart_prefix}_{idx}")


def render_pagination(page_key: str, total_pages: int, *, btn_prefix: str = "pg") -> None:
    st.markdown("---")
    _, b1, p_box, b2, _ = st.columns([4, 0.3, 1, 0.3, 4])
    with b1:
        if st.button("❮", key=f"{btn_prefix}_prev") and st.session_state[page_key] > 1:
            st.session_state[page_key] -= 1
            st.rerun()
    with p_box:
        st.markdown(
            f"<div class='page-info-box'>{st.session_state[page_key]} / {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with b2:
        if st.button("❯", key=f"{btn_prefix}_next") and st.session_state[page_key] < total_pages:
            st.session_state[page_key] += 1
            st.rerun()
