# 리팩토링 상세 보고서

> 작성일: 2026-07-13  
> 대상 저장소: `SK-Rookies5-MINI1_CVS-EVENT-COMPARATOR`  
> 기준 브랜치: `main` (원본 보존 브랜치: `original`)  
> 변경량(대략): +931 / −1475 (순감 중심 정리)

---

## 1. 배경과 목표

코드 전반 점검 결과, 기능 범위는 넓지만 아래 문제가 반복적으로 확인되었다.

1. **배치 파이프라인 Critical 결함** — 월 고정, YYMM 미필터, 실패 후 덮어쓰기
2. **페이지 복붙 스파게티** — `get_brand_color`, 데이터 로드, 필터, 상품카드, CSS 주입 중복
3. **Streamlit / 웹 안티패턴** — 자식 `set_page_config`, Popover CSS 충돌, XSS
4. **경로·브랜드·죽은 코드** — CWD 의존, EN/KR 혼재, `cart.py` orphan 블록

이번 작업은 **Critical → 공통 모듈 → Streamlit/보안 → 정리** 순으로 전부 반영했다.

---

## 2. Critical: 배치 파이프라인

### 2.1 year/month 고정 버그 (`batch/batch_scheduler_manager.py`)

**이전**

- `add_job()` 시점에 `datetime.now()`로 year/month를 계산해 cron `kwargs`에 박아 넣음
- 앱이 오래 떠 있으면 매월 cron이 돌아도 **등록 당시 달**로 배치가 호출됨

**이후**

- `year`/`month`가 `None`이면 `use_current_month=True`
- 실제 실행 시 `_resolve_target_year_month()`로 **KST 현재 연/월** 계산
- 고정 타깃이 필요한 경우에만 kwargs에 year/month를 명시

관련 함수:

- `run_monthly_batch_task(..., use_current_month=False)`
- `SchedulerManager.add_job(...)`

### 2.2 cleaner YYMM 미필터 (`utils/data_cleaner_batch.py`)

**이전**

- 로그에만 `current_target = %y%m` 기록
- 실제로는 브랜드명이 들어간 CSV를 **전부** merge → 과거 달 데이터 혼입

**이후**

- `_latest_per_brand(files, yymm)` 도입
- 브랜드(CU / GS25 / 7Eleven / emart24)마다:
  - `_{yymm}` 포함 파일이 있으면 그중 사용
  - 없으면 **최신 mtime 파일 1개**만 사용(경고 로그)
- 비상품 CSV(`official_event_news.csv`, `filtered_convenience_stores.csv` 등)는 `is_brand_raw_csv()`로 제외
- 저장은 `cleaned_data.csv.tmp` → `os.replace` 원자 교체
- `clean_and_merge_batch(year=..., month=...)` 시그니처로 배치 타깃 달 전달 가능
- 실패 시 `None` 반환

수동 cleaner(`utils/data_cleaner.py`)도 동일하게 **브랜드 raw만** 대상으로 변경.

### 2.3 크롤 실패 후 clean/categorize 진행 (`batch/script/crawl_batch_script.py`)

**이전**

- 브랜드별 try/except로 실패만 로그
- 무조건 `clean_and_merge_batch` → `run_categorization` 실행 → **불완전 카탈로그로 덮어쓰기**

**이후**

1. 브랜드별 크롤 실행
2. `_brand_csv_ready(data_dir, brand, yymm)`로 `{brand}_{yymm}*.csv` 존재·비어있지 않음 확인
3. 하나라도 실패/미생성 시:
   - post-process **스킵**
   - `=== BATCH ABORTED (incomplete crawl) ===`
   - `False` 반환 (스케줄러 재시도 가능)
4. clean이 `None`이어도 categorize 스킵 후 abort
5. 행사 뉴스 스크래퍼는 마지막에 **비치명(non-fatal)** 으로 연결

### 2.4 기타 배치/데이터 정합

| 항목 | 내용 |
|------|------|
| `DATA_DIR` env | 배치가 세팅 → `utils.paths.get_data_dir()` / `scraper.base.save_products`가 사용 |
| categorize 원자 저장 | `utils/data_categorize.py`도 `.tmp` + `os.replace` |
| 뉴스 경로 | `event_news_scraper` / `news_scraper`가 `get_data_dir()` / `data_path()` 사용 |

---

## 3. 공통 모듈 추출

### 3.1 신규 파일 목록

| 경로 | 역할 |
|------|------|
| `utils/paths.py` | `PROJECT_ROOT`, `get_data_dir()`, `categorized_path()`, `cleaned_path()`, `style_css_path()`, `is_brand_raw_csv()` |
| `utils/brand.py` | `BRAND_COLORS`, `get_brand_color()`, `normalize_brand()`, `display_brand()` |
| `utils/pricing.py` | `unit_price()`, `discount_rate()`, `discount_num()`, `pay_and_total_counts()` |
| `utils/data_loader.py` | `@st.cache_data` `load_categorized_df(...)` — 가격/행사/브랜드 정규화 + 단가 컬럼 |
| `utils/filters.py` | `render_product_filters()`, `track_recent_keyword()`, `apply_sort()`, `FilterState` |
| `utils/product_grid.py` | `product_card_html()`, `render_product_grid()`, `paginate()`, `render_pagination()` |
| `utils/html_safe.py` | `esc()`, `esc_attr()` — HTML escape |
| `utils/ui_css.py` | `inject_app_css()` — 루트 `style.css` 1회 주입 |
| `scraper/base.py` | `save_products(df, brand, ...)` — 공통 CSV 저장 |

### 3.2 페이지 쪽 적용 방식

- 로컬 `def get_brand_color` 제거 → `from utils.brand import get_brand_color`
- 로컬 `get_data` / `calc_info` 제거 → `load_categorized_df(...)`
- 공통 필터·그리드 페이지(예: `01_overall_summary`)는 filters + product_grid로 축소
- 테마/게임/지도/예산 등 **고유 로직은 유지**, 인프라만 공유

### 3.3 스크래퍼 쪽 적용

- CU / GS25 / emart24 / 7-Eleven 저장 보일러플레이트 → `save_products`
- `seven_eleven_scraper.py`에 있던 **파일 전체 이중 복제(약 73줄×2)** 제거 후 단일 구현

---

## 4. High: Streamlit / CSS / 보안

### 4.1 `st.set_page_config` 중복

- **이전**: `app.py` + 다수 `pages/*.py`에서 중복 호출 → `st.navigation` 환경에서 예외/경고 가능
- **이후**: `app.py`에만 존재. 자식 페이지 전부 제거

### 4.2 CSS 이중/오주입

- **이전**: 페이지마다 `style.css` open+inject, 예산 페이지는 존재하지 않는 `static/css/style.css` 참조
- **이후**: `app.py` → `inject_app_css()` 한 번만. 예산 페이지 잘못된 경로 블록 삭제

### 4.3 챗봇 vs 장바구니 Popover CSS 충돌

**이전**

- 둘 다 `div[data-testid="stPopover"]` 전역 스타일
- FAB(우하단)과 카트(우상단)가 서로 덮어씀

**이후**

- 챗봇: `#cvs-chatbot-anchor` 인접 형제만 스타일 (`utils/chatbot.py`)
- 장바구니: `#cvs-cart-anchor` 인접 형제만 스타일 (`utils/cart.py`)
- CSS `:has()` 셀렉터 사용 (모던 브라우저 기준)

### 4.4 XSS (unsafe_allow_html)

- CSV/스크래핑 필드(`name`, `img_url`, `title`, `link`, `brand`, `event` 등)를 HTML에 넣기 전 `esc` / `esc_attr` 적용
- 적용 위치 예: `00_home`, `03_best_value`, `04_budget_combination`, `10_event_news`, `product_grid`, cart warning 일부

### 4.5 assets

- `assets/`에 브랜드 로고 PNG가 존재함 (`logo_cu.png`, `logo_gs25.png`, `logo_7eleven.png`, `logo_emart24.png`)
- `pages/00_home.py`의 `logos` dict 경로와 일치 → 홈 브랜드 로고는 정상 표시 대상
- 점검 초기에 assets 부재로 오인했으나, 실제 파일은 저장소에 포함되어 있음

---

## 5. 정리 / 품질

| 항목 | 내용 |
|------|------|
| `utils/cart.py` | 함수 밖 orphan UI 블록(약 265줄 이후) 삭제 |
| 브랜드 정규화 | 로드 시 `7Eleven`/`세븐일레븐`, `emart24`/`이마트24` 등 canonical 통일 |
| `data_categorize` | 동일 misc 키워드 이중 `if` 제거 |
| 뉴스 배치 연동 | 월간 배치 끝에 `scrape_official_events()` (실패해도 상품 배치 성공 유지) |
| `app.py` | `categorized_path()`, `inject_app_css()` 사용 |

---

## 6. 파일별 변경 요약

### 수정 (Modified)

- `app.py`
- `batch/batch_scheduler_manager.py`
- `batch/script/crawl_batch_script.py`
- `pages/00_home.py` ~ `pages/10_event_news.py` (전 페이지)
- `scraper/cu_scraper.py`, `gs25_scraper.py`, `emart24_scraper.py`, `seven_eleven_scraper.py`, `event_news_scraper.py`
- `utils/cart.py`, `chatbot.py`, `data_categorize.py`, `data_cleaner.py`, `data_cleaner_batch.py`, `news_scraper.py`

### 신규 (Untracked → 추가)

- `utils/paths.py`, `brand.py`, `pricing.py`, `data_loader.py`, `filters.py`, `product_grid.py`, `html_safe.py`, `ui_css.py`
- `scraper/base.py`
- `docs/` 문서들

---

## 7. 의도적으로 건드리지 않은 것 / 잔여 리스크

1. **예산 조합 알고리즘 본체** (`find_best_combinations` 등) — 로직 유지, 데이터 로더/CSS/escape만 교체
2. **지도 Folium / 잭팟 / 럭키박스 게임 로직** — 고유 로직 유지
3. **Popover `:has()`** — 구형 브라우저에서 스코프가 약할 수 있음
4. **스케줄러가 Streamlit 프로세스 내부** — 멀티워커/재시작 시 MemoryJobStore 한계는 구조적으로 남음 (별도 cron/systemd 이관은 미실시)
5. **커밋/PR** — 이 문서 작성 시점 기준 로컬 변경만 존재 (요청 시 커밋)

---

## 8. 권장 검증 체크리스트

- [ ] `streamlit run app.py` 후 네비게이션·사이드바·챗봇·장바구니 동시 표시
- [ ] 전체 요약 / 가성비 / 다이어트 / 야식 필터·카드·페이지네이션
- [ ] 예산 조합 생성 + 장바구니 담기
- [ ] 행사 뉴스 페이지 HTML/링크 정상, 스크립트 삽입 문자열 escape 확인
- [ ] (가능 시) dry_run 또는 테스트 배치로 abort/성공 경로 로그 확인
- [ ] `original` 브랜치와 diff로 회귀 범위 확인

---

## 9. 관련 문서

- 대화/작업 요약: [`docs/session-summary.md`](./session-summary.md)
- 점검 캔버스(IDE): `canvases/codebase-review.canvas.tsx` (로컬 Cursor 프로젝트 경로)
