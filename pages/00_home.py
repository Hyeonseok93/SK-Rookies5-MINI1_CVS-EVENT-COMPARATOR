import streamlit as st
import os
import pandas as pd
import base64
from datetime import datetime, timedelta
import pytz
import streamlit.components.v1 as components

from utils.brand import get_brand_color
from utils.cart import init_cart, render_floating_cart
from utils.data_loader import load_categorized_df
from utils.html_safe import esc, esc_attr, safe_img_url, safe_url
from utils.news_scraper import fetch_realtime_cvs_news
from utils.paths import PROJECT_ROOT
from utils.filters import name_contains

KST = pytz.timezone("Asia/Seoul")
now_hour = datetime.now(KST).hour

init_cart()
render_floating_cart()


def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


@st.cache_data
def get_fixed_hot_deals(recent_keywords):
    try:
        df_main = load_categorized_df(with_unit_price=True)
        if df_main.empty:
            return pd.DataFrame()
        df_main = df_main[df_main["event"].astype(str).str.contains(r"\+", na=False, regex=True)]

        display_df = pd.DataFrame()

        if recent_keywords:
            rec_list = []
            for kwd in recent_keywords:
                matched = df_main[name_contains(df_main["name"].astype(str), kwd)]
                rec_list.append(matched)
            if rec_list:
                display_df = pd.concat(rec_list).drop_duplicates(subset=["name", "brand", "event"])

        if len(display_df) < 10 and not df_main.empty:
            shortfall = 10 - len(display_df)
            remaining_df = df_main.drop(display_df.index, errors="ignore")
            if not remaining_df.empty:
                fill_df = remaining_df.sample(n=min(shortfall, len(remaining_df)))
                display_df = pd.concat([display_df, fill_df])

        return display_df.head(10)
    except Exception:
        return pd.DataFrame()


st.markdown(
    f"""
    <div class="hero-section">
        <div class="hero-title">🚀 편의점 득템 가이드</div>
        <div class="hero-subtitle">
            스마트한 소비를 위한 실시간 행사 압축 가이드!<br>
            CU, GS25, 7-Eleven, Emart24의 모든 혜택을 한눈에 비교하세요.
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

try:
    current_keywords = st.session_state.get("recent_keywords", [])
    display_df = get_fixed_hot_deals(tuple(current_keywords) if current_keywords else ())

    if current_keywords:
        st.markdown("### 🎁 취향 저격 맞춤 추천")
    else:
        st.markdown("### 🎲 오늘의 핫딜 추천")

    if not display_df.empty:
        scroll_html = """<style>
    .horizontal-scroll-wrapper {
        display: flex;
        overflow: hidden;
        gap: 20px;
        padding: 15px 5px 25px 5px;
        scroll-behavior: smooth;
    }
    .horizontal-scroll-wrapper::-webkit-scrollbar {
        height: 8px;
    }
    .horizontal-scroll-wrapper::-webkit-scrollbar-thumb {
        background-color: #d1d5db;
        border-radius: 10px;
    }
    .scroll-item {
        flex: 0 0 calc(20% - 16px);
        border: 1px solid #eef0f2;
        border-radius: 16px;
        padding: 15px;
        background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        text-align: left;
        transition: transform 0.2s;
        box-sizing: border-box;
    }
    .scroll-item:hover {
        transform: translateY(-5px);
    }
    .item-name {
        font-size: 16px;
        font-weight: bold;
        color: #1a1a1a;
        margin: 8px 0;
        height: 42px;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        word-break: break-all;
    }
    </style>
    <div class="horizontal-scroll-wrapper" id="hotdeal-scroll">
    """

        for idx, row in display_df.iterrows():
            raw_img = row["img_url"] if pd.notna(row["img_url"]) else "https://via.placeholder.com/150?text=No+Image"
            img_url = safe_img_url(raw_img, fallback="https://via.placeholder.com/150?text=No+Image")
            price = int(str(row["price"]).replace(",", "")) if pd.notna(row["price"]) else 0
            unit_price = int(row.get("unit_price", price) or price)
            brand_color = get_brand_color(row["brand"])
            brand = esc(row["brand"])
            event = esc(row["event"])
            name = esc(row["name"])

            scroll_html += f"""
        <div class="scroll-item">
            <img src="{img_url}" style="width:100%; height:130px; object-fit:contain; border-radius:8px; margin-bottom:12px;">
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 5px;">
                <span style="font-size:0.8rem; color:{brand_color}; background:{brand_color}15; padding:2px 6px; border-radius:4px; font-weight:bold;">{brand}</span>
                <span style="font-size:11px; color:#ff4b4b; background:#fff0f0; padding:2px 6px; border-radius:4px; font-weight:bold;">{event}</span>
            </div>
            <div class="item-name">{name}</div>
            <div style="font-size:18px; color:#1a1a1a; font-weight:900;">{price:,}원</div>
            <div style="font-size:13px; color:#3182f6; font-weight:bold; margin-top:4px;">✨ 개당 {unit_price:,}원</div>
        </div>"""

        scroll_html += """
    </div>

    <script>
    const container = document.getElementById("hotdeal-scroll");
    const items = container.querySelectorAll(".scroll-item");

    items.forEach((el, i) => {
        if (i >= 10) el.style.display = "none";
    });

    let currentIndex = 0;
    const visibleCount = 5;

    function slide() {
        const itemWidth = items[0].offsetWidth + 20;
        currentIndex += visibleCount;

        if (currentIndex >= 10) currentIndex = 0;

        container.scrollTo({
            left: itemWidth * currentIndex,
            behavior: "smooth"
        });
    }

    setInterval(slide, 4000);
    </script>
    """

        components.html(scroll_html, height=350, scrolling=False)
except Exception:
    pass

st.markdown("<br>", unsafe_allow_html=True)

df_time = load_categorized_df(with_unit_price=True)

if not df_time.empty:
    if 6 <= now_hour < 11:
        target_cat, title, icon = ["식사류"], "🌅 바쁜 아침, 든든한 한 끼!", "🥛"
    elif 11 <= now_hour < 14:
        target_cat, title, icon = ["식사류"], "🍱 오늘 점심 뭐 먹지?", "🥢"
    elif 14 <= now_hour < 18:
        target_cat, title, icon = ["간식류", "음료"], "☕ 나른한 오후, 당 충전 시간", "🍪"
    elif 18 <= now_hour < 21:
        target_cat, title, icon = ["식사류"], "🍺 하루를 마무리하는 저녁", "🍗"
    else:
        target_cat, title, icon = ["간식류", "식사류"], "🌙 출출한 밤, 야식의 유혹", "🍜"

    display_cats = " ".join([f"#{c}" for c in target_cat])
    st.markdown(f"### {icon} {title}")

    col_tag, col_btn = st.columns([4, 1])
    with col_tag:
        st.markdown(f"현재 시간대에 딱 맞는 **{display_cats}** 상품들입니다.")
    with col_btn:
        st.button("🔄 다른 상품 보기", use_container_width=True, key="refresh_time_items")

    recommend_df = df_time[df_time["category"].isin(target_cat)].copy()
    if not recommend_df.empty:
        exclude_keywords = ["쏘피", "좋은", "섬유유연제", "티셔츠", "순수한면", "면도날", "라엘", "순면", "비비안"]
        filter_condition = recommend_df["name"].str.contains("|".join(exclude_keywords), na=False)
        recommend_df = recommend_df[~filter_condition]
        recommend_df = recommend_df[recommend_df["event"] != "세일"]

        display_items = recommend_df.sample(n=min(len(recommend_df), 5))
        cols = st.columns(5)
        for i, (_, row) in enumerate(display_items.iterrows()):
            with cols[i]:
                img_url = safe_img_url(row["img_url"]) if pd.notna(row["img_url"]) else ""
                name = esc(row["name"])
                event = esc(row["event"])
                brand = esc(row["brand"])
                brand_color = get_brand_color(row["brand"])
                price = int(row["price"])
                st.markdown(
                    f"""
                    <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; text-align: center; height: 100%;">
                        <div style="height: 100px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                            <img src="{img_url}" style="max-width: 100%; max-height: 100px; object-fit: contain;">
                        </div>
                        <div style="font-size: 0.85rem; font-weight: bold; color: white; margin-bottom: 5px; height: 40px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.2;">
                            {name}
                        </div>
                        <div style="color: #58a6ff; font-weight: bold; font-size: 1.1rem;">{price:,}원</div>
                        <div style="font-size: 0.8rem; color: #ff6b6b; font-weight: bold;">{event}</div>
                        <div style="margin-top: 5px;">
                            <span style="color:{brand_color}; background:{brand_color}15; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:0.8rem;">📍 {brand}</span>
                        </div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
    else:
        st.info(f"현재 {target_cat} 카테고리에 해당하는 행사 상품이 없습니다.")

st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("### 🚀 빠른 메뉴")

MENU_CARDS = [
    ("pages/01_overall_summary.py", "🔍", "전체 요약", "이미지 기반의 카드 리스트로 모든 행사 상품을 검색하고 필터링하세요."),
    ("pages/02_brand_comparison.py", "📊", "브랜드별 비교", "어느 편의점이 가장 혜택이 좋을까요? 차트와 통계로 브랜드별 전략을 비교합니다."),
    ("pages/03_best_value.py", "💎", "가성비 비교", "할인율이 가장 높은 TOP 50 상품만 모았습니다. 지갑을 지키는 가장 쉬운 방법!"),
    ("pages/04_budget_combination.py", "🍱", "내 예산 맞춤 꿀조합 생성기", "내 예산 안에서 가장 많이 절약할 수 있는 상품들의 조합을 추천해드려요."),
    ("pages/05_diet_guide.py", "🏋️", "다이어트 가이드", "제로 슈거, 고단백 상품들만 쏙쏙 골라 건강한 편의점 식단을 제안합니다."),
    ("pages/06_night_snack_guide.py", "🌙", "야식 & 안주 가이드", "오늘 밤 혼술 안주와 야식을 고민하시나요? 딱 맞는 행사 안주를 찾아보세요."),
    ("pages/08_random_picker.py", "🎁", "럭키박스", "메뉴 결정이 힘드신가요? 랜덤 럭키박스로 오늘 행운의 상품을 뽑아보세요!"),
    ("pages/07_convenience_store_map.py", "📍", "편의점 지도", "내 주변의 편의점은 어디에 있을까요? 브랜드별 위치를 지도에서 확인하세요."),
    ("pages/09_jackpot_game.py", "🎰", "잭팟 게임!", "똑같은 상품 3개를 맞추면 오늘 운세 대박! 행운의 메뉴를 잭팟으로 확인하세요."),
]

for row_start in range(0, len(MENU_CARDS), 3):
    cols = st.columns(3)
    for col, (page, icon, title, desc) in zip(cols, MENU_CARDS[row_start : row_start + 3]):
        with col:
            st.markdown(
                f"""
                <div class="dashboard-card">
                    <div class="card-icon">{icon}</div>
                    <div class="card-title">{title}</div>
                    <div class="card-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.page_link(page, label=f"{title} 이동하기 →", use_container_width=True)

st.markdown("---")
r1, r2 = st.columns([4, 1])
with r1:
    st.markdown("### 🎉 행사 및 이벤트 소식")
with r2:
    st.write("")
    st.page_link("pages/10_event_news.py", label="더보기 +", icon="📰")

try:
    news_df = fetch_realtime_cvs_news()
    top_news = news_df.head(5)
    now = datetime.now()

    for _, row in top_news.iterrows():
        is_new = (now - row["pub_date"]) < timedelta(hours=24)
        badge = "🔥" if is_new else "👉"
        brand = esc(row["brand"])
        title = esc(row["title"])
        link = safe_url(row["link"])
        if link == "#":
            st.markdown(f"- {badge} **[{brand}]** {title}", unsafe_allow_html=True)
        else:
            st.markdown(f"- {badge} **[{brand}]** [{title}]({link})", unsafe_allow_html=True)
except Exception:
    st.caption("현재 행사 소식을 불러올 수 없습니다.")

st.markdown("---")
st.markdown("### 🏢 함께하는 브랜드")
l1, l2, l3, l4 = st.columns(4)

logos = {
    "CU": os.path.join(PROJECT_ROOT, "assets", "logo_cu.png"),
    "GS25": os.path.join(PROJECT_ROOT, "assets", "logo_gs25.png"),
    "7Eleven": os.path.join(PROJECT_ROOT, "assets", "logo_7eleven.png"),
    "emart24": os.path.join(PROJECT_ROOT, "assets", "logo_emart24.png"),
}

for col, (name, path) in zip([l1, l2, l3, l4], logos.items()):
    with col:
        b64_img = get_base64_image(path)
        if b64_img:
            st.markdown(
                f"""
                <div class="brand-logo-card">
                    <img src="data:image/png;base64,{b64_img}">
                </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.button(name, use_container_width=True)

st.markdown("---")
st.caption("© 2026 Convenience Store Event Dashboard. Data updated daily.")
