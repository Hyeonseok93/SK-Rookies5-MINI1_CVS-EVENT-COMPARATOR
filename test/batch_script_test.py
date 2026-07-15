"""
일간 배치 테스트: 파일 스탬프 연·월을 2026-03으로 두고 크롤을 실행합니다.
"""
import sys, os
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from batch.script.crawl_batch_script import run_daily_data_batch
from datetime import datetime

TARGET_YEAR = 2026
TARGET_MONTH = 3

test_run_time = datetime(2026, 3, 1, 0, 30, 0)

print(f"Running daily batch test stamp={TARGET_YEAR}-{TARGET_MONTH:02d}")
run_daily_data_batch(TARGET_YEAR, TARGET_MONTH, dry_run=False, run_time=test_run_time)

log_dir = os.path.join(PROJECT_ROOT, 'batch', 'batch_script_log', f"{str(TARGET_YEAR)[-2:]}_{TARGET_MONTH}")
print('Expected log dir:', log_dir)
print('Exists:', os.path.exists(log_dir))
if os.path.exists(log_dir):
    print('Files:', os.listdir(log_dir))
else:
    print('No logs created')
