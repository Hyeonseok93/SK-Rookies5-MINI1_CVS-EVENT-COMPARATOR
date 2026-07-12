"""Shared product filter expander UI."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass
class FilterState:
    search_query: str
    sort_option: str
    selected_brands: list
    selected_events: list
    selected_cats: list
    filtered_df: pd.DataFrame


def track_recent_keyword(search_query: str, limit: int = 5) -> None:
    if not search_query:
        return
    if "recent_keywords" not in st.session_state:
        st.session_state["recent_keywords"] = []
    kws = st.session_state["recent_keywords"]
    if search_query in kws:
        kws.remove(search_query)
    kws.insert(0, search_query)
    st.session_state["recent_keywords"] = kws[:limit]


def apply_sort(df: pd.DataFrame, sort_option: str, search_query: str = "") -> pd.DataFrame:
    out = df
    if sort_option == "가격 낮은 순" and "unit_price" in out.columns:
        return out.sort_values(by="unit_price", ascending=True)
    if sort_option == "가격 높은 순" and "unit_price" in out.columns:
        return out.sort_values(by="unit_price", ascending=False)
    if (
        not search_query
        and "recent_keywords" in st.session_state
        and st.session_state["recent_keywords"]
        and "name" in out.columns
    ):
        latest = st.session_state["recent_keywords"][0]
        ranked = out.copy()
        ranked["is_recommended"] = ranked["name"].str.contains(latest, case=False, na=False).astype(int)
        ranked = ranked.sort_values(by="is_recommended", ascending=False)
        return ranked.drop(columns=["is_recommended"])
    return out


def render_product_filters(
    df: pd.DataFrame,
    *,
    expander_title: str = "🔍 상세 필터 및 검색",
    sort_options: list | None = None,
    exclude_events: list | None = None,
    key_prefix: str = "flt",
) -> FilterState:
    """Standard search / sort / brand / event / category filter block."""
    sort_options = sort_options or ["기본", "가격 낮은 순", "가격 높은 순"]
    exclude_events = exclude_events if exclude_events is not None else ["SALE", "세일"]

    with st.expander(expander_title, expanded=True):
        r1_c1, r1_c2 = st.columns([3, 1])
        with r1_c1:
            search_query = st.text_input(
                "📝 검색", "", placeholder="상품명 입력", key=f"{key_prefix}_search"
            )
            track_recent_keyword(search_query)
        with r1_c2:
            sort_option = st.selectbox("💰 정렬", sort_options, key=f"{key_prefix}_sort")

        r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])
        with r2_c1:
            brand_list = sorted(df["brand"].dropna().unique().tolist())
            selected_brands = st.multiselect(
                "🏪 브랜드", brand_list, default=brand_list, key=f"{key_prefix}_brands"
            )
        with r2_c2:
            event_list = sorted(
                [e for e in df["event"].dropna().unique().tolist() if e not in exclude_events]
            )
            selected_events = st.multiselect(
                "🎁 행사", event_list, default=event_list, key=f"{key_prefix}_events"
            )
        with r2_c3:
            cat_list = sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else []
            selected_cats = st.multiselect(
                "📂 분류", cat_list, default=cat_list, key=f"{key_prefix}_cats"
            ) if cat_list else []

    filtered = df[
        (df["brand"].isin(selected_brands))
        & (df["event"].isin(selected_events))
        & (df["name"].str.contains(search_query, case=False, na=False))
    ]
    if selected_cats and "category" in filtered.columns:
        filtered = filtered[filtered["category"].isin(selected_cats)]

    filtered = apply_sort(filtered, sort_option, search_query)

    return FilterState(
        search_query=search_query,
        sort_option=sort_option,
        selected_brands=selected_brands,
        selected_events=selected_events,
        selected_cats=selected_cats,
        filtered_df=filtered,
    )
