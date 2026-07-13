"""Shared themed product-guide UI (diet / night snack)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from utils.cart import render_cart_button
from utils.filters import SEARCH_MAX_CHARS, name_contains, track_recent_keyword
from utils.product_grid import paginate, product_card_html, render_pagination


@dataclass(frozen=True)
class ThemeGuideConfig:
    title: str
    themes: dict[str, list[str]]
    exclude_keywords: list[str]
    page_key: str
    cart_prefix: str
    btn_prefix: str
    expander_title: str = "🔍 상세 필터 및 테마 선택"
    subtitle: str | None = None
    theme_label: str = "🎯 테마"
    search_label: str = "📝 검색"
    search_placeholder: str = "상품명 입력"
    sort_label: str = "💰 정렬"
    sort_options: tuple[str, ...] = ("기본", "가격 낮은 순", "가격 높은 순")
    brand_label: str = "🏪 브랜드"
    event_label: str = "🎁 행사"
    cat_label: str = "📂 분류"
    result_kind: str = "info"  # info | success
    empty_message: str = "결과가 없습니다."
    footer: str | None = None


def _name_matches_any(series: pd.Series, keywords: list[str]) -> pd.Series:
    mask = pd.Series(False, index=series.index)
    for kw in keywords:
        if not kw:
            continue
        mask |= series.astype(str).str.contains(kw, case=False, na=False, regex=False)
    return mask


def filter_theme_products(
    df: pd.DataFrame,
    *,
    keywords: list[str],
    exclude_keywords: list[str],
    selected_brands: list,
    selected_events: list,
    selected_cats: list,
    search_query: str,
) -> pd.DataFrame:
    out = df[
        _name_matches_any(df["name"], keywords)
        & ~_name_matches_any(df["name"], exclude_keywords)
        & (df["brand"].isin(selected_brands))
        & (df["event"].isin(selected_events))
        & (df["category"].isin(selected_cats))
        & name_contains(df["name"], search_query)
    ]
    return out


def _apply_theme_sort(df: pd.DataFrame, sort_option: str) -> pd.DataFrame:
    if sort_option == "가격 낮은 순":
        return df.sort_values(by="unit_price")
    if sort_option == "가격 높은 순":
        return df.sort_values(by="unit_price", ascending=False)
    # 기본 / 할인율 순 — 숫자 컬럼 사용 (문자열 "50%" 정렬 방지)
    if "discount_num" in df.columns:
        return df.sort_values(by="discount_num", ascending=False)
    return df.sort_values(by="discount_rate", ascending=False)


def render_theme_guide(df: pd.DataFrame, config: ThemeGuideConfig) -> None:
    st.title(config.title)
    if config.subtitle:
        st.markdown(config.subtitle)

    if df.empty:
        st.info("데이터를 불러오는 중입니다...")
        return

    with st.expander(config.expander_title, expanded=True):
        r1_c1, r1_c2, r1_c3 = st.columns([2, 1, 1])
        with r1_c1:
            search_query = st.text_input(
                config.search_label,
                "",
                placeholder=config.search_placeholder,
                max_chars=SEARCH_MAX_CHARS,
                key=f"{config.page_key}_search",
            )
            track_recent_keyword(search_query)
        with r1_c2:
            selected_theme = st.selectbox(
                config.theme_label,
                list(config.themes.keys()),
                key=f"{config.page_key}_theme",
            )
            keywords = config.themes[selected_theme]
        with r1_c3:
            sort_option = st.selectbox(
                config.sort_label,
                list(config.sort_options),
                key=f"{config.page_key}_sort",
            )

        r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])
        with r2_c1:
            brand_list = sorted(df["brand"].unique().tolist())
            selected_brands = st.multiselect(
                config.brand_label,
                brand_list,
                default=brand_list,
                key=f"{config.page_key}_brands",
            )
        with r2_c2:
            event_list = sorted(
                [e for e in df["event"].unique().tolist() if e not in ["SALE", "세일"]]
            )
            selected_events = st.multiselect(
                config.event_label,
                event_list,
                default=event_list,
                key=f"{config.page_key}_events",
            )
        with r2_c3:
            cat_list = sorted(df["category"].unique().tolist())
            selected_cats = st.multiselect(
                config.cat_label,
                cat_list,
                default=cat_list,
                key=f"{config.page_key}_cats",
            )

    filtered_df = filter_theme_products(
        df,
        keywords=keywords,
        exclude_keywords=config.exclude_keywords,
        selected_brands=selected_brands,
        selected_events=selected_events,
        selected_cats=selected_cats,
        search_query=search_query,
    )
    filtered_df = _apply_theme_sort(filtered_df, sort_option)

    query_hash = (
        selected_theme
        + str(selected_brands)
        + str(selected_events)
        + str(selected_cats)
        + search_query
        + sort_option
    )
    display_df, total_pages = paginate(
        filtered_df, page_key=config.page_key, query_hash=query_hash, items_per_page=30
    )

    if display_df.empty:
        st.warning(config.empty_message)
    else:
        msg = f"**{selected_theme}** 테마 상품 {len(filtered_df)}건"
        if config.result_kind == "success":
            st.success(f"🍻 {msg}을 찾았습니다!")
        else:
            st.info(f"✨ {msg} 검색")

        cols = st.columns(5)
        for idx, (_, row) in enumerate(display_df.iterrows()):
            with cols[idx % 5]:
                st.markdown(product_card_html(row), unsafe_allow_html=True)
                render_cart_button(row, f"{config.cart_prefix}_{idx}")

        render_pagination(config.page_key, total_pages, btn_prefix=config.btn_prefix)

    if config.footer:
        st.markdown("---")
        st.caption(config.footer)
