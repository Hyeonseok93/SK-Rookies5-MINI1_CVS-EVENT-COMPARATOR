"""브랜드별 행사 전략 심층 비교 — 세로 스크롤 + 간결 호버."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.brand import BRAND_COLORS
from utils.cart import init_cart, render_floating_cart
from utils.data_loader import load_categorized_df
from utils.filters import name_contains, render_product_filters

DUMP_EVENTS = ("1+1", "2+1", "3+1")

TREND_KEYWORDS = {
    "제로/슈가프리": ["제로", "zero", "무설탕", "저당", "슈가프리"],
    "단백질/헬스": ["단백질", "프로틴", "protein", "닭가슴살"],
    "매운맛/마라": ["매운", "핫", "hot", "마라", "불닭"],
    "과일/상큼": ["딸기", "사과", "포도", "망고", "레몬"],
}


def _count_keyword_hits(series: pd.Series, words: list[str]) -> int:
    mask = pd.Series(False, index=series.index)
    for w in words:
        mask |= name_contains(series, w)
    return int(mask.sum())


def _brand_order(f_df: pd.DataFrame, selected_brands: list, sort_option: str) -> list:
    if f_df.empty:
        return list(selected_brands)
    if sort_option == "상품 많은 순":
        return f_df["brand"].value_counts().index.tolist()
    if sort_option == "가격 낮은 순":
        return f_df.groupby("brand")["unit_price"].mean().sort_values().index.tolist()
    if sort_option == "할인율 높은 순":
        return (
            f_df.groupby("brand")["discount_num"]
            .mean()
            .sort_values(ascending=False)
            .index.tolist()
        )
    return sorted(selected_brands)


def _slim_hover(fig, template: str, **layout_kw) -> None:
    """필요한 필드만 호버에 표시."""
    fig.update_traces(hovertemplate=template, hoverlabel=dict(namelength=-1))
    fig.update_layout(hovermode="closest", **layout_kw)


df = load_categorized_df(with_unit_price=True, with_discount_num=True)
init_cart()
render_floating_cart()

st.title("📊 브랜드별 행사 전략 심층 비교")
st.markdown("단순 세일 제외 후 **순수 덤 증정(1+1, 2+1, 3+1)** 상품 전략을 비교합니다.")

if df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

df = df[df["event"].isin(DUMP_EVENTS)].copy()
if df.empty:
    st.warning("1+1 / 2+1 / 3+1 행사 상품이 없습니다.")
    st.stop()

brand_colors = BRAND_COLORS
state = render_product_filters(
    df,
    expander_title="🔍 상세 필터 및 검색",
    sort_options=["기본", "상품 많은 순", "가격 낮은 순", "할인율 높은 순"],
    exclude_events=[],
    key_prefix="brand_cmp",
)
f_df = state.filtered_df
selected_brands = state.selected_brands
sort_option = state.sort_option
brand_order = _brand_order(f_df, selected_brands, sort_option)

if f_df.empty:
    st.warning("선택한 조건에 맞는 상품이 없습니다. 필터를 조정해 주세요.")
    st.stop()

# --- KPI ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("행사 상품 수", f"{len(f_df):,}개")
m2.metric("평균 할인 효과", f"{f_df['discount_num'].mean():.1f}%")
m3.metric("평균 실질구매가", f"{int(f_df['unit_price'].mean()):,}원")
top_cat = f_df["category"].mode()
m4.metric("최다 행사 품목", f"{top_cat.iloc[0]}" if not top_cat.empty else "-")

# ========== 1. Brand DNA ==========
st.markdown("---")
st.subheader("🧬 브랜드별 증정 전략 프로필 (Brand DNA)")
stats = []
for brand in selected_brands:
    b_df = f_df[f_df["brand"] == brand]
    if b_df.empty:
        continue
    n = len(b_df)
    stats.append(
        {
            "brand": brand,
            "다양성": n,
            "할인강도": b_df["discount_num"].mean(),
            "식사특화": len(b_df[b_df["category"] == "식사류"]) / n * 100,
            "간식특화": len(b_df[b_df["category"] == "간식류"]) / n * 100,
            "가성비": len(b_df[b_df["unit_price"] < 3000]) / n * 100,
        }
    )
radar_df = pd.DataFrame(stats)
if not radar_df.empty:
    for col in ["다양성", "할인강도", "식사특화", "간식특화", "가성비"]:
        mx = radar_df[col].max()
        if mx > 0:
            radar_df[col] = (radar_df[col] / mx) * 100
    categories = ["다양성", "할인강도", "식사특화", "간식특화", "가성비"]
    fig_radar = go.Figure()
    for _, row in radar_df.iterrows():
        fig_radar.add_trace(
            go.Scatterpolar(
                r=[row[c] for c in categories],
                theta=categories,
                fill="toself",
                name=row["brand"],
                line_color=brand_colors.get(row["brand"]),
                hovertemplate="<b>%{fullData.name}</b><br>%{theta}: %{r:.0f}<extra></extra>",
            )
        )
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=500,
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="closest",
    )
    st.plotly_chart(fig_radar, use_container_width=True)
else:
    st.info("레이더에 표시할 브랜드 데이터가 없습니다.")

# ========== 2. Event share ==========
st.markdown("---")
st.subheader("브랜드별 행사 유형 비중 (1+1 vs 2+1 vs 3+1)")
event_pct = f_df.groupby(["brand", "event"]).size().reset_index(name="count")
brand_totals = event_pct.groupby("brand")["count"].transform("sum")
event_pct["percentage"] = (event_pct["count"] / brand_totals) * 100
fig_pct = px.bar(
    event_pct,
    x="brand",
    y="percentage",
    color="event",
    text=event_pct["percentage"].map(lambda x: f"{x:.1f}%"),
    category_orders={"brand": brand_order},
    color_discrete_sequence=px.colors.qualitative.Pastel,
    labels={"percentage": "비중 (%)", "brand": "브랜드", "event": "행사"},
    custom_data=["event", "count"],
)
_slim_hover(
    fig_pct,
    "<b>%{x}</b><br>%{customdata[0]}: %{y:.1f}% (%{customdata[1]}개)<extra></extra>",
    yaxis_title="비중 (%)",
    barmode="stack",
    height=450,
)
st.plotly_chart(fig_pct, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.subheader("카테고리별 비중 (Treemap)")
    tree_df = (
        f_df.groupby(["brand", "category"], as_index=False)
        .size()
        .rename(columns={"size": "상품수"})
    )
    # 브랜드마다 동일 크기 칸(2×2)으로 배치해 비교하기 쉽게
    cat_order = (
        tree_df.groupby("category")["상품수"].sum().sort_values(ascending=False).index.tolist()
    )
    brands_for_tree = [b for b in brand_order if b in tree_df["brand"].unique()]
    for row_start in range(0, len(brands_for_tree), 2):
        tcols = st.columns(2)
        for j, brand in enumerate(brands_for_tree[row_start : row_start + 2]):
            with tcols[j]:
                b_tree = tree_df[tree_df["brand"] == brand].copy()
                b_tree["category"] = pd.Categorical(
                    b_tree["category"], categories=cat_order, ordered=True
                )
                b_tree = b_tree.sort_values("category")
                fig_tree = px.treemap(
                    b_tree,
                    path=["category"],
                    values="상품수",
                    color_discrete_sequence=[brand_colors.get(brand, "#888")],
                )
                fig_tree.update_traces(
                    textinfo="label+percent root",
                    hovertemplate="<b>%{label}</b><br>상품 %{value}개<extra></extra>",
                    marker=dict(line=dict(width=1, color="rgba(0,0,0,0.35)")),
                )
                fig_tree.update_layout(
                    title=dict(text=brand, x=0.5, xanchor="center", font=dict(size=14)),
                    margin=dict(t=36, l=4, r=4, b=4),
                    height=260,
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_tree, use_container_width=True)
with c2:
    st.subheader("브랜드 × 카테고리 집중도 (Heatmap)")
    heat_data = f_df.groupby(["brand", "category"]).size().unstack(fill_value=0)
    fig_heat = px.imshow(
        heat_data,
        text_auto=True,
        color_continuous_scale="GnBu",
        labels=dict(x="카테고리", y="브랜드", color="상품 수"),
    )
    fig_heat.update_traces(
        hovertemplate="<b>%{y}</b> · %{x}<br>상품 %{z}개<extra></extra>",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ========== 3. Price ==========
st.markdown("---")
st.subheader("💸 가격 전략")
p1, p2 = st.columns(2)
with p1:
    st.markdown("##### 실질 구매가 분포")
    fig_box = px.strip(
        f_df,
        x="brand",
        y="unit_price",
        color="brand",
        color_discrete_map=brand_colors,
        category_orders={"brand": brand_order},
        labels={"brand": "브랜드", "unit_price": "실질가(원)"},
    )
    fig_box.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y:,.0f}원<extra></extra>",
    )
    fig_box.update_layout(showlegend=False, height=420)
    st.plotly_chart(fig_box, use_container_width=True)
with p2:
    st.markdown("##### 가격 구간별 상품 수")
    plot_df = f_df.copy()
    plot_df["price_group"] = pd.cut(
        plot_df["unit_price"],
        bins=[0, 1500, 3000, 5000, 10000, 100000],
        labels=["1.5천 이하", "3천 이하", "5천 이하", "1만 이하", "1만 초과"],
    )
    price_group_df = (
        plot_df.groupby(["brand", "price_group"], observed=False)
        .size()
        .reset_index(name="상품수")
    )
    fig_pg = px.bar(
        price_group_df,
        x="brand",
        y="상품수",
        color="price_group",
        barmode="stack",
        color_discrete_sequence=px.colors.sequential.Teal,
        category_orders={"brand": brand_order},
        labels={"brand": "브랜드", "price_group": "구간"},
        custom_data=["price_group"],
    )
    _slim_hover(
        fig_pg,
        "<b>%{x}</b><br>%{customdata[0]}: %{y}개<extra></extra>",
        showlegend=True,
        height=420,
    )
    st.plotly_chart(fig_pg, use_container_width=True)

# ========== 4. Trends ==========
st.markdown("---")
st.subheader("🔥 트렌드 키워드 대응력")
key_stats = []
for brand in selected_brands:
    b_df = f_df[f_df["brand"] == brand]
    for label, words in TREND_KEYWORDS.items():
        key_stats.append(
            {
                "브랜드": brand,
                "트렌드": label,
                "상품수": _count_keyword_hits(b_df["name"], words),
            }
        )
key_df = pd.DataFrame(key_stats)
fig_key = px.bar(
    key_df,
    x="트렌드",
    y="상품수",
    color="브랜드",
    barmode="group",
    color_discrete_map=brand_colors,
    text_auto=True,
    custom_data=["브랜드"],
)
_slim_hover(
    fig_key,
    "<b>%{customdata[0]}</b><br>%{x}: %{y}개<extra></extra>",
    height=420,
)
st.plotly_chart(fig_key, use_container_width=True)

# ========== 5. Summary ==========
st.markdown("---")
st.subheader(f"📈 요약 통계 (정렬: {sort_option})")
s1, s2 = st.columns(2)
with s1:
    st.markdown("##### 브랜드별 상품 수")
    brand_counts = f_df["brand"].value_counts().reindex(brand_order).reset_index()
    brand_counts.columns = ["브랜드", "상품개수"]
    fig_v1 = px.bar(
        brand_counts,
        x="브랜드",
        y="상품개수",
        text="상품개수",
        color="브랜드",
        color_discrete_map=brand_colors,
        category_orders={"브랜드": brand_order},
    )
    _slim_hover(
        fig_v1,
        "<b>%{x}</b><br>%{y}개<extra></extra>",
        xaxis_tickangle=0,
        showlegend=False,
        height=420,
        margin=dict(t=28, b=48, l=48, r=16),
    )
    st.plotly_chart(fig_v1, use_container_width=True)
with s2:
    st.markdown("##### 행사 유형별 건수")
    event_pivot = (
        f_df.groupby(["brand", "event"]).size().unstack(fill_value=0).reindex(brand_order)
    )
    event_cols = [c for c in DUMP_EVENTS if c in event_pivot.columns]
    n_rows = max(len(event_pivot), 1)
    # Plotly Table은 세로 중앙 정렬이 안 돼 HTML로 맞춤 (헤더 굵게 · 가로·세로 중앙)
    row_h = max(64, int(340 / n_rows))
    th = "".join(
        f'<th style="font-weight:700;text-align:center;vertical-align:middle;'
        f'padding:0.6rem;border:1px solid rgba(255,255,255,0.12);'
        f'background:rgba(255,255,255,0.10);font-size:0.95rem;">{c}</th>'
        for c in ["브랜드", *event_cols]
    )
    body_rows = []
    for i, (brand, row) in enumerate(event_pivot.iterrows()):
        bg = "rgba(255,255,255,0.06)" if i % 2 == 0 else "rgba(255,255,255,0.03)"
        cells = [
            f'<td style="text-align:center;vertical-align:middle;height:{row_h}px;'
            f'border:1px solid rgba(255,255,255,0.08);background:{bg};'
            f'font-size:1rem;">{brand}</td>'
        ]
        for c in event_cols:
            cells.append(
                f'<td style="text-align:center;vertical-align:middle;height:{row_h}px;'
                f'border:1px solid rgba(255,255,255,0.08);background:{bg};'
                f'font-size:1rem;">{int(row[c]):,}</td>'
            )
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(
        f'<div style="height:420px;display:flex;align-items:stretch;padding:0.35rem 0 1.2rem 0;">'
        f'<table style="width:100%;height:100%;border-collapse:collapse;'
        f'color:#fff;table-layout:fixed;">'
        f"<thead><tr>{th}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )

s3, s4 = st.columns(2)
with s3:
    st.markdown("##### 평균 실질 구매가")
    avg_price = f_df.groupby("brand")["unit_price"].mean().reindex(brand_order).reset_index()
    avg_price.columns = ["brand", "unit_price"]
    fig_v2 = px.line(
        avg_price,
        x="brand",
        y="unit_price",
        markers=True,
        category_orders={"brand": brand_order},
        labels={"brand": "브랜드", "unit_price": "평균 실질가"},
    )
    fig_v2.update_traces(
        line=dict(color="#FF6B6B", width=3),
        marker=dict(size=10),
        hovertemplate="<b>%{x}</b><br>%{y:,.0f}원<extra></extra>",
    )
    fig_v2.update_layout(height=400, hovermode="x unified")
    st.plotly_chart(fig_v2, use_container_width=True)
with s4:
    st.markdown("##### 평균 할인율")
    avg_disc = f_df.groupby("brand")["discount_num"].mean().reindex(brand_order).reset_index()
    avg_disc.columns = ["brand", "discount_num"]
    fig_v3 = px.bar(
        avg_disc,
        x="brand",
        y="discount_num",
        text=avg_disc["discount_num"].map(lambda x: f"{x:.1f}%" if pd.notnull(x) else "0%"),
        color="brand",
        color_discrete_map=brand_colors,
        category_orders={"brand": brand_order},
    )
    fig_v3.update_traces(
        textposition="outside",
        marker_line_width=0,
        width=0.5,
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    )
    fig_v3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showticklabels=False, showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        xaxis=dict(showgrid=False),
        showlegend=False,
        height=400,
    )
    st.plotly_chart(fig_v3, use_container_width=True)

with st.expander("📄 검색 결과 상품 목록"):
    show_cols = [
        c
        for c in ["brand", "category", "name", "price", "event", "unit_price", "discount_num"]
        if c in f_df.columns
    ]
    st.dataframe(f_df[show_cols], use_container_width=True, hide_index=True)
