"""Batch-oriented cleaner: pick YYMM file per brand, then shared merge."""
from __future__ import annotations

import glob
import os
from datetime import datetime

import pytz
from loguru import logger

from utils.data_cleaner import load_and_merge_files
from utils.paths import BRAND_RAW_PREFIXES, get_data_dir, is_brand_raw_csv


def _latest_per_brand(files: list[str], yymm: str, *, allow_fallback: bool = False) -> list[str]:
    """Prefer files matching YYMM. Without allow_fallback, skip brands missing that month."""
    by_brand: dict[str, list[str]] = {b: [] for b in BRAND_RAW_PREFIXES}
    for f in files:
        base = os.path.basename(f)
        for brand in BRAND_RAW_PREFIXES:
            if brand.lower() in base.lower():
                by_brand[brand].append(f)
                break

    selected = []
    for brand, paths in by_brand.items():
        if not paths:
            continue
        month_hits = [p for p in paths if f"_{yymm}" in os.path.basename(p)]
        if month_hits:
            month_hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            selected.append(month_hits[0])
            continue
        if allow_fallback:
            paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            selected.append(paths[0])
            logger.warning(f"{brand}: {yymm} 파일 없음 → 최신 파일 사용: {paths[0]}")
        else:
            logger.error(f"{brand}: {yymm} 파일 없음 — 스킵 (fallback 비활성)")
    return selected


def clean_and_merge_batch(
    year: int | None = None,
    month: int | None = None,
    *,
    allow_fallback: bool = False,
):
    """
    Merge brand raw CSVs for the target YYMM into cleaned_data.csv.
    Returns the final DataFrame, or None on failure.

    allow_fallback=True 이면 대상 월 파일이 없을 때 브랜드별 최신 파일로 대체합니다.
    기본값은 False (월 혼입 방지).
    """
    logger.info("데이터 정제를 시작합니다.")

    kst = pytz.timezone("Asia/Seoul")
    now_kst = datetime.now(kst)
    target_year = year if year is not None else now_kst.year
    target_month = month if month is not None else now_kst.month
    current_target = f"{target_year % 100:02d}{target_month:02d}"

    data_dir = get_data_dir()
    brand_files = [f for f in glob.glob(os.path.join(data_dir, "*.csv")) if is_brand_raw_csv(f)]
    all_files = _latest_per_brand(brand_files, current_target, allow_fallback=allow_fallback)

    if not all_files:
        logger.error(f"data/ 폴더 안에 {current_target}(대상 달)에 해당하는 브랜드 CSV가 없습니다.")
        return None

    if len(all_files) < len(BRAND_RAW_PREFIXES) and not allow_fallback:
        logger.warning(
            f"대상 월({current_target}) 브랜드 파일 {len(all_files)}/{len(BRAND_RAW_PREFIXES)}개만 확보"
        )

    logger.info(f"정제 대상 파일 ({current_target} 데이터): {all_files}")
    return load_and_merge_files(all_files)


if __name__ == "__main__":
    clean_and_merge_batch()
