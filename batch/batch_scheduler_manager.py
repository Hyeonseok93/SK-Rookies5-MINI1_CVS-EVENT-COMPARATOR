from __future__ import annotations

import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from loguru import logger
from datetime import datetime
import pytz
import time
import os

# 경로 설정
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_FILE_DIR)
SCHEDULER_LOG_DIR = os.path.join(PROJECT_ROOT, "batch", "batch_scheduler_log")


def get_kst_now():
    kst = pytz.timezone('Asia/Seoul')
    return datetime.now(kst).replace(tzinfo=None)


def _resolve_target_year_month(year: int | None = None, month: int | None = None):
    """Compute target year/month at call time (not at job registration)."""
    now = get_kst_now()
    return (year if year is not None else now.year), (month if month is not None else now.month)


def run_monthly_batch_task(year: int = None, month: int = None, batch_name: str = None,
                           max_retry: int = 3, dry_run: bool = False,
                           use_current_month: bool = False):
    """
    지정된 연/월의 배치를 실행합니다.

    use_current_month=True 이면 실행 시점의 연/월을 사용합니다 (월간 cron용).
    """
    if use_current_month or year is None or month is None:
        year, month = _resolve_target_year_month(year, month)

    batch_name = batch_name or f"{year}년 {month}월"
    run_time = get_kst_now().replace(day=1, hour=0, minute=30, second=0, microsecond=0)
    # Keep filename stamp aligned with target month while using real clock for uniqueness
    now = get_kst_now()
    run_time = run_time.replace(year=year, month=month, hour=now.hour, minute=now.minute, second=now.second)
    logger.info(f"🚀 [{batch_name}] 스케줄러에 의해 배치 루틴 호출됨 (target={year}-{month:02d})")

    attempt = 0
    success = False
    while attempt <= max_retry and not success:
        try:
            from batch.script.crawl_batch_script import get_next_month_data_batch
            ok = get_next_month_data_batch(year=year, month=month, dry_run=dry_run, run_time=run_time)
            if not ok:
                raise RuntimeError("배치 후처리 조건 미충족 (크롤 실패 또는 데이터 부족)")
            logger.success(f"✅ [{batch_name}] 배치 완료 - {get_kst_now().strftime('%H:%M:%S')}")
            success = True
        except Exception as e:
            attempt += 1
            logger.error(f"❌ [{batch_name}] 배치 오류: {e}")
            if attempt <= max_retry:
                logger.info(f"🔁 재시도 {attempt}/{max_retry}회 진행 중...")
                time.sleep(5)
            else:
                logger.error(f"❌ [{batch_name}] 모든 재시도 실패")


class SchedulerManager:
    """여러 개의 배치 작업을 관리하는 스케줄러"""

    def __init__(self):
        os.makedirs(SCHEDULER_LOG_DIR, exist_ok=True)

        log_file_path = os.path.join(SCHEDULER_LOG_DIR, "scheduler_{time:YYYY-MM-DD}.log")

        # 기본 핸들러 제거 후 스케줄러 전용 로그 설정 적용
        logger.remove()
        logger.add(
            log_file_path,
            rotation="00:00",
            retention="30 days",
            level="INFO",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            enqueue=True  # 멀티쓰레드 안전성 확보
        )

        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='Asia/Seoul'
        )
        self.job_configs = {}  # job_id별 설정 저장

    def add_job(self, day: int, hour: int, minute: int, year: int = None, month: int = None,
                batch_name: str = None, job_id: str = None, dry_run: bool = False):
        """새로운 배치 작업을 등록 (이미 존재하면 건너뜀)

        year/month가 None이면 매 실행 시점의 현재 연/월을 사용합니다.
        """
        now = get_kst_now()
        fixed_target = year is not None and month is not None
        use_current_month = not fixed_target
        label = batch_name or ("정기 월간 데이터 최신화 배치" if use_current_month else f"{year}년 {month}월")
        job_id = job_id or (
            f"batch_monthly_{day}_{hour:02d}{minute:02d}"
            if use_current_month
            else f"batch_{year}_{month}_{day}_{hour}_{minute}"
        )

        if self.scheduler.get_job(job_id):
            return

        log_file_path = os.path.join(SCHEDULER_LOG_DIR, f"scheduler_{now.strftime('%Y-%m-%d')}.log")
        already_logged = False

        if os.path.exists(log_file_path):
            with open(log_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if f"✅ 배치 등록 완료: {job_id}" in content:
                    already_logged = True

        self.job_configs[job_id] = {
            'day': day, 'hour': hour, 'minute': minute,
            'year': year, 'month': month,
            'batch_name': label, 'dry_run': dry_run,
            'use_current_month': use_current_month,
        }

        # Do NOT bake year/month into kwargs when using rolling monthly schedule
        kwargs = {
            'batch_name': label,
            'dry_run': dry_run,
            'use_current_month': use_current_month,
        }
        if fixed_target:
            kwargs['year'] = year
            kwargs['month'] = month

        self.scheduler.add_job(
            run_monthly_batch_task,
            'cron',
            day=day,
            hour=hour,
            minute=minute,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs,
        )

        if not already_logged:
            logger.info(f"✅ 배치 등록 완료: {job_id}")
            target_desc = "실행 시점 현재 연/월" if use_current_month else f"{year}-{month:02d}"
            logger.info(f"   매월 {day}일 {hour:02d}:{minute:02d} - [{label}] target={target_desc} (dry_run={dry_run})")

    def remove_job(self, job_id: str):
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            if job_id in self.job_configs:
                del self.job_configs[job_id]
            logger.info(f"🗑️  job 제거: {job_id}")

    def start(self):
        """스케줄러를 시작합니다 (오늘 이미 시작된 로그가 있으면 생략)"""
        if not self.scheduler.running:
            self.scheduler.start()

            now = datetime.now()
            already_started_logged = False
            if os.path.exists(SCHEDULER_LOG_DIR):
                for file in os.listdir(SCHEDULER_LOG_DIR):
                    if file.startswith(f"scheduler_{now.strftime('%Y-%m-%d')}") and file.endswith(".log"):
                        try:
                            with open(os.path.join(SCHEDULER_LOG_DIR, file), "r", encoding="utf-8") as f:
                                if "🟢 스케줄러 시작됨" in f.read():
                                    already_started_logged = True
                                    break
                        except Exception:
                            pass

            if not already_started_logged:
                logger.info("🟢 스케줄러 시작됨")
        else:
            pass

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 스케줄러 중지됨")

    def get_jobs(self):
        jobs = self.scheduler.get_jobs()
        job_details = []
        for job in jobs:
            job_details.append({
                "id": job.id,
                "trigger": str(job.trigger),
                "next_run": job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else "N/A",
                "config": self.job_configs.get(job.id, {})
            })
        return {
            "is_running": self.scheduler.running,
            "total_jobs": len(job_details),
            "jobs": job_details
        }

    def trigger_now(self, job_id: str):
        job = self.scheduler.get_job(job_id)
        if job:
            logger.info(f"⚡ [테스트] Job {job_id} 즉시 실행 시작")
            job.func(**job.kwargs)
            return True
        return False


@st.cache_resource
def get_scheduler_manager():
    """Streamlit 캐시를 사용해 전역 스케줄러 인스턴스를 반환"""
    manager = SchedulerManager()
    manager.start()
    return manager
