"""Shared scraper CSV save helpers."""
from __future__ import annotations

import datetime as datetime_module
import os
import time

import pandas as pd

from utils.paths import get_data_dir


def save_products(
    df: pd.DataFrame,
    brand: str,
    *,
    start_ts: datetime_module.datetime | None = None,
    t0: float | None = None,
    dedupe_subset: list | None = None,
    file_stamp: str | None = None,
) -> str | None:
    """
    Save brand products under DATA_DIR (or ./data) as {brand}_{stamp}.csv.

    Filename stamp priority:
      1) file_stamp arg
      2) BATCH_FILE_STAMP env (set by daily batch runner, usually YYMMDD)
      3) start_ts.strftime("%y%m%d")
      4) wall-clock now

    Elapsed time:
      - prefer t0=time.perf_counter() captured at crawl start (batch-safe)
      - else wall-clock delta from start_ts using real datetime (not monkeypatched)
    """
    if df is None or df.empty:
        print("❌ 수집된 데이터가 없습니다.")
        return None

    wall_now = datetime_module.datetime.now()
    start_ts = start_ts or wall_now
    work = df.copy()
    raw_count = len(work)
    subset = dedupe_subset or ["name", "event"]
    subset = [c for c in subset if c in work.columns]
    if subset:
        work = work.drop_duplicates(subset=subset, keep="first")

    stamp = (
        file_stamp
        or os.environ.get("BATCH_FILE_STAMP")
        or start_ts.strftime("%y%m%d")
    )
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, f"{brand}_{stamp}.csv")
    work.to_csv(file_path, index=False, encoding="utf-8-sig")

    if t0 is not None:
        elapsed_sec = max(0, int(time.perf_counter() - t0))
    else:
        # Real wall clock — survives scraper datetime monkeypatch on `datetime` name
        elapsed_sec = max(0, int((wall_now - start_ts).total_seconds()))
        # Patched start_ts far from wall clock → delta meaningless
        if elapsed_sec > 12 * 3600:
            elapsed_sec = 0

    print("\n최종 결과 요약:")
    print(f" - 전체 수집 개수: {raw_count}")
    print(f" - 중복 제거 후  : {len(work)}")
    print(f" - 저장 파일명   : {file_path}")
    print(f" - 소요 시간     : {elapsed_sec // 60}분 {elapsed_sec % 60}초")
    return file_path
