from datetime import datetime

from utils.cart import init_cart, render_floating_cart
from utils.data_loader import load_categorized_df
from utils.theme_guide import ThemeGuideConfig, render_theme_guide

df = load_categorized_df(with_discount_num=True)

init_cart()
render_floating_cart()

DIET_THEMES = {
    "🥤 제로 & 저당": ["제로", "zero", "무가당", "슈가프리", "0칼로리"],
    "🍗 고단백 식단": ["단백질", "프로틴", "닭가슴살", "계란", "단백", "닭가슴"],
}

DIET_EXCLUDE = [
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

render_theme_guide(
    df,
    ThemeGuideConfig(
        title=f"🏋️ {datetime.now().strftime('%Y년 %m월')} 다이어트 & 식단 가이드",
        themes=DIET_THEMES,
        exclude_keywords=DIET_EXCLUDE,
        page_key="diet_page",
        cart_prefix="cart_diet",
        btn_prefix="d",
        expander_title="🔍 상세 필터 및 테마 선택",
        theme_label="🎯 식단 테마",
    ),
)
