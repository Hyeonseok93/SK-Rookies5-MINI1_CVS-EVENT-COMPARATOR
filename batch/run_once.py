"""
배치 1회 즉시 실행 (스케줄러 없이).

  python -m batch.run_once
  python -m batch.run_once --dry-run
  python -m batch.run_once --year 2026 --month 7
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime

import pytz

from batch.script.crawl_batch_script import run_daily_data_batch


def main() -> int:
    parser = argparse.ArgumentParser(description="편의점 행사 데이터 일간 배치 1회 실행")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="파일명 스탬프용 연도 (기본: 오늘 KST)",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=None,
        help="파일명 스탬프용 월 (기본: 오늘 KST)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="크롤·정제·분류·뉴스 전부 스킵 (카탈로그 미변경)",
    )
    args = parser.parse_args()

    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst).replace(tzinfo=None)
    year = args.year if args.year is not None else now.year
    month = args.month if args.month is not None else now.month

    print(f"Running daily batch once: stamp={year}-{month:02d} (dry_run={args.dry_run})")
    ok = run_daily_data_batch(
        year=year,
        month=month,
        run_time=now,
        dry_run=args.dry_run,
    )
    if ok:
        print("Batch finished successfully.")
        return 0
    print("Batch failed or aborted. Check batch/batch_script_log/")
    return 1


if __name__ == "__main__":
    sys.exit(main())
