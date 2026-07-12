"""Canonical brand colors and name normalization."""
from __future__ import annotations

BRAND_COLORS = {
    "CU": "#652D90",
    "GS25": "#0054A6",
    "7-Eleven": "#008061",
    "7Eleven": "#008061",
    "세븐일레븐": "#008061",
    "emart24": "#FFB81C",
    "이마트24": "#FFB81C",
}

# Scraper / CSV canonical keys
CANONICAL_BRANDS = {
    "cu": "CU",
    "gs25": "GS25",
    "7eleven": "7Eleven",
    "7-eleven": "7Eleven",
    "세븐일레븐": "7Eleven",
    "emart24": "emart24",
    "이마트24": "emart24",
}

DISPLAY_BRANDS = {
    "CU": "CU",
    "GS25": "GS25",
    "7Eleven": "세븐일레븐",
    "emart24": "이마트24",
}


def get_brand_color(brand: str) -> str:
    if brand is None:
        return "#8b949e"
    return BRAND_COLORS.get(str(brand), "#8b949e")


def normalize_brand(brand: str) -> str:
    """Map EN/KR aliases to scraper canonical names."""
    if brand is None:
        return ""
    raw = str(brand).strip()
    key = raw.lower().replace(" ", "")
    return CANONICAL_BRANDS.get(key, raw)


def display_brand(brand: str) -> str:
    canon = normalize_brand(brand)
    return DISPLAY_BRANDS.get(canon, canon or str(brand))
