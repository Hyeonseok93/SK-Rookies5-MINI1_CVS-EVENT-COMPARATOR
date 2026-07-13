import streamlit as st
import pandas as pd
import time

from utils.brand import get_brand_color
from utils.cart import init_cart, add_to_cart, is_in_cart, remove_from_cart, render_floating_cart
from utils.data_loader import load_categorized_df
from utils.html_safe import esc, safe_img_url

df = load_categorized_df(with_unit_price=True)

init_cart()
render_floating_cart()

st.title("🎁 럭키박스")
st.markdown("##### 오늘의 운명적 득템은? 럭키박스를 열어 당신을 기다리는 행운의 상품을 확인하세요!")

if not df.empty:
    with st.expander("🛠️ 럭키픽 필터 설정", expanded=True):
        col1, col2 = st.columns([1, 2])

        with col1:
            if "category" in df.columns:
                categories = ["전체"] + sorted(df["category"].dropna().unique().tolist())
            else:
                categories = ["전체"]
            selected_cat = st.selectbox("📂 카테고리 선택", categories)

        with col2:
            if "brand" in df.columns:
                brands = sorted(df["brand"].dropna().unique().tolist())
            else:
                brands = []
            selected_brand = st.multiselect("🏪 브랜드 선택 (미선택 시 전체)", brands, default=brands)

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])

    with col_c:
        pick_button = st.button("🎁 럭키박스 열기!", use_container_width=True, type="primary")

    st.markdown("---")

    if pick_button:
        filtered_df = df[df["brand"].isin(selected_brand)] if selected_brand else df
        if selected_cat != "전체":
            filtered_df = filtered_df[filtered_df["category"] == selected_cat]

        if not filtered_df.empty:
            with st.spinner("🎲 행운의 상품을 고르는 중..."):
                time.sleep(1)
                picked = filtered_df.sample(n=1).iloc[0]
                st.session_state.lucky_picked = picked.to_dict()
                st.balloons()
        else:
            st.session_state.lucky_picked = None
            with col_c:
                st.warning("선택하신 조건에 맞는 상품이 없습니다. 필터를 조정해 보세요!")

    picked_item = st.session_state.get("lucky_picked")

    if picked_item:
        with col_c:
            st.success(f"🎉 오늘의 추천 상품은 **{picked_item['name']}** 입니다!")

            img_url = (
                safe_img_url(
                    picked_item["img_url"],
                    fallback="https://via.placeholder.com/250?text=No+Image",
                )
                if pd.notna(picked_item.get("img_url"))
                else "https://via.placeholder.com/250?text=No+Image"
            )
            name = esc(picked_item.get("name", ""))
            event = esc(picked_item.get("event", ""))
            brand = esc(picked_item.get("brand", ""))
            category = esc(picked_item.get("category", ""))
            brand_color = get_brand_color(picked_item.get("brand", ""))
            price = int(picked_item.get("price", 0) or 0)

            st.markdown(
                f"""
                <div style="background-color: #161b22; border: 2px solid #58a6ff; border-radius: 20px; padding: 30px; text-align: center;">
                    <div style="background: white; padding: 10px; border-radius: 15px; display: inline-block; margin-bottom: 20px;">
                        <img src="{img_url}" style="max-width: 250px; max-height: 250px; object-fit: contain;">
                    </div>
                    <h2 style="color: white; margin-bottom: 10px;">{name}</h2>
                    <div style="font-size: 1.5rem; color: #ff6b6b; font-weight: bold; margin-bottom: 10px;">
                        {event} | {price:,}원
                    </div>
                    <div style="margin-bottom: 10px;">
                        <span style="color:{brand_color}; background:{brand_color}15; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:1.1rem;">📍 {brand}</span>
                        <span style="color: #8b949e; font-size: 1.1rem; margin-left: 5px;">({category})</span>
                    </div>
                    <hr style="border-color: #30363d; margin: 20px 0;">
                    <p style="color: #58a6ff; font-weight: bold; font-size: 1.1rem;">지금 바로 집 앞 {brand}(으)로 달려가세요! 🏃‍♂️</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

            cart_key = (picked_item["name"], picked_item["brand"], picked_item["event"])
            in_cart = is_in_cart(picked_item["name"], picked_item["brand"], picked_item["event"])
            unit_price = int(picked_item.get("unit_price", picked_item["price"]))

            st.markdown("<br>", unsafe_allow_html=True)
            if in_cart:
                if st.button("✅ 장바구니에 담김 (취소)", use_container_width=True, key="lucky_cart_btn"):
                    remove_from_cart(cart_key)
                    st.rerun()
            else:
                if st.button("🛒 장바구니에 담기", use_container_width=True, key="lucky_cart_btn", type="primary"):
                    add_to_cart(
                        name=picked_item["name"],
                        brand=picked_item["brand"],
                        event=picked_item["event"],
                        price=int(picked_item["price"]),
                        unit_price=unit_price,
                    )
                    st.rerun()

    elif "lucky_picked" not in st.session_state:
        with col_c:
            st.markdown(
                """
                <div style="height: 300px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px dashed #30363d; border-radius: 20px; color: #8b949e;">
                    <div style="font-size: 4rem; margin-bottom: 10px;">🎁</div>
                    <h3>어떤 상품이 나올까요?</h3>
                    <p>위의 버튼을 눌러 럭키박스를 열어보세요!</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

else:
    st.error("데이터를 불러올 수 없습니다. data/categorized_data.csv 파일을 확인해주세요.")
