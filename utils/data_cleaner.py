import pandas as pd
import glob
from loguru import logger
import os

from utils.paths import cleaned_path, get_data_dir, is_brand_raw_csv


def clean_and_merge():
    logger.info("데이터 정제를 시작합니다.")

    data_dir = get_data_dir()
    all_files = [f for f in glob.glob(os.path.join(data_dir, "*.csv")) if is_brand_raw_csv(f)]

    if not all_files:
        logger.error("data/ 폴더 안에 처리할 브랜드 CSV 파일이 없습니다.")
        return

    logger.info(f"정제 대상 파일: {all_files}")

    df_list = []

    for file in all_files:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')

            if 'price' not in df.columns:
                logger.error(f"{file}: price 컬럼 없음 — 스킵")
                continue

            # 가격 데이터에서 숫자만 추출
            df['price'] = df['price'].astype(str).str.replace(r'[^0-9]', '', regex=True)
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0).astype(int)

            df_list.append(df)
            logger.info(f"파일 로드 완료: {file}")

        except Exception as e:
            logger.error(f"{file} 처리 중 오류 발생: {e}")

    if not df_list:
        logger.error("로드된 데이터가 없습니다.")
        return

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

if __name__ == "__main__":
    clean_and_merge()
