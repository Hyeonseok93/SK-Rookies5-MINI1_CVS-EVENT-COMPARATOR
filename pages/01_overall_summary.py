import streamlit as st
from datetime import datetime

from utils.cart import init_cart, render_floating_cart
from utils.data_loader import load_categorized_df
from utils.filters import render_product_filters
from utils.product_grid import paginate, render_pagination, render_product_grid

df = load_categorized_df()

init_cart()
render_floating_cart()

st.title(f"🏪 {datetime.now().strftime('%Y년 %m월')} 편의점 행사 정보 통합 보드")

if df.empty:
    st.info("데이터를 로드하는 중입니다...")
else:
    state = render_product_filters(df, key_prefix="summary")
    filtered_df = state.filtered_df

    query_hash = (
        state.search_query
        + str(state.selected_cats)
        + str(state.selected_events)
        + str(state.selected_brands)
        + state.sort_option
    )
    display_df, total_pages = paginate(
        filtered_df, page_key="current_page", query_hash=query_hash, items_per_page=30
    )
    render_product_grid(display_df, cart_prefix="cart_summary")
    if not display_df.empty:
        render_pagination("current_page", total_pages, btn_prefix="summary")
