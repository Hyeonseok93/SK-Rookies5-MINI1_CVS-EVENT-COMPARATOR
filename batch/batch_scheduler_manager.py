from __future__ import annotations

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

_manager = None  # SchedulerManager singleton


def get_kst_now():
    kst = pytz.timezone("Asia/Seoul")
    return datetime.now(kst).replace(tzinfo=None)


def _resolve_file_stamp_year_month(year: int | None = None, month: int | None = None):
    """연/월은 cron 주기가 아니라 raw CSV 파일명 접두사(YYMM)용. 기본은 실행 시점 KST."""
    now = get_kst_now()
    return (year if year is not None else now.year), (month if month is not None else now.month)


def run_daily_batch_task(
    year: int = None,
    month: int = None,
    batch_name: str = None,
    max_retry: int = 3,
    dry_run: bool = False,
    use_run_date: bool = False,
):
    """
    일간 데이터 최신화 배치를 실행합니다.

    use_run_date=True 이면 실행 시점의 연/월을 파일 스탬프(YYMM)로 사용합니다 (매일 cron용).
    year/month를 고정 넘기면 그 접두사로 파일을 맞춥니다.
    """
    if use_run_date or year is None or month is None:
        year, month = _resolve_file_stamp_year_month(year, month)

    batch_name = batch_name or f"일간 배치 ({year}-{month:02d})"
    run_time = get_kst_now().replace(day=1, hour=0, minute=30, second=0, microsecond=0)
    now = get_kst_now()
    run_time = run_time.replace(year=year, month=month, hour=now.hour, minute=now.minute, second=now.second)
    logger.info(f"🚀 [{batch_name}] 스케줄러에 의해 배치 루틴 호출됨 (file_stamp={year}-{month:02d})")

    attempt = 0
    success = False
    while attempt <= max_retry and not success:
        try:
            from batch.script.crawl_batch_script import run_daily_data_batch

            ok = run_daily_data_batch(year=year, month=month, dry_run=dry_run, run_time=run_time)
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
    """여러 개의 배치 작업을 관리하는 스케줄러 (Streamlit과 독립)."""

    def __init__(self):
        os.makedirs(SCHEDULER_LOG_DIR, exist_ok=True)

        log_file_path = os.path.join(SCHEDULER_LOG_DIR, "scheduler_{time:YYYY-MM-DD}.log")
        # 전역 핸들러를 지우지 않고 파일 sink만 추가 (다른 모듈 logger 보존)
        logger.add(
            log_file_path,
            rotation="00:00",
            retention="30 days",
            level="INFO",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            enqueue=True,
        )

        self.scheduler = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            timezone="Asia/Seoul",
        )
        self.job_configs = {}

    def add_job(
        self,
        hour: int,
        minute: int,
        day: int | None = None,
        year: int = None,
        month: int = None,
        batch_name: str = None,
        job_id: str = None,
        dry_run: bool = False,
    ):
        """새로운 배치 작업을 등록 (이미 존재하면 건너뜀).

        day가 None이면 매일 실행합니다.
        year/month가 None이면 매 실행 시점의 현재 연/월을 파일 스탬프(YYMM)로 사용합니다.
        """
        now = get_kst_now()
        fixed_stamp = year is not None and month is not None
        use_run_date = not fixed_stamp
        daily = day is None
        label = batch_name or (
            "정기 일간 데이터 최신화 배치" if use_run_date else f"파일스탬프 {year}-{month:02d}"
        )
        job_id = job_id or (
            f"batch_daily_{hour:02d}{minute:02d}"
            if daily and use_run_date
            else f"batch_dom_{day}_{hour:02d}{minute:02d}"
            if use_run_date
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
            "day": day,
            "hour": hour,
            "minute": minute,
            "year": year,
            "month": month,
            "batch_name": label,
            "dry_run": dry_run,
            "use_run_date": use_run_date,
            "daily": daily,
        }

        kwargs = {
            "batch_name": label,
            "dry_run": dry_run,
            "use_run_date": use_run_date,
        }
        if fixed_stamp:
            kwargs["year"] = year
            kwargs["month"] = month

        cron_kwargs = {"hour": hour, "minute": minute}
        if not daily:
            cron_kwargs["day"] = day

        self.scheduler.add_job(
            run_daily_batch_task,
            "cron",
            id=job_id,
            replace_existing=True,
            kwargs=kwargs,
            **cron_kwargs,
        )

        if not already_logged:
            logger.info(f"✅ 배치 등록 완료: {job_id}")
            stamp_desc = "실행 시점 연/월 (파일 스탬프)" if use_run_date else f"고정 스탬프 {year}-{month:02d}"
            when = f"매일 {hour:02d}:{minute:02d}" if daily else f"매월 {day}일 {hour:02d}:{minute:02d}"
            logger.info(f"   {when} - [{label}] stamp={stamp_desc} (dry_run={dry_run})")

    def remove_job(self, job_id: str):
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            if job_id in self.job_configs:
                del self.job_configs[job_id]
            logger.info(f"🗑️  job 제거: {job_id}")

    def start(self):
        """스케줄러를 시작합니다 (오늘 이미 시작된 로그가 있으면 생략)."""
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

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 스케줄러 중지됨")

    def get_jobs(self):
        jobs = self.scheduler.get_jobs()
        job_details = []
        for job in jobs:
            job_details.append(
                {
                    "id": job.id,
                    "trigger": str(job.trigger),
                    "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A",
                    "config": self.job_configs.get(job.id, {}),
                }
            )
        return {
            "is_running": self.scheduler.running,
            "total_jobs": len(job_details),
            "jobs": job_details,
        }

    def trigger_now(self, job_id: str):
        job = self.scheduler.get_job(job_id)
        if job:
            logger.info(f"⚡ [테스트] Job {job_id} 즉시 실행 시작")
            job.func(**job.kwargs)
            return True
        return False


def get_scheduler_manager() -> SchedulerManager:
    """프로세스 전역 싱글톤 (Streamlit cache 없음)."""
    global _manager
    if _manager is None:
        _manager = SchedulerManager()
        _manager.start()
    return _manager
