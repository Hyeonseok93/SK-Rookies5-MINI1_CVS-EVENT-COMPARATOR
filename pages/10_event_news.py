import streamlit as st
import math
from datetime import datetime, timedelta

from utils.html_safe import esc, safe_url
from utils.news_scraper import fetch_realtime_cvs_news

st.markdown("## 🎉 편의점 행사 및 이벤트 소식")
st.caption("편의점 4사의 최신 공식 이벤트를 한눈에 확인하세요!")

df = fetch_realtime_cvs_news()

if df.empty or "brand" not in df.columns:
    st.warning("수집된 행사 소식이 없습니다. 배치/뉴스 스크래퍼 실행 후 다시 확인해주세요.")
    st.stop()

brands = ["전체", "GS25", "CU", "세븐일레븐", "이마트24"]
selected_brand = st.selectbox("🏢 브랜드 필터", brands)

if selected_brand != "전체":
    df = df[df['brand'] == selected_brand].reset_index(drop=True)

ITEMS_PER_PAGE = 20
total_items = len(df)
total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1

if 'event_page' not in st.session_state:
    st.session_state['event_page'] = 1

if st.session_state['event_page'] > total_pages:
    st.session_state['event_page'] = total_pages
if st.session_state['event_page'] < 1:
    st.session_state['event_page'] = 1

# 이전/다음이 화면 양끝으로 벌어지지 않게 가운데로 모음 (전체 요약 페이지네이션과 동일 패턴)
_, c_prev, c_info, c_next, _ = st.columns([3, 1, 2, 1, 3])
with c_prev:
    if st.button("⬅️ 이전", disabled=(st.session_state["event_page"] <= 1), use_container_width=True):
        st.session_state["event_page"] -= 1
        st.rerun()

with c_info:
    st.markdown(
        f"<div style='text-align:center; padding-top:0.35rem;'><b>{st.session_state['event_page']} / {total_pages}</b><br/><span style='color:#888; font-size:0.85rem;'>총 {total_items}건</span></div>",
        unsafe_allow_html=True,
    )

with c_next:
    if st.button("다음 ➡️", disabled=(st.session_state["event_page"] >= total_pages), use_container_width=True):
        st.session_state["event_page"] += 1
        st.rerun()

st.markdown("---")

start_idx = (st.session_state['event_page'] - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
display_df = df.iloc[start_idx:end_idx]

now = datetime.now()

if display_df.empty:
    st.warning("수집된 행사 소식이 없습니다.")
else:
    for _, row in display_df.iterrows():
        is_new = (now - row['pub_date']) < timedelta(hours=24)
        badge = "<span style='color:#ff4b4b; font-weight:bold;'>🔥 [NEW]</span>" if is_new else ""
        date_str = row['pub_date'].strftime("%Y-%m-%d")
        brand = esc(row['brand'])
        title = esc(row['title'])
        link = safe_url(row['link'])

        st.markdown(f"""
        <div style="padding: 15px; border-bottom: 1px solid #444; display: flex; flex-direction: column;">
            <div style="font-size: 13px; color: #bbb; margin-bottom: 5px;">
                <span style="background-color: #58a6ff; color: white; padding: 2px 8px; border-radius: 10px; margin-right: 5px;">{brand}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <a href="{link}" target="_blank" rel="noopener noreferrer" style="font-size: 17px; font-weight: bold; text-decoration: none; color: #ffffff;">
                    {badge} {title}
                </a>
                <span style="font-size: 14px; color: #888;">{date_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
