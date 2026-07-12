"""Shared scraper CSV save helpers."""
from __future__ import annotations

import os
from datetime import datetime

import pandas as pd

from utils.paths import get_data_dir


def save_products(
    df: pd.DataFrame,
    brand: str,
    *,
    start_ts: datetime | None = None,
    dedupe_subset: list | None = None,
) -> str | None:
    """
    Save brand products under DATA_DIR (or ./data) as {brand}_{yymmdd}.csv.
    Returns saved path or None if empty.
    """
    if df is None or df.empty:
        print("❌ 수집된 데이터가 없습니다.")
        return None

    start_ts = start_ts or datetime.now()
    work = df.copy()
    raw_count = len(work)
    subset = dedupe_subset or ["name", "event"]
    subset = [c for c in subset if c in work.columns]
    if subset:
        work = work.drop_duplicates(subset=subset, keep="first")

    date_str = datetime.now().strftime("%y%m%d")
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, f"{brand}_{date_str}.csv")
    work.to_csv(file_path, index=False, encoding="utf-8-sig")

    duration = datetime.now() - start_ts
    print("\n최종 결과 요약:")
    print(f" - 전체 수집 개수: {raw_count}")
    print(f" - 중복 제거 후  : {len(work)}")
    print(f" - 저장 파일명   : {file_path}")
    print(f" - 소요 시간     : {duration.seconds // 60}분 {duration.seconds % 60}초")
    return file_path
