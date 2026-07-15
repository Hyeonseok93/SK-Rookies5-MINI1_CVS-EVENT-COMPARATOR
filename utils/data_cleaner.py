"""Shared CSV cleansing for manual runs and the daily batch."""
from __future__ import annotations

import glob
import os

import pandas as pd
from loguru import logger

from utils.paths import cleaned_path, get_data_dir, is_brand_raw_csv


def sanitize_price_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["price"] = out["price"].astype(str).str.replace(r"[^0-9]", "", regex=True)
    out["price"] = pd.to_numeric(out["price"], errors="coerce").fillna(0).astype(int)
    return out


def merge_brand_dataframes(df_list: list[pd.DataFrame]) -> pd.DataFrame | None:
    if not df_list:
        return None
    combined = pd.concat(df_list, ignore_index=True)
    final_df = combined.dropna(subset=["brand", "name", "event"]).drop_duplicates()
    return final_df[~final_df["name"].str.contains("디폴트 이미지", na=False)]


def write_cleaned_csv(final_df: pd.DataFrame) -> str:
    output_path = cleaned_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tmp_path = output_path + ".tmp"
    final_df.to_csv(tmp_path, index=False, encoding="utf-8-sig")
    os.replace(tmp_path, output_path)
    return output_path


def load_and_merge_files(files: list[str]) -> pd.DataFrame | None:
    """Load brand CSVs, sanitize prices, merge, and write cleaned_data.csv."""
    if not files:
        logger.error("data/ 폴더 안에 처리할 브랜드 CSV 파일이 없습니다.")
        return None

    logger.info(f"정제 대상 파일: {files}")
    df_list: list[pd.DataFrame] = []

    for file in files:
        try:
            df = pd.read_csv(file, encoding="utf-8-sig")
            if "price" not in df.columns:
                logger.error(f"{file}: price 컬럼 없음 — 스킵")
                continue
            df_list.append(sanitize_price_column(df))
            logger.info(f"파일 로드 완료: {file}")
        except Exception as e:
            logger.error(f"{file} 처리 중 오류 발생: {e}")

    final_df = merge_brand_dataframes(df_list)
    if final_df is None:
        logger.error("로드된 데이터가 없습니다.")
        return None

    output_path = write_cleaned_csv(final_df)
    logger.success(
        f"정제 및 통합 완료: 총 {len(final_df)}개의 데이터가 '{output_path}'에 저장되었습니다."
    )
    return final_df


def clean_and_merge() -> pd.DataFrame | None:
    logger.info("데이터 정제를 시작합니다.")
    data_dir = get_data_dir()
    all_files = [f for f in glob.glob(os.path.join(data_dir, "*.csv")) if is_brand_raw_csv(f)]
    return load_and_merge_files(all_files)


if __name__ == "__main__":
    clean_and_merge()
