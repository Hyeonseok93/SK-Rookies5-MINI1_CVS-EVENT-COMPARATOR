from __future__ import annotations

import pandas as pd
import glob
from loguru import logger
import os
from datetime import datetime
import pytz

from utils.paths import BRAND_RAW_PREFIXES, cleaned_path, get_data_dir, is_brand_raw_csv


def _latest_per_brand(files: list[str], yymm: str) -> list[str]:
    """Prefer files matching YYMM; fall back to newest file per brand if none."""
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
        pool = month_hits if month_hits else paths
        pool.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        selected.append(pool[0])
        if not month_hits:
            logger.warning(f"{brand}: {yymm} 파일 없음 → 최신 파일 사용: {pool[0]}")
    return selected


def clean_and_merge_batch(year: int | None = None, month: int | None = None):
    """
    Merge brand raw CSVs for the target YYMM into cleaned_data.csv.
    Returns the final DataFrame, or None on failure.
    """
    logger.info("데이터 정제를 시작합니다.")

    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    target_year = year if year is not None else now_kst.year
    target_month = month if month is not None else now_kst.month
    current_target = f"{target_year % 100:02d}{target_month:02d}"

    data_dir = get_data_dir()
    raw_files = glob.glob(os.path.join(data_dir, "*.csv"))
    brand_files = [f for f in raw_files if is_brand_raw_csv(f)]
    all_files = _latest_per_brand(brand_files, current_target)

    if not all_files:
        logger.error(f"data/ 폴더 안에 {current_target}(대상 달)에 해당하는 브랜드 CSV가 없습니다.")
        return None

    logger.info(f"정제 대상 파일 ({current_target} 데이터): {all_files}")

    df_list = []

    for file in all_files:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')

            if 'price' not in df.columns:
                logger.error(f"{file}: price 컬럼 없음 — 스킵")
                continue

            df['price'] = df['price'].astype(str).str.replace(r'[^0-9]', '', regex=True)
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0).astype(int)

            df_list.append(df)
            logger.info(f"파일 로드 완료: {file}")

        except Exception as e:
            logger.error(f"{file} 처리 중 오류 발생: {e}")

    if not df_list:
        logger.error("로드된 데이터가 없습니다.")
        return None

    combined_df = pd.concat(df_list, ignore_index=True)

    # 필수 컬럼 결측치 제거 및 중복 제거
    final_df = combined_df.dropna(subset=['brand', 'name', 'event']).drop_duplicates()

    # 노이즈 데이터 제거
    final_df = final_df[~final_df['name'].str.contains('디폴트 이미지', na=False)]

    output_path = cleaned_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tmp_path = output_path + ".tmp"
    final_df.to_csv(tmp_path, index=False, encoding='utf-8-sig')
    os.replace(tmp_path, output_path)
    logger.success(f"정제 및 통합 완료: 총 {len(final_df)}개의 데이터가 '{output_path}'에 저장되었습니다.")
    return final_df


if __name__ == "__main__":
    clean_and_merge_batch()
