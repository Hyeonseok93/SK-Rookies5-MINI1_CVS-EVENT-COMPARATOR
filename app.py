import streamlit as st
import os
import pandas as pd

from batch.batch_scheduler_manager import get_scheduler_manager
from utils.chatbot import show_chatbot
from utils.cart import init_cart
from utils.paths import categorized_path
from utils.ui_css import inject_app_css

st.set_page_config(page_title="편의점 행사 대시보드", page_icon="🏪", layout="wide")
scheduler = get_scheduler_manager()
scheduler.add_job(
    day=1,
    hour=0,
    minute=30,
    year=None,
    month=None,
    batch_name="정기 월간 데이터 최신화 배치",
    job_id="run_monthly_batch_task",
    dry_run=False
)

# 세션 메모리 초기화
if 'recent_keywords' not in st.session_state:
    st.session_state['recent_keywords'] = []

# 장바구니 세션 초기화
init_cart()

# CSS 로드 (모든 페이지 공통 — 페이지에서 재주입하지 않음)
inject_app_css()

# 데이터 로드 (사이드바 통계용)
@st.cache_data(ttl=3600)
def get_summary_stats():
    file_path = categorized_path()
    if not os.path.exists(file_path):
        return None
    df = pd.read_csv(file_path)
    return {
        "total_count": len(df),
        "brands_count": len(df['brand'].unique())
    }

# 사이드바 공통 영역
def show_sidebar():
    stats = get_summary_stats()
    if stats:
        st.sidebar.markdown("### 📊 실시간 현황")
        st.sidebar.write(f"✅ 총 행사 상품: **{stats['total_count']:,}개**")
        st.sidebar.write(f"🏢 참여 브랜드: **{stats['brands_count']}개**")

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 Convenience Store Dashboard")

# 페이지 정의
home_page = st.Page("pages/00_home.py", title="🏠 메인보드", default=True)
summary_page = st.Page("pages/01_overall_summary.py", title="🔍 전체 요약")
comparison_page = st.Page("pages/02_brand_comparison.py", title="📊 브랜드 비교")
best_value_page = st.Page("pages/03_best_value.py", title="💎 가성비 TOP 50")
budget_page = st.Page("pages/04_budget_combination.py", title="🍱 내 예산 맞춤 꿀조합 생성기")
diet_guide_page = st.Page("pages/05_diet_guide.py", title="🏋️ 다이어트 & 식단 가이드")
night_snack_page = st.Page("pages/06_night_snack_guide.py", title="🌙 야식 & 안주 가이드")
random_picker_page = st.Page("pages/08_random_picker.py", title="🎁 럭키박스")
map_page = st.Page("pages/07_convenience_store_map.py", title="📍 편의점 지도")
jackpot_game_page = st.Page("pages/09_jackpot_game.py", title="🎰 잭팟 게임")
event_news_page = st.Page("pages/10_event_news.py", title="🎉 행사 및 이벤트 소식")

# 내비게이션 구성
pg = st.navigation({
    "대시보드": [home_page],
    "상세 서비스": [summary_page, comparison_page, best_value_page, budget_page, diet_guide_page, night_snack_page, random_picker_page, map_page, jackpot_game_page, event_news_page]
})

# 사이드바 실행
show_sidebar()

# 챗봇 실행
show_chatbot()

# 페이지 실행
pg.run()
