import streamlit as st
import pandas as pd

from utils.brand import get_brand_color
from utils.cart import init_cart, render_cart_button, render_floating_cart
from utils.data_loader import load_categorized_df
from utils.filters import SEARCH_MAX_CHARS, name_contains, track_recent_keyword
from utils.html_safe import esc, safe_img_url
from utils.product_grid import paginate, render_pagination

df = load_categorized_df(with_discount_num=True)

init_cart()
render_floating_cart()

st.title("💎 최고의 가성비 아이템 (할인율 TOP 50)")

if df.empty:
    st.error("데이터가 없습니다.")
else:
    with st.expander("🔍 상세 필터 및 검색", expanded=True):
        r1_c1, r1_c2 = st.columns([3, 1])
        with r1_c1:
            search_query = st.text_input(
                "📝 검색",
                "",
                placeholder="상품명 입력",
                key="best_search",
                max_chars=SEARCH_MAX_CHARS,
            )
            track_recent_keyword(search_query)
        with r1_c2:
            sort_option = st.selectbox(
                "💰 정렬",
                ["가성비 순 (할인율)", "가격 낮은 순", "가격 높은 순"],
                key="best_sort",
            )

        r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])
        with r2_c1:
            brand_list = sorted(df['brand'].unique().tolist())
            selected_brands = st.multiselect("🏪 브랜드", brand_list, default=brand_list, key="best_brands")
        with r2_c2:
            event_list = sorted([e for e in df['event'].unique().tolist() if e not in ['SALE', '세일']])
            selected_events = st.multiselect("🎁 행사", event_list, default=event_list, key="best_events")
        with r2_c3:
            cat_list = sorted(df['category'].unique().tolist())
            selected_cats = st.multiselect("📂 분류", cat_list, default=cat_list, key="best_cats")

    filtered_df = df[
        (df['brand'].isin(selected_brands))
        & (df['event'].isin(selected_events))
        & (df['category'].isin(selected_cats))
        & name_contains(df['name'], search_query)
    ].copy()

    if sort_option == "가격 낮은 순":
        best_value_df = filtered_df.sort_values(by='unit_price', ascending=True)
    elif sort_option == "가격 높은 순":
        best_value_df = filtered_df.sort_values(by='unit_price', ascending=False)
    else:
        best_value_df = filtered_df.sort_values(by=['discount_num', 'unit_price'], ascending=[False, True])

    best_value_df = best_value_df.head(50).reset_index(drop=True)

    if best_value_df.empty:
        st.warning("결과가 없습니다.")
    else:
        query_hash = search_query + str(selected_cats) + str(selected_events) + str(selected_brands) + sort_option
        page_items, total_pages = paginate(
            best_value_df, page_key="best_value_page", query_hash=query_hash, items_per_page=9
        )

        st.divider()

        for idx, row in page_items.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([1.5, 4, 2])
                with c1:
                    img_url = safe_img_url(row['img_url']) if pd.notna(row['img_url']) else ""
                    if img_url:
                        st.image(img_url, width=120)
                with c2:
                    st.markdown(f"### {row['name']}")
                    brand_color = get_brand_color(row['brand'])
                    st.markdown(
                        f"<span style='color:{brand_color}; background:{brand_color}15; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:0.8rem;'>📍 {esc(row['brand'])}</span> | {esc(row['category'])} | <span class='event-tag'>{esc(row['event'])}</span>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"<h2 style='color:#ff6b6b; margin-bottom:0;'>{esc(row['discount_rate'])} 할인</h2>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"#### 개당 {int(row['unit_price']):,}원")
                    st.caption(f"정가 {int(row['price']):,}원")
                    render_cart_button(row, f"cart_best_{idx}")
                st.divider()

        render_pagination("best_value_page", total_pages, btn_prefix="best")
