"""
Standalone batch scheduler process — run separately from Streamlit.

  python -m batch.run_scheduler
  python batch/run_scheduler.py
"""
from __future__ import annotations

import signal
import sys
import time

from batch.batch_scheduler_manager import get_scheduler_manager


def main() -> int:
    manager = get_scheduler_manager()
    # day=None → 매일 06:00 KST
    manager.add_job(
        day=None,
        hour=6,
        minute=0,
        year=None,
        month=None,
        batch_name="정기 일간 데이터 최신화 배치",
        job_id="run_daily_batch_task",
        dry_run=False,
    )

    print("Batch scheduler running (Ctrl+C to stop). Daily job: 06:00 KST")
    stop = False

    def _handle_sig(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _handle_sig)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_sig)

    while not stop:
        time.sleep(1)

    manager.stop()
    print("Scheduler stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
