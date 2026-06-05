# 🏪 CVS Event Comparator (편의점 행사 상품 통합 대시보드)

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=Selenium&logoColor=white" />
  <img src="https://img.shields.io/badge/BeautifulSoup-Orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Llama_3.3_(Groq)-F34F29?style=for-the-badge&logo=groq&logoColor=white" />
  <img src="https://img.shields.io/badge/Folium-77B829?style=for-the-badge&logo=leaflet&logoColor=white" />
</div>

<br />

**CVS Event Comparator**는 국내 주요 편의점 4사(CU, GS25, 7-Eleven, emart24)의 행사 상품 데이터를 수집, 정제, 카테고리화하여 스마트한 소비를 돕는 **실시간 행사 통합 분석 및 추천 대시보드**입니다.

단순 정보 조회를 넘어 **AI 기반 추천 챗봇, 예산 맞춤형 조합 생성, 다이어트 및 야식 등 테마별 추천 가이드, 편의점 지도 서비스 및 게이미피케이션 요소**까지 결합한 종합 편의점 플랫폼 서비스입니다.

---

## 🌟 프로젝트 핵심 차별화 포인트 (Portfolio Highlights)

1. **자동화된 데이터 파이프라인 (Data Pipeline & Batch Scheduler)**
   - Selenium & BeautifulSoup 기반의 개별 크롤러 탑재.
   - `APScheduler`를 활용하여 매월/매주 주기적으로 편의점 4사의 행사 상품 목록을 자동으로 갱신하고 클렌징하는 배치 스크립트 구축.
2. **AI RAG 기반 편의점 추천 챗봇 (Groq Llama-3 Chatbot)**
   - 사용자의 입력 키워드를 기반으로 상품 데이터베이스(CSV)를 필터링하여 컨텍스트(Context)로 전달하는 실시간 룰 기반 챗봇 서비스 설계.
   - 자연스러운 한국어로 상품 정보 및 페어링 팁을 알려주는 대화형 에이전트 구현.
3. **스마트 예산 조합 알고리즘 (Greedy & Dynamic Combination)**
   - 사용자가 입력한 예산에 맞추어 영양과 만족도를 고려한 최적의 1+1, 2+1 행사 상품 조합을 계산해 제안하는 기능 제공.
4. **위치 기반 편의점 지도 서비스 (Geospatial Visualization)**
   - `Folium`과 `streamlit-folium`을 연동하여 편의점 브랜드별 마커 클러스터링 지도 시각화.
5. **인터랙티브 UX & 다크모드/글래스모피즘 테마**
   - CSS 기반의 미려한 카드 UI 스타일링, 흐르는 배너 및 럭키박스, 잭팟 슬롯머신 등 사용자 참여를 유도하는 게이미피케이션 적용.

---

## 🏗️ 시스템 아키텍처 (System Architecture)

```mermaid
graph TD
    %% Scraper Layer
    subgraph Crawling & Scraping
        CU[CU Scraper] -->|Raw Data| CU_CSV[(CU Raw CSV)]
        GS[GS25 Scraper] -->|Raw Data| GS_CSV[(GS25 Raw CSV)]
        SE[7-Eleven Scraper] -->|Raw Data| SE_CSV[(7-Eleven Raw CSV)]
        EM[emart24 Scraper] -->|Raw Data| EM_CSV[(emart24 Raw CSV)]
    end

    %% Batch / Clean Layer
    subgraph Data Pipeline
        Scheduler[APScheduler Manager] -->|Trigger| Run[crawl_batch_script.py]
        Run --> Crawling & Scraping
        CU_CSV & GS_CSV & SE_CSV & EM_CSV -->|Data Cleansing| Cleaner[data_cleaner.py]
        Cleaner -->|Formatted Raw| CleanCSV[(cleaned_data.csv)]
        CleanCSV -->|Text-based NLP Classification| Categorizer[data_categorize.py]
        Categorizer -->|Final Database| FinalCSV[(categorized_data.csv)]
    end

    %% Application Layer
    subgraph Dashboard Application (Streamlit)
        FinalCSV -->|Load| Main[app.py / st.navigation]

        %% Features
        Main --> Home[00_home: 추천 & 실시간 뉴스]
        Main --> Summary[01_overall_summary: 전체 요약 & 필터]
        Main --> Compare[02_brand_comparison: 브랜드 비교 & Plotly 시각화]
        Main --> BestVal[03_best_value: 가성비 TOP 50]
        Main --> Budget[04_budget_combination: 예산 맞춤 조합 생성]
        Main --> Diet[05_diet_guide: 식단 & 다이어트 가이드]
        Main --> Night[06_night_snack_guide: 야식 & 안주 가이드]
        Main --> Map[07_convenience_store_map: 편의점 지도]
        Main --> Game[08_random_picker & 09_jackpot_game]

        %% Chatbot
        Main --> Chatbot[utils/chatbot.py: Groq Llama-3 RAG Chat]
        FinalCSV -->|Keyword RAG Context| Chatbot
    end

    %% Styling
    classDef styleClass fill:#1c2128,stroke:#30363d,stroke-width:2px,color:#fff;
    class CU,GS,SE,EM,CU_CSV,GS_CSV,SE_CSV,EM_CSV,Scheduler,Run,Cleaner,CleanCSV,Categorizer,FinalCSV,Main,Home,Summary,Compare,BestVal,Budget,Diet,Night,Map,Game,Chatbot styleClass;
```

---

## 📂 프로젝트 구조 (Project Folder Structure)

```text
conv-dashboard/
┣━━ 📂 .devcontainer/               # 개발 환경 컨테이너화 설정 (DevContainer)
┃   ┗━━ 📄 devcontainer.json        # 클라우드/컨테이너 개발 환경 명세
┣━━ 📂 .streamlit/                  # Streamlit 설정 폴더
┃   ┗━━ 📄 config.toml              # 테마(Dark), 레이아웃 및 포트 설정
┣━━ 📂 assets/                      # 브랜드 로고 및 분석 정적 이미지
┃   ┣━━ 🖼️ logo_cu.png              # CU 브랜드 로고
┃   ┣━━ 🖼️ logo_gs25.png            # GS25 브랜드 로고
┃   ┣━━ 🖼️ logo_7eleven.png         # 세븐일레븐 브랜드 로고
┃   ┣━━ 🖼️ logo_emart24.png         # 이마트24 브랜드 로고
┃   ┣━━ 🖼️ brandname_visual.png     # 브랜드 통계 차트 이미지
┃   ┗━━ 🖼️ graph.png                # 가격 통계 분석 그래프
┣━━ 📂 batch/                       # 데이터 수집 자동화 및 스케줄러
┃   ┣━━ 📂 script/
┃   ┃   ┗━━ 📄 crawl_batch_script.py # 통합 크롤링 및 정제 실행 자동화 스크립트
┃   ┣━━ 📄 batch_scheduler_manager.py # 백그라운드 APScheduler 스케줄러 관리자
┃   ┣━━ 📄 Batach_README.md         # 배치 관리 상세 가이드
┃   ┗━━ 📄 __init__.py
┣━━ 📂 data/                        # 데이터 저장소 (CSV)
┃   ┣━━ 📄 CU_260224.csv            # 브랜드별 수집 원본 로우 데이터
┃   ┣━━ 📄 GS25_260224.csv
┃   ┣━━ 📄 7Eleven_260224.csv
┃   ┣━━ 📄 emart24_260224.csv
┃   ┣━━ 📄 cleaned_data.csv         # 중복 제거 및 누락치 처리 완료 데이터
┃   ┣━━ 📄 categorized_data.csv     # 최종 상품 분류 및 인덱싱이 끝난 메인 데이터
┃   ┗━━ 📄 filtered_convenience_stores.csv # 위치 기반 편의점 매장 데이터
┣━━ 📂 pages/                       # 대시보드 핵심 기능 웹 페이지 모듈
┃   ┣━━ 📄 00_home.py               # 실시간 추천 핫딜, 꿀팁봇, 뉴스 피드 메인보드
┃   ┣━━ 📄 01_overall_summary.py    # 이미지 카드 레이아웃 기반 통합 검색/필터 페이지
┃   ┣━━ 📄 02_brand_comparison.py   # 브랜드별 상품 구성, 행사 규모 시각화 비교
┃   ┣━━ 📄 03_best_value.py         # 실질 할인율/효율 기준 TOP 50 랭킹 정보
┃   ┣━━ 📄 04_budget_combination.py # 예산 조건 충족 최적 번들 조합 구성기
┃   ┣━━ 📄 05_diet_guide.py         # 닭가슴살, 제로 탄산 등 다이어터 특화 상품 정보
┃   ┣━━ 📄 06_night_snack_guide.py  # 혼술 안주, 새벽 야식 매칭 추천 서비스
┃   ┣━━ 📄 07_convenience_store_map.py # 전국 편의점 위치 시각화 (Folium 지리 공간 지도)
┃   ┣━━ 📄 08_random_picker.py      # 결정 장애 해결용 럭키박스 뽑기
┃   ┣━━ 📄 09_jackpot_game.py       # 재미 요소를 결합한 상품 매칭 슬롯머신
┃   ┗━━ 📄 10_event_news.py         # 편의점 업계 최신 마케팅 및 이벤트 동향 소식
┣━━ 📂 scraper/                     # 편의점 4사 전용 크롤링 라이브러리
┃   ┣━━ 📄 cu_scraper.py            # CU 이벤트 크롤러 (Ajax Requests)
┃   ┣━━ 📄 gs25_scraper.py          # GS25 이벤트 크롤러 (Selenium)
┃   ┣━━ 📄 seven_eleven_scraper.py  # 7-Eleven 이벤트 크롤러 (BeautifulSoup)
┃   ┣━━ 📄 emart24_scraper.py       # emart24 이벤트 크롤러 (BeautifulSoup)
┃   ┣━━ 📄 event_news_scraper.py    # 브랜드별 보도자료/뉴스 연동용 스크래퍼
┃   ┗━━ 📄 __init__.py
┣━━ 📂 test/                        # 스케줄러 기능 검증 및 개별 스크립트 테스트 폴더
┣━━ 📂 utils/                       # 공통 유틸리티 및 AI/시각화 모듈
┃   ┣━━ 📄 data_cleaner.py          # 수집 데이터 텍스트 정제 및 중복 제어
┃   ┣━━ 📄 data_categorize.py       # 상품명 키워드 패턴 매칭 기반 카테고리 분류 엔진
┃   ┣━━ 📄 chatbot.py               # Groq API 활용 LLM Chatbot 로직
┃   ┣━━ 📄 brandname_visual.py      # 브랜드 통계 차트 생성
┃   ┣━━ 📄 graph.py                 # 가격 통계 분석 시각화
┃   ┣━━ 📄 cart.py                  # 장바구니/장바구니 찜하기 데이터 유지 관리
┃   ┣━━ 📄 news_scraper.py          # 네이버/다음 뉴스 포털 크롤링 래퍼
┃   ┗━━ 📄 __init__.py
┣━━ 📄 app.py                       # 메인 컨트롤러 및 사이드바 내비게이션 진입점
┣━━ 📄 style.css                    # 다크 모드 맞춤 커스텀 CSS (Glassmorphism 적용)
┣━━ 📄 requirements.txt             # 개발 패키지 명세서
┗━━ 📄 .gitignore                   # Git 제외 파일 관리 가이드
```

---

## 🛠️ 주요 기술 스택 (Tech Stack)

### **Frontend & Dashboard UI**

- **Streamlit**: 다중 페이지 구조(`st.navigation`) 및 상태 관리(`st.session_state`)를 활용한 고기능 SPA 구현.
- **Custom CSS (style.css)**: 다크 모드에 최적화된 글래스모피즘 테마 및 고유 컴포넌트 커스터마이징.
- **Plotly**: 반응형 데이터 통계 차트 및 브랜드별 규모 시각화.
- **Folium & Streamlit-Folium**: 카카오/VWorld API 연동 없이 마커 클러스터링을 적용한 지도 서비스 구현.

### **Backend & Data Pipeline**

- **Selenium**: 동적 로딩(Ajax) 기반의 GS25 등 사이트 스크래핑 제어.
- **BeautifulSoup4 & Requests**: 정적 페이지의 고속 데이터 스크래핑.
- **Pandas**: 대용량 상품 데이터의 전처리, 중복 제어 및 다차원 통계 연산.
- **APScheduler**: 백그라운드 데몬 형태의 자동 정기 스크래핑 태스크 스케줄링.
- **Loguru**: 직관적인 로그 포맷팅 및 디버깅 시스템 구축.

### **Artificial Intelligence**

- **Groq Cloud API**: Llama-3.3-70B 모델을 탑재하여 초고속 LLM 응답 구현.
- **Local RAG (Retrieval-Augmented Generation)**: 사용자의 질문 맥락에 적합한 데이터프레임 내의 상품 목록(20여 개)을 동적으로 추출하여 시스템 프롬프트에 실시간 주입.

---

## ⚙️ 설치 및 로컬 실행 방법

### 1. 레포지토리 클론 및 폴더 이동

```bash
git clone https://github.com/Hyeonseok93/SK-Rookies5-MINI1_CVS-EVENT-COMPARATOR.git
cd SK-Rookies5-MINI1_CVS-EVENT-COMPARATOR
```

### 2. 가상환경 구축 및 패키지 설치

```bash
python -m venv venv
source venv/Scripts/activate  # Windows (CMD/PowerShell)
# 또는
source venv/bin/activate      # Mac/Linux

pip install -r requirements.txt
```

### 3. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 Groq API 키를 설정합니다. (챗봇 기능을 사용하지 않으려면 생략 가능)

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. 대시보드 애플리케이션 실행

```bash
streamlit run app.py
```

### 5. 수동 데이터 크롤링 및 업데이트 (선택 사항)

스케줄러가 백그라운드에서 동작하지만, 데이터를 즉시 업데이트하고 싶다면 아래 명령어를 순서대로 실행합니다:

```bash
# 편의점 4사 데이터 스크래핑 실행
python scraper/cu_scraper.py
python scraper/gs25_scraper.py
python scraper/seven_eleven_scraper.py
python scraper/emart24_scraper.py

# 데이터 정제 및 카테고리 자동 분류 적용
python utils/data_cleaner.py
python utils/data_categorize.py
```

---

## 🎨 주요 화면 가이드 (Features Walkthrough)

| 🏠 메인보드 (`00_home.py`)                                                                | 🔍 전체 요약 (`01_overall_summary.py`)                                           |
| ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 맞춤형 핫딜 배너 스크롤러, 시간대별 지능형 메뉴 추천, 편의점 업계 최신 보도자료 피드 탑재 | 정교한 다중 선택 필터(브랜드, 행사 유형, 카테고리) 및 텍스트 통합 검색 엔진 제공 |

| 📊 브랜드 비교 (`02_brand_comparison.py`)                                    | 🍱 예산 맞춤 꿀조합 (`04_budget_combination.py`)                      |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Plotly를 이용한 브랜드별 행사 상품 점유율 분석 및 평균 단가 비교 그래프 제공 | 예산 맞춤 알고리즘을 사용해 최대 효율을 내는 최적 번들 상품 조합 추천 |

| 📍 편의점 지도 (`07_convenience_store_map.py`)                                | 💬 AI 꿀팁봇 (`utils/chatbot.py`)                                       |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 마커 클러스터 기능을 활용한 사용자 위치 기반 주변 4대 편의점 위치 매핑 시각화 | Groq Llama-3 기반으로 실시간 맥락 파악 및 상품 매칭, 페어링 가이드 제공 |

---
