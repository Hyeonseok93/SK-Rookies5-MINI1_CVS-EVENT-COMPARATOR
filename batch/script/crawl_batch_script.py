import os
import sys
import importlib
from datetime import datetime

# 최상위 폴더 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# 로그 저장 기본 경로 (루트/batch/batch_script)
LOG_BASE_DIR = os.path.join(PROJECT_ROOT, 'batch', 'batch_script_log')

REQUIRED_BRANDS = ('7Eleven', 'CU', 'GS25', 'emart24')


def get_log_path(run_time: datetime):
    """실행 시점(run_time)을 기준으로 단 하나의 로그 파일 경로를 생성"""

    yy = run_time.year % 100
    m = run_time.month
    dirname = f"{yy}_{m}"
    dirpath = os.path.join(LOG_BASE_DIR, dirname)

    # 폴더는 여기서 딱 한 번 생성
    os.makedirs(dirpath, exist_ok=True)

    fname = run_time.strftime('batch_script_%Y%m%d_%H%M%S.log')
    return os.path.join(dirpath, fname)


def write_log(msg: str, run_time: datetime):
    """전달받은 run_time 기준의 로그 파일에 메시지 추가"""
    path = get_log_path(run_time)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    line = f"[{timestamp} KST] {msg}\n"
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line)
    print(line, end='')


def make_datetime(fixed_dt: datetime):
    """스크래퍼 내부의 datetime.now()를 배치 시점으로 고정"""
    if fixed_dt is None:
        fixed_dt = datetime.now()

    class DateTime:
        @staticmethod
        def now():
            return fixed_dt

    return DateTime


def _yymm_prefix(year: int, month: int) -> str:
    return f"{year % 100:02d}{month:02d}"


def _brand_csv_ready(data_dir: str, brand: str, yymm: str) -> bool:
    """True if at least one brand CSV with the file-name YYMM prefix exists and is non-empty."""
    prefix = f"{brand}_{yymm}"
    try:
        for name in os.listdir(data_dir):
            if name.startswith(prefix) and name.endswith('.csv'):
                path = os.path.join(data_dir, name)
                if os.path.getsize(path) > 0:
                    return True
    except FileNotFoundError:
        return False
    return False


def run_daily_data_batch(year: int, month: int, run_time: datetime, dry_run: bool = False) -> bool:
    """
    일간 데이터 최신화 배치 (크롤 → 정제 → 분류 → 뉴스).

    year/month는 스케줄 주기가 아니라 raw CSV 파일명 접두사(YYMM)용입니다.
    기본(스케줄러)은 실행 당일 KST의 연·월을 넣습니다.
    브랜드 크롤이 하나라도 실패하면 clean/categorize를 건너뛰고 False를 반환합니다.
    """
    # 현재 작업 디렉토리를 프로젝트 루트로 변경
    os.chdir(PROJECT_ROOT)

    data_dir = os.path.join(PROJECT_ROOT, 'data')

    os.makedirs(data_dir, exist_ok=True)

    # 환경변수로 data 폴더 경로 전달
    os.environ['DATA_DIR'] = data_dir

    yymm = _yymm_prefix(year, month)

    # 2. 시작 로그 기록
    write_log('=== BATCH START ===', run_time)
    write_log(
        f'File stamp period: {year}-{month:02d} (yymm={yymm}) | Run time: {run_time.strftime("%H:%M:%S")}',
        run_time,
    )
    write_log(f'Data directory: {data_dir}', run_time)

    # dry-run: 크롤/정제/분류/뉴스 전부 스킵 (카탈로그 오염 방지)
    if dry_run:
        write_log('Dry run enabled: Skipping crawl, clean, categorize, and news.', run_time)
        write_log('=== BATCH DRY-RUN COMPLETE ===', run_time)
        return True

    # 파일명 스탬프 = 연월 접두사 + 실행일 (ready 체크의 yymm prefix와 일치)
    file_stamp = f"{yymm}{run_time.day:02d}"
    os.environ["BATCH_FILE_STAMP"] = file_stamp
    write_log(f'BATCH_FILE_STAMP={file_stamp}', run_time)

    # 스크래퍼 datetime 패치 (start_ts용) + base 모듈도 동일 패치
    mods = [
        "scraper.base",
        "scraper.seven_eleven_scraper",
        "scraper.cu_scraper",
        "scraper.gs25_scraper",
        "scraper.emart24_scraper",
    ]
    time_patch = make_datetime(run_time)

    for m in mods:
        try:
            mod = importlib.import_module(m)
            setattr(mod, "datetime", time_patch)
            write_log(f"Module patched: {m}", run_time)
        except Exception as e:
            write_log(f"Failed to patch {m}: {e}", run_time)

    crawl_ok = True
    crawl_results = {}

    crawlers = [
        ("7Eleven", "scraper.seven_eleven_scraper", "crawl_7eleven", None),
        ("CU", "scraper.cu_scraper", "CUCrawler", "run"),
        ("GS25", "scraper.gs25_scraper", "scrape_gs25_event_goods", None),
        ("emart24", "scraper.emart24_scraper", "Emart24Scraper", "run"),
    ]

    for brand, module_name, attr, method in crawlers:
        try:
            mod = importlib.import_module(module_name)
            target = getattr(mod, attr)
            if method:
                getattr(target(), method)()
            else:
                target()
            ready = _brand_csv_ready(data_dir, brand, yymm)
            crawl_results[brand] = ready
            if ready:
                write_log(f"Finished: {brand}", run_time)
            else:
                crawl_ok = False
                write_log(f"{brand} finished but no {brand}_{yymm}*.csv found", run_time)
        except Exception as e:
            crawl_ok = False
            crawl_results[brand] = False
            write_log(f"{brand} failed: {e}", run_time)

    write_log(f"Crawl summary: {crawl_results}", run_time)

    if not crawl_ok:
        write_log(
            "SKIP post-process: one or more brand crawls failed. Keeping existing cleaned/categorized data.",
            run_time,
        )
        write_log("=== BATCH ABORTED (incomplete crawl) ===", run_time)
        return False

    try:
        from utils.data_cleaner_batch import clean_and_merge_batch

        cleaned = clean_and_merge_batch(year=year, month=month)
        if cleaned is None:
            write_log("data_cleaner produced no output — skip categorize", run_time)
            write_log("=== BATCH ABORTED (clean failed) ===", run_time)
            return False
        write_log("Finished: data_cleaner", run_time)

        from utils.data_categorize import run_categorization

        run_categorization()
        write_log("Finished: data_categorize", run_time)
    except Exception as e:
        write_log(f"Post-processing failed: {e}", run_time)
        write_log("=== BATCH ABORTED (post-process error) ===", run_time)
        return False

    # 행사 뉴스 — 실패해도 상품 카탈로그 배치는 성공으로 유지
    try:
        from scraper.event_news_scraper import scrape_official_events

        scrape_official_events()
        write_log("Finished: event_news_scraper", run_time)
    except Exception as e:
        write_log(f"event_news_scraper failed (non-fatal): {e}", run_time)

    write_log("=== BATCH COMPLETE ===", run_time)
    return True
