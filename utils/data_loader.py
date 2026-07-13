"""Cached categorized product loader used across Streamlit pages."""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from utils.brand import normalize_brand
from utils.paths import categorized_path
from utils.pricing import discount_num, discount_rate, pay_and_total_counts


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "event" in out.columns:
        out["event"] = out["event"].astype(str).str.replace(" ", "", regex=False)
        out["event"] = out["event"].replace({"SALE": "세일"})
    if "price" in out.columns:
        out["price"] = out["price"].astype(str).str.replace(r"[^\d.]", "", regex=True)
        out["price"] = pd.to_numeric(out["price"], errors="coerce").fillna(0).astype(int)
    if "brand" in out.columns:
        out["brand"] = out["brand"].map(normalize_brand)
    return out


def _unit_price_vectorized(events: pd.Series, prices: pd.Series) -> pd.Series:
    e = events.astype(str).str.replace(" ", "", regex=False)
    p = prices.astype(int)
    out = p.copy()
    m1 = e == "1+1"
    m2 = e == "2+1"
    m3 = e == "3+1"
    out = out.mask(m1, p // 2)
    out = out.mask(m2, (p * 2) // 3)
    out = out.mask(m3, (p * 3) // 4)
    return out.astype(int)


@st.cache_data(ttl=3600)
def load_categorized_df(
    with_unit_price: bool = True,
    with_discount_num: bool = False,
    with_pay_counts: bool = False,
    drop_duplicates: bool = True,
) -> pd.DataFrame:
    path = categorized_path()
    if not os.path.exists(path):
        return pd.DataFrame()

    df = _normalize_frame(pd.read_csv(path))

    if with_unit_price and not df.empty:
        df["unit_price"] = _unit_price_vectorized(df["event"], df["price"])
        df["discount_rate"] = df["event"].map(discount_rate)

    if with_discount_num and not df.empty:
        df["discount_num"] = df["event"].map(discount_num)

    if with_pay_counts and not df.empty:
        counts = df["event"].map(pay_and_total_counts)
        df["pay_count"] = counts.map(lambda t: t[0])
        df["total_count"] = counts.map(lambda t: t[1])

    if drop_duplicates and not df.empty and {"name", "event", "brand"}.issubset(df.columns):
        df = df.drop_duplicates(subset=["name", "event", "brand"])

    return df
