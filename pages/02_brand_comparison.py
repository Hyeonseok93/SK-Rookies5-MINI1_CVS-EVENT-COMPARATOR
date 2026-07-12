import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_categorized_df
from utils.filters import render_product_filters

df = load_categorized_df()

st.title("📊 브랜드별 행사 비교")

if not df.empty:
    brand_colors = {
        "CU": "#9BC621",
        "7Eleven": "#008135",
        "emart24": "#FFB71B",
        "GS25": "#0095D3",
    }

    state = render_product_filters(df, key_prefix="brand_cmp")
    sort_option = state.sort_option
    filtered_df = state.filtered_df

    st.subheader("📊 브랜드별 행사 통계")

    if not filtered_df.empty:
        event_pivot = filtered_df.groupby(["brand", "event"]).size().unstack(fill_value=0)

        desired_order = ["1+1", "2+1", "3+1", "4+1", "5+1"]
        existing_cols = [c for c in desired_order if c in event_pivot.columns]
        other_cols = sorted([c for c in event_pivot.columns if c not in desired_order])
        cols_order = existing_cols + other_cols
        event_pivot = event_pivot[cols_order]

        if sort_option == "가격 높은 순":
            if len(cols_order) > 0:
                sort_indices = sorted(
                    range(len(event_pivot)),
                    key=lambda i: event_pivot[cols_order[0]].iloc[i],
                    reverse=True,
                )
                event_pivot = event_pivot.iloc[sort_indices]
        elif sort_option == "가격 낮은 순":
            if len(cols_order) > 0:
                sort_indices = sorted(
                    range(len(event_pivot)),
                    key=lambda i: event_pivot[cols_order[0]].iloc[i],
                    reverse=False,
                )
                event_pivot = event_pivot.iloc[sort_indices]
        else:
            event_pivot = event_pivot.sort_index(ascending=True)

        brand_order = event_pivot.index.tolist()

        sorted_event_data = {}
        for col in cols_order:
            if sort_option == "가격 높은 순":
                sorted_event_data[col] = sorted(event_pivot[col].values, reverse=True)
            elif sort_option == "가격 낮은 순":
                sorted_event_data[col] = sorted(event_pivot[col].values, reverse=False)
            else:
                sorted_event_data[col] = event_pivot[col].values

        event_pivot_display = pd.DataFrame(sorted_event_data, index=brand_order)

        first_col_sorted_values = sorted_event_data[cols_order[0]]

        brand_counts = pd.DataFrame({"브랜드": brand_order, "상품 개수": first_col_sorted_values})
        brand_counts["브랜드"] = pd.Categorical(brand_counts["브랜드"], categories=brand_order, ordered=True)
        brand_counts = brand_counts.sort_values("브랜드")

        col1, col2 = st.columns(2)
        with col1:
            st.write("✨ 브랜드별 총 행사 상품 수")
            fig1 = px.bar(
                brand_counts,
                x="브랜드",
                y="상품 개수",
                text="상품 개수",
                color="브랜드",
                color_discrete_map=brand_colors,
                category_orders={"브랜드": brand_order},
            )
            fig1.update_layout(xaxis_tickangle=0, showlegend=False, height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.write(f"📝 상세 통계 표 ({sort_option})")
            event_brand_counts = event_pivot_display.copy()
            event_brand_counts.index = event_brand_counts.index.astype(str)
            event_brand_counts.index.name = "브랜드"
            st.dataframe(event_brand_counts, use_container_width=True)

        st.subheader("💰 브랜드별 평균 개당 가격")
        avg_price_dict = dict(filtered_df.groupby("brand")["unit_price"].mean())
        avg_price = pd.DataFrame(
            {"브랜드": brand_order, "평균가격": [avg_price_dict.get(b, 0) for b in brand_order]}
        )
        avg_price["브랜드"] = pd.Categorical(avg_price["브랜드"], categories=brand_order, ordered=True)
        avg_price = avg_price.sort_values("브랜드", key=lambda x: x.cat.codes)

        fig2 = px.line(avg_price, x="브랜드", y="평균가격", markers=True, category_orders={"브랜드": brand_order})
        fig2.update_traces(line=dict(color="#FF6B6B", width=3), marker=dict(size=10))
        fig2.update_layout(
            xaxis_tickangle=0,
            showlegend=False,
            height=400,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📉 브랜드별 평균 할인율")

        filtered_df = filtered_df.copy()
        filtered_df["discount_rate"] = 0.0

        valid_mask = filtered_df["price"] > 0
        filtered_df.loc[valid_mask, "discount_rate"] = (
            (filtered_df.loc[valid_mask, "price"] - filtered_df.loc[valid_mask, "unit_price"])
            / filtered_df.loc[valid_mask, "price"]
            * 100
        )

        discount_df = filtered_df[filtered_df["discount_rate"] > 0]
        avg_discount_dict = dict(discount_df.groupby("brand")["discount_rate"].mean())

        avg_discount = pd.DataFrame(
            {"브랜드": brand_order, "평균할인율": [avg_discount_dict.get(b, 0) for b in brand_order]}
        )

        fig3 = px.bar(
            avg_discount,
            x="브랜드",
            y="평균할인율",
            text=[f"{val:.1f}%" for val in avg_discount["평균할인율"]],
            color="브랜드",
            color_discrete_map=brand_colors,
            category_orders={"브랜드": brand_order},
        )

        fig3.update_traces(
            textposition="outside",
            textfont=dict(
                size=15, family="Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif", weight="bold"
            ),
            marker_line_width=0,
            opacity=1.0,
            width=0.45,
        )

        min_val = avg_discount["평균할인율"].min()
        max_val = avg_discount["평균할인율"].max()

        y_min = max(0, min_val - 2)
        y_max = max_val + 2 if max_val > 0 else 10

        fig3.update_layout(
            xaxis_tickangle=0,
            showlegend=False,
            height=380,
            yaxis_title=None,
            font=dict(family="Pretendard, -apple-system, system-ui, sans-serif", size=13, color="#8B95A1"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=14, color="#E5E8EB", weight="bold")),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.05)",
                zeroline=False,
                showticklabels=False,
                range=[y_min, y_max],
            ),
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("📈 브랜드별 핵심 요약")
        brand_stats = (
            filtered_df.groupby("brand")
            .agg({"name": "count", "unit_price": "mean"})
            .rename(columns={"name": "상품 수", "unit_price": "평균 단가"})
        )
        brand_stats = brand_stats.sort_values("평균 단가", ascending=False)

        if len(brand_stats) > 0:
            m_cols = st.columns(len(brand_stats))
            for i, (brand, row) in enumerate(brand_stats.iterrows()):
                with m_cols[i]:
                    st.metric(brand, f"{int(row['상품 수'])}개", f"평균 {int(row['평균 단가']):,}원")
    else:
        st.warning("필터링된 결과가 없습니다.")
else:
    st.error("데이터를 불러올 수 없습니다.")
