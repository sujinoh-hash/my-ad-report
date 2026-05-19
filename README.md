# 네이버 키워드 소재 분석 자동화 대시보드

## 구조
```
naver-ad-dashboard/
├── collector/
│   ├── naver_searchad.py    # 네이버 검색광고 API - 검색량 수집
│   └── naver_open_api.py    # 네이버 Open API - 블로그/카페 수집
├── analyzer/
│   └── claude_analyzer.py   # Claude AI 분석 엔진
├── dashboard/
│   └── app.py               # Streamlit 대시보드
├── data/                    # 수집된 데이터 (자동 생성)
├── .github/workflows/
│   └── daily_analysis.yml   # 매일 오전 9시 자동 실행
├── run_daily.py             # 메인 실행 스크립트
└── requirements.txt
```

## 세팅 순서

### 1. GitHub Secrets 등록
레포 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|---|---|
| `NAVER_AD_CUSTOMER_ID` | 네이버 검색광고 고객 ID |
| `NAVER_AD_ACCESS_LICENSE` | Access License |
| `NAVER_AD_SECRET_KEY` | Secret Key |
| `NAVER_CLIENT_ID` | 네이버 Open API Client ID |
| `NAVER_CLIENT_SECRET` | 네이버 Open API Client Secret |
| `ANTHROPIC_API_KEY` | Claude API Key |

### 2. Streamlit Cloud 배포
1. [streamlit.io/cloud](https://streamlit.io/cloud) 접속
2. GitHub 레포 연결
3. Main file: `dashboard/app.py`
4. Secrets 탭에 위 환경변수 동일하게 입력

### 3. 로컬 테스트
```bash
pip install -r requirements.txt

# 환경변수 설정 후
python run_daily.py

# 대시보드 실행
streamlit run dashboard/app.py
```

### 4. 키워드 변경
`run_daily.py` 상단 `TARGET_KEYWORDS` 리스트 수정

## 실행 주기
- GitHub Actions: 매일 KST 09:00 자동 실행
- 결과는 `data/` 폴더에 날짜별로 저장
- `data/latest.json` → 대시보드에서 참조
