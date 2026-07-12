"""Project and data path helpers. Honors DATA_DIR env when set by batch."""
from __future__ import annotations

import os

_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_UTILS_DIR)

BRAND_RAW_PREFIXES = ("7Eleven", "CU", "emart24", "GS25")
NON_PRODUCT_CSV_NAMES = {
    "cleaned_data.csv",
    "categorized_data.csv",
    "official_event_news.csv",
    "filtered_convenience_stores.csv",
}


def get_data_dir() -> str:
    env = os.environ.get("DATA_DIR")
    if env:
        return env
    return os.path.join(PROJECT_ROOT, "data")


def data_path(*parts: str) -> str:
    return os.path.join(get_data_dir(), *parts)


def categorized_path() -> str:
    return data_path("categorized_data.csv")


def cleaned_path() -> str:
    return data_path("cleaned_data.csv")


def style_css_path() -> str:
    return os.path.join(PROJECT_ROOT, "style.css")


def is_brand_raw_csv(filename: str) -> bool:
    name = os.path.basename(filename)
    if name in NON_PRODUCT_CSV_NAMES:
        return False
    lower = name.lower()
    return any(brand.lower() in lower for brand in BRAND_RAW_PREFIXES)
