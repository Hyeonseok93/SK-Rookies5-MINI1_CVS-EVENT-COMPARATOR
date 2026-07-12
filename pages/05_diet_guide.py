import streamlit as st
from datetime import datetime

from utils.cart import init_cart, render_cart_button, render_floating_cart
from utils.data_loader import load_categorized_df
from utils.filters import track_recent_keyword
from utils.product_grid import paginate, product_card_html

df = load_categorized_df()

init_cart()


def trigger_scroll():
    st.session_state.do_scroll = True


def execute_scroll():
    st.components.v1.html(
        """
        <script>
        var scrollCount = 0;
        var maxTries = 20;
        function resetScroll() {
            scrollCount++;
            var doc = window.parent.document;
            var allElements = doc.querySelectorAll('*');
            for (var i = 0; i < allElements.length; i++) {
                if (allElements[i].scrollTop > 0) allElements[i].scrollTop = 0;
            }
            window.parent.scrollTo(0, 0);
            doc.documentElement.scrollTop = 0;
            doc.body.scrollTop = 0;
            if (scrollCount < maxTries) setTimeout(resetScroll, 100);
        }
        resetScroll();
        </script>
        """,
        height=0,
    )


render_floating_cart()
st.title(f"🏋️ {datetime.now().strftime('%Y년 %m월')} 다이어트 & 식단 가이드")

if not df.empty:
    with st.expander("🔍 상세 필터 및 테마 선택", expanded=True):
        r1_c1, r1_c2, r1_c3 = st.columns([2, 1, 1])
        with r1_c1:
            search_query = st.text_input("📝 검색", "", placeholder="상품명 입력")
            track_recent_keyword(search_query)
        with r1_c2:
            tags = {
                "🥤 제로 & 저당": ["제로", "zero", "무가당", "슈가프리", "0칼로리"],
                "🍗 고단백 식단": ["단백질", "프로틴", "닭가슴살", "계란", "단백", "닭가슴"],
            }
            selected_tag = st.selectbox("🎯 식단 테마", list(tags.keys()))
            keywords = tags[selected_tag]
        with r1_c3:
            sort_option = st.selectbox("💰 정렬", ["기본", "가격 낮은 순", "가격 높은 순"])

        r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])
        with r2_c1:
            brand_list = sorted(df["brand"].unique().tolist())
            selected_brands = st.multiselect("🏪 브랜드", brand_list, default=brand_list)
        with r2_c2:
            event_list = sorted([e for e in df["event"].unique().tolist() if e not in ["SALE", "세일"]])
            selected_events = st.multiselect("🎁 행사", event_list, default=event_list)
        with r2_c3:
            cat_list = sorted(df["category"].unique().tolist())
            selected_cats = st.multiselect("📂 분류", cat_list, default=cat_list)

    pattern = "|".join(keywords)
    exclude_pattern = "|".join(
        [
            "맥주",
            "라이트비어",
            "피죤",
            "필라이트",
            "카스라이트",
            "주류",
            "스팸",
            "베이컨",
            "부대찌개",
            "햄",
            "가그린",
            "구강",
            "리스테린",
            "순수한면",
            "대형",
            "무알콜",
            "제로백젤리",
        ]
    )

    filtered_df = df[
        (df["name"].str.contains(pattern, case=False, na=False))
        & (~df["name"].str.contains(exclude_pattern, case=False, na=False))
        & (df["brand"].isin(selected_brands))
        & (df["event"].isin(selected_events))
        & (df["category"].isin(selected_cats))
        & (df["name"].str.contains(search_query, case=False))
    ]

    if sort_option == "가격 낮은 순":
        filtered_df = filtered_df.sort_values(by="unit_price")
    elif sort_option == "가격 높은 순":
        filtered_df = filtered_df.sort_values(by="unit_price", ascending=False)
    else:
        filtered_df = filtered_df.sort_values(by="discount_rate", ascending=False)

    query_hash = (
        selected_tag
        + str(selected_brands)
        + str(selected_events)
        + str(selected_cats)
        + search_query
        + sort_option
    )
    display_df, total_pages = paginate(
        filtered_df, page_key="diet_page", query_hash=query_hash, items_per_page=30
    )

    if not display_df.empty:
        st.info(f"✨ **{selected_tag}** 테마 상품 {len(filtered_df)}건 검색")

        if st.session_state.get("do_scroll", False):
            execute_scroll()
            st.session_state.do_scroll = False

        cols = st.columns(5)
        for idx, (_, row) in enumerate(display_df.iterrows()):
            with cols[idx % 5]:
                st.markdown(product_card_html(row), unsafe_allow_html=True)
                render_cart_button(row, f"cart_diet_{idx}")

        st.markdown("---")
        _, b1, p_box, b2, _ = st.columns([4, 0.3, 1, 0.3, 4])

        with b1:
            if st.button("❮", key="d_prev") and st.session_state.diet_page > 1:
                st.session_state.diet_page -= 1
                trigger_scroll()
                st.rerun()

        with p_box:
            st.markdown(
                f"<div class='page-info-box'>{st.session_state.diet_page} / {total_pages}</div>",
                unsafe_allow_html=True,
            )

        with b2:
            if st.button("❯", key="d_next") and st.session_state.diet_page < total_pages:
                st.session_state.diet_page += 1
                trigger_scroll()
                st.rerun()

    else:
        st.warning("결과가 없습니다.")
else:
    st.info("데이터 로딩 중...")
