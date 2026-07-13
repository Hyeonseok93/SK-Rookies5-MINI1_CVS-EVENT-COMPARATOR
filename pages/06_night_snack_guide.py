from datetime import datetime

from utils.cart import init_cart, render_floating_cart
from utils.data_loader import load_categorized_df
from utils.theme_guide import ThemeGuideConfig, render_theme_guide

df = load_categorized_df(with_discount_num=True)

init_cart()
render_floating_cart()

SNACK_THEMES = {
    "🍺 맥주와 찰떡궁합": [
        "치킨",
        "너겟",
        "소시지",
        "핫바",
        "만두",
        "피자",
        "감자",
        "나쵸",
        "과자",
        "팝콘",
        "땅콩",
        "아몬드",
        "어포",
    ],
    "🔥 소주 & 매콤안주": [
        "닭발",
        "곱창",
        "막창",
        "족발",
        "편육",
        "육포",
        "오징어",
        "황태",
        "어묵탕",
        "부대찌개",
        "매콤",
        "불닭",
    ],
    "🍜 든든한 야식": [
        "떡볶이",
        "라면",
        "컵라면",
        "짜장",
        "짬뽕",
        "우동",
        "도시락",
        "김밥",
        "삼각김밥",
        "햄버거",
    ],
}

SNACK_EXCLUDE = [
    "피죤",
    "가그린",
    "칫솔",
    "치약",
    "샴푸",
    "린스",
    "면도기",
    "생리대",
    "마스크",
    "세제",
    "멀티비타민",
]

render_theme_guide(
    df,
    ThemeGuideConfig(
        title=f"🌙 {datetime.now().strftime('%Y년 %m월')} 야식 & 안주 가이드",
        subtitle="##### 오늘 밤, 당신의 소중한 혼술과 야식을 책임질 최고의 행사 상품 큐레이션!",
        themes=SNACK_THEMES,
        exclude_keywords=SNACK_EXCLUDE,
        page_key="snack_page",
        cart_prefix="cart_snack",
        btn_prefix="snack",
        expander_title="🔍 야식 테마 및 상세 필터",
        theme_label="🎯 야식 테마 선택",
        search_label="📝 상품 검색",
        search_placeholder="예: 닭발, 감자칩, 소시지",
        sort_label="💰 정렬 방식",
        sort_options=("할인율 순", "가격 낮은 순", "가격 높은 순"),
        brand_label="🏪 편의점",
        event_label="🎁 행사 유형",
        cat_label="📂 상품 카테고리",
        result_kind="success",
        empty_message="아쉽게도 해당 테마에 맞는 행사 상품이 현재 없습니다. 다른 테마나 필터를 선택해보세요!",
        footer="※ 상품 정보는 각 편의점 공식 홈페이지의 행사 정보를 바탕으로 제공됩니다.",
    ),
)
