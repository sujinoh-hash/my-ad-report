name: Daily Keyword Analysis

on:
  schedule:
    - cron: '0 0 * * *'  # 매일 UTC 00:00 = KST 09:00
  workflow_dispatch:      # 수동 실행도 가능

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Python 설정
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 패키지 설치
        run: pip install -r requirements.txt

      - name: 분석 실행
        env:
          NAVER_AD_CUSTOMER_ID: ${{ secrets.NAVER_AD_CUSTOMER_ID }}
          NAVER_AD_ACCESS_LICENSE: ${{ secrets.NAVER_AD_ACCESS_LICENSE }}
          NAVER_AD_SECRET_KEY: ${{ secrets.NAVER_AD_SECRET_KEY }}
          NAVER_CLIENT_ID: ${{ secrets.NAVER_CLIENT_ID }}
          NAVER_CLIENT_SECRET: ${{ secrets.NAVER_CLIENT_SECRET }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python run_daily.py

      - name: 결과 data/ 커밋
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --staged --quiet || git commit -m "📊 Daily analysis $(date +'%Y-%m-%d')"
          git push

"""
Claude AI 분석 엔진
- 키워드 트렌드 분석
- 소비자 언어 → 소구점 분류
- 광고 카피 추천
"""
import os
import json
import anthropic
from datetime import datetime


client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def analyze_keywords(keyword_stats: list[dict]) -> dict:
    """검색량 데이터 기반 트렌드 분석"""
    stats_text = "\n".join([
        f"- {item['keyword']}: 월간 {item['monthly_total']:,}회 (PC {item['monthly_pc']:,} / 모바일 {item['monthly_mobile']:,}), 경쟁도: {item['competition']}"
        for item in sorted(keyword_stats, key=lambda x: x["monthly_total"], reverse=True)
    ])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""다음은 네이버 검색광고 키워드 검색량 데이터입니다.

{stats_text}

아래 JSON 형식으로만 분석 결과를 출력하세요. 다른 텍스트 없이:
{{
  "top_keywords": ["검색량 상위 키워드 3개"],
  "trend_summary": "2줄 이내 트렌드 요약",
  "opportunity_keywords": ["경쟁도 낮고 검색량 있는 기회 키워드 3개"],
  "peak_insight": "광고 집행 타이밍 인사이트 1줄"
}}"""
        }]
    )

    text = message.content[0].text
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def classify_consumer_language(posts: list[dict], keyword: str) -> dict:
    """블로그/카페 게시글에서 소비자 언어 분류"""
    sample = posts[:15]
    content_text = "\n".join([
        f"[{p['type']}] 제목: {p['title']} / 내용: {p['description'][:100]}"
        for p in sample
    ])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f""""{keyword}" 관련 네이버 블로그/카페 게시글입니다.

{content_text}

소비자 언어를 분석해서 아래 JSON 형식으로만 출력하세요:
{{
  "pain_points": ["페인포인트 키워드 5개"],
  "benefits": ["혜택/결과 키워드 5개"],
  "copy_materials": ["광고 카피 소재 키워드 8개"],
  "trends": ["트렌드 표현 3개"],
  "consumer_insight": "소비자 핵심 니즈 1줄 요약"
}}"""
        }]
    )

    text = message.content[0].text
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def generate_ad_copies(keyword: str, consumer_data: dict, format_type: str = "search") -> list[dict]:
    """광고 카피 자동 생성"""
    format_guide = {
        "search": "네이버 검색광고 헤드라인 (15자 이내)",
        "sns": "SNS 배너 카피 (짧고 감성적)",
        "both": "검색광고 + SNS 배너 두 가지 모두",
    }

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""키워드: "{keyword}"
소비자 인사이트: {consumer_data.get('consumer_insight', '')}
페인포인트: {', '.join(consumer_data.get('pain_points', []))}
혜택: {', '.join(consumer_data.get('benefits', []))}
트렌드: {', '.join(consumer_data.get('trends', []))}

위 데이터를 바탕으로 {format_guide[format_type]} 카피를 생성하세요.

아래 JSON 형식으로만 출력하세요:
{{
  "copies": [
    {{"headline": "카피 텍스트", "angle": "소구 방향 (상황/기능/감성 중 하나)", "note": "10자 이내 설명"}},
    {{"headline": "카피 텍스트", "angle": "소구 방향", "note": "10자 이내 설명"}},
    {{"headline": "카피 텍스트", "angle": "소구 방향", "note": "10자 이내 설명"}},
    {{"headline": "카피 텍스트", "angle": "소구 방향", "note": "10자 이내 설명"}},
    {{"headline": "카피 텍스트", "angle": "소구 방향", "note": "10자 이내 설명"}}
  ]
}}"""
        }]
    )

    text = message.content[0].text
    result = json.loads(text.replace("```json", "").replace("```", "").strip())
    return result.get("copies", [])


def run_full_analysis(keyword_stats: list[dict], blog_cafe_data: dict) -> dict:
    """전체 분석 파이프라인 실행"""
    print("📊 키워드 트렌드 분석 중...")
    trend_analysis = analyze_keywords(keyword_stats)

    results = {
        "analyzed_at": datetime.now().isoformat(),
        "trend_analysis": trend_analysis,
        "keyword_analysis": {},
    }

    keywords = list(blog_cafe_data.get("summary", {}).keys())
    for kw in keywords:
        print(f"🔍 '{kw}' 소비자 언어 분석 중...")
        posts = [
            p for p in blog_cafe_data.get("blog", []) + blog_cafe_data.get("cafe", [])
            if p["keyword"] == kw
        ]

        if not posts:
            continue

        consumer_data = classify_consumer_language(posts, kw)
        copies = generate_ad_copies(kw, consumer_data, format_type="both")

        results["keyword_analysis"][kw] = {
            "consumer_language": consumer_data,
            "ad_copies": copies,
            "post_count": len(posts),
        }

    return results


if __name__ == "__main__":
    # 테스트용 더미 데이터
    dummy_stats = [
        {"keyword": "야간러닝", "monthly_pc": 1200, "monthly_mobile": 8500, "monthly_total": 9700, "competition": "중간"},
        {"keyword": "새벽러닝", "monthly_pc": 800, "monthly_mobile": 6200, "monthly_total": 7000, "competition": "낮음"},
    ]
    print(json.dumps(analyze_keywords(dummy_stats), ensure_ascii=False, indent=2))

    
"""
네이버 검색광고 API - 키워드 검색량 수집
"""
import os
import json
import hmac
import hashlib
import base64
import time
import requests
from datetime import datetime


BASE_URL = "https://api.naver.com"


def get_signature(timestamp: str, method: str, path: str, secret_key: str) -> str:
    message = f"{timestamp}.{method}.{path}"
    sig = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(sig.digest()).decode()


def get_headers(method: str, path: str) -> dict:
    timestamp = str(int(time.time() * 1000))
    signature = get_signature(
        timestamp, method, path,
        os.environ["NAVER_AD_SECRET_KEY"]
    )
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": os.environ["NAVER_AD_ACCESS_LICENSE"],
        "X-Customer": os.environ["NAVER_AD_CUSTOMER_ID"],
        "X-Signature": signature,
    }


def get_keyword_stats(keywords: list[str]) -> list[dict]:
    """키워드 월간 검색량 조회 (PC + 모바일)"""
    path = "/keywordstool"
    url = BASE_URL + path
    headers = get_headers("GET", path)

    results = []
    # API 한 번에 최대 5개
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        params = {"hintKeywords": ",".join(batch), "showDetail": 1}
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("keywordList", []):
            results.append({
                "keyword": item["relKeyword"],
                "monthly_pc": item["monthlyPcQcCnt"],
                "monthly_mobile": item["monthlyMobileQcCnt"],
                "monthly_total": item["monthlyPcQcCnt"] + item["monthlyMobileQcCnt"],
                "competition": item.get("compIdx", ""),
                "collected_at": datetime.now().isoformat(),
            })
        time.sleep(0.5)

    return results


def get_related_keywords(keyword: str) -> list[dict]:
    """연관 키워드 조회"""
    path = "/keywordstool"
    url = BASE_URL + path
    headers = get_headers("GET", path)
    params = {"hintKeywords": keyword, "showDetail": 1}

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("keywordList", [])[:20]:
        results.append({
            "keyword": item["relKeyword"],
            "monthly_total": item["monthlyPcQcCnt"] + item["monthlyMobileQcCnt"],
            "competition": item.get("compIdx", ""),
        })

    return sorted(results, key=lambda x: x["monthly_total"], reverse=True)


if __name__ == "__main__":
    keywords = ["야간러닝", "새벽러닝", "실내러닝", "여름러닝", "러닝웨어"]
    stats = get_keyword_stats(keywords)
    print(json.dumps(stats, ensure_ascii=False, indent=2))

"""
네이버 Open API - 블로그/카페 언급량 및 소비자 언어 수집
"""
import os
import json
import requests
import re
from datetime import datetime


NAVER_API_URL = "https://openapi.naver.com/v1/search"


def get_headers() -> dict:
    return {
        "X-Naver-Client-Id": os.environ["NAVER_CLIENT_ID"],
        "X-Naver-Client-Secret": os.environ["NAVER_CLIENT_SECRET"],
    }


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).replace("&quot;", '"').replace("&amp;", "&").strip()


def search_blog(keyword: str, display: int = 20) -> list[dict]:
    """블로그 게시글 수집"""
    params = {
        "query": keyword,
        "display": display,
        "sort": "date",
    }
    resp = requests.get(
        f"{NAVER_API_URL}/blog.json",
        headers=get_headers(),
        params=params,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])

    results = []
    for item in items:
        results.append({
            "type": "blog",
            "keyword": keyword,
            "title": strip_html(item.get("title", "")),
            "description": strip_html(item.get("description", "")),
            "blogger_name": item.get("bloggername", ""),
            "post_date": item.get("postdate", ""),
            "link": item.get("link", ""),
            "collected_at": datetime.now().isoformat(),
        })
    return results


def search_cafe(keyword: str, display: int = 20) -> list[dict]:
    """카페 게시글 수집"""
    params = {
        "query": keyword,
        "display": display,
        "sort": "date",
    }
    resp = requests.get(
        f"{NAVER_API_URL}/cafearticle.json",
        headers=get_headers(),
        params=params,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])

    results = []
    for item in items:
        results.append({
            "type": "cafe",
            "keyword": keyword,
            "title": strip_html(item.get("title", "")),
            "description": strip_html(item.get("description", "")),
            "cafe_name": item.get("cafename", ""),
            "post_date": item.get("postdate", ""),
            "link": item.get("link", ""),
            "collected_at": datetime.now().isoformat(),
        })
    return results


def collect_all(keywords: list[str]) -> dict:
    """키워드 목록 전체 수집"""
    all_results = {"blog": [], "cafe": [], "summary": {}}

    for kw in keywords:
        try:
            blogs = search_blog(kw, display=10)
            cafes = search_cafe(kw, display=10)
            all_results["blog"].extend(blogs)
            all_results["cafe"].extend(cafes)
            all_results["summary"][kw] = {
                "blog_count": len(blogs),
                "cafe_count": len(cafes),
                "total": len(blogs) + len(cafes),
            }
        except Exception as e:
            print(f"[ERROR] {kw}: {e}")

    return all_results


if __name__ == "__main__":
    keywords = ["야간러닝", "새벽러닝", "실내러닝", "여름러닝웨어"]
    result = collect_all(keywords)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))

"""
Streamlit 대시보드 - 키워드 직접 입력 → 실시간 분석
"""
import json
import os
import sys
import time
import requests
import re
import hmac
import hashlib
import base64
import anthropic
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="키워드 소재 분석",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
.copy-card {
    background: white;
    border-radius: 8px;
    padding: 14px 18px;
    border-left: 4px solid #4CAF50;
    margin: 6px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.tag { padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.tag-situation { background: #fff3e0; color: #e65100; }
.tag-function  { background: #e8f5e9; color: #1b5e20; }
.tag-emotion   { background: #ede7f6; color: #4527a0; }
.kw-chip {
    display: inline-block;
    background: #f1f3f4;
    border-radius: 16px;
    padding: 4px 12px;
    margin: 3px;
    font-size: 13px;
    color: #333;
}
</style>
""", unsafe_allow_html=True)


# ── API 함수 ─────────────────────────────────────────

def get_ad_headers(method: str, path: str) -> dict:
    ts = str(int(time.time() * 1000))
    msg = f"{ts}.{method}.{path}"
    sig = hmac.new(
        os.environ["NAVER_AD_SECRET_KEY"].encode(),
        msg.encode(), hashlib.sha256
    )
    signature = base64.b64encode(sig.digest()).decode()
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": ts,
        "X-API-KEY": os.environ["NAVER_AD_ACCESS_LICENSE"],
        "X-Customer": os.environ["NAVER_AD_CUSTOMER_ID"],
        "X-Signature": signature,
    }


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).replace("&quot;", '"').replace("&amp;", "&").strip()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_keyword_stats(keywords_tuple: tuple) -> list:
    keywords = list(keywords_tuple)
    path = "/keywordstool"
    url = "https://api.naver.com" + path
    results = []
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        try:
            headers = get_ad_headers("GET", path)
            params = {"hintKeywords": ",".join(batch), "showDetail": 1}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            for item in resp.json().get("keywordList", []):
                results.append({
                    "keyword": item["relKeyword"],
                    "monthly_pc": item["monthlyPcQcCnt"],
                    "monthly_mobile": item["monthlyMobileQcCnt"],
                    "monthly_total": item["monthlyPcQcCnt"] + item["monthlyMobileQcCnt"],
                    "competition": item.get("compIdx", "-"),
                })
        except Exception as e:
            st.warning(f"검색광고 API 오류: {e}")
        time.sleep(0.3)
    return results


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_blog_cafe(keyword: str, display: int = 15) -> list:
    headers = {
        "X-Naver-Client-Id": os.environ["NAVER_CLIENT_ID"],
        "X-Naver-Client-Secret": os.environ["NAVER_CLIENT_SECRET"],
    }
    results = []
    for source in ["blog", "cafearticle"]:
        try:
            resp = requests.get(
                f"https://openapi.naver.com/v1/search/{source}.json",
                headers=headers,
                params={"query": keyword, "display": display, "sort": "date"},
                timeout=10,
            )
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                results.append({
                    "type": "블로그" if source == "blog" else "카페",
                    "title": strip_html(item.get("title", "")),
                    "description": strip_html(item.get("description", ""))[:150],
                    "date": item.get("postdate", ""),
                    "link": item.get("link", ""),
                })
        except Exception as e:
            st.warning(f"Open API 오류 ({source}): {e}")
    return results


@st.cache_data(ttl=3600, show_spinner=False)
def analyze_with_claude(keyword: str, posts_json: str, stats_json: str) -> dict:
    posts = json.loads(posts_json)
    stats = json.loads(stats_json)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    content_sample = "\n".join([
        f"[{p['type']}] {p['title']} / {p['description']}"
        for p in posts[:15]
    ])
    stats_text = "\n".join([
        f"- {s['keyword']}: 월 {s['monthly_total']:,}회 (경쟁도: {s['competition']})"
        for s in sorted(stats, key=lambda x: x["monthly_total"], reverse=True)[:10]
    ]) if stats else "검색량 데이터 없음"

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": f"""
키워드: "{keyword}"

[검색량 데이터]
{stats_text}

[블로그/카페 게시글]
{content_sample}

아래 JSON 형식으로만 출력하세요. 다른 텍스트 없이:
{{
  "consumer_insight": "소비자 핵심 니즈 1줄",
  "trend_summary": "트렌드 요약 1줄",
  "peak_insight": "광고 집행 타이밍 인사이트 1줄",
  "pain_points": ["페인포인트 5개"],
  "benefits": ["혜택/결과 5개"],
  "copy_materials": ["카피 소재 키워드 8개"],
  "trends": ["트렌드 표현 4개"],
  "ad_copies": [
    {{"headline": "네이버 검색광고 카피 15자 이내", "angle": "상황", "note": "설명"}},
    {{"headline": "네이버 검색광고 카피 15자 이내", "angle": "기능", "note": "설명"}},
    {{"headline": "네이버 검색광고 카피 15자 이내", "angle": "감성", "note": "설명"}},
    {{"headline": "SNS 배너 카피", "angle": "상황", "note": "설명"}},
    {{"headline": "SNS 배너 카피", "angle": "기능", "note": "설명"}},
    {{"headline": "SNS 배너 카피", "angle": "감성", "note": "설명"}}
  ]
}}
"""}]
    )

    text = msg.content[0].text
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def tag_html(angle: str) -> str:
    cls = {"상황": "tag-situation", "기능": "tag-function", "감성": "tag-emotion"}.get(angle, "tag-situation")
    return f'<span class="tag {cls}">{angle}</span>'


# ── 환경변수 체크 ────────────────────────────────────
required_envs = [
    "NAVER_AD_CUSTOMER_ID", "NAVER_AD_ACCESS_LICENSE", "NAVER_AD_SECRET_KEY",
    "NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET", "ANTHROPIC_API_KEY"
]
missing = [e for e in required_envs if not os.environ.get(e)]
if missing:
    st.error(f"⚠️ 환경변수 미설정: {', '.join(missing)}")
    st.code("""
# Streamlit Cloud → App settings → Secrets 에 아래 형식으로 입력
NAVER_AD_CUSTOMER_ID = "your_value"
NAVER_AD_ACCESS_LICENSE = "your_value"
NAVER_AD_SECRET_KEY = "your_value"
NAVER_CLIENT_ID = "your_value"
NAVER_CLIENT_SECRET = "your_value"
ANTHROPIC_API_KEY = "your_value"
    """)
    st.stop()


# ── UI ───────────────────────────────────────────────
st.title("📊 키워드 소재 분석")
st.caption("네이버 검색광고 + 블로그/카페 + Claude AI 실시간 분석")

# 세션 히스토리 초기화
if "history" not in st.session_state:
    st.session_state.history = []
if "current_keywords" not in st.session_state:
    st.session_state.current_keywords = ""

# 검색창
col_input, col_btn = st.columns([5, 1])
with col_input:
    keyword_input = st.text_input(
        label="키워드 입력",
        placeholder="예: 야간러닝   또는 여러 개: 야간러닝, 새벽러닝, 실내러닝",
        value=st.session_state.current_keywords,
        label_visibility="collapsed",
    )
with col_btn:
    run_btn = st.button("🔍 분석", use_container_width=True, type="primary")

# 최근 검색 히스토리
if st.session_state.history:
    st.markdown("**최근 검색:**")
    hist_cols = st.columns(min(len(st.session_state.history), 6))
    for i, hist_kw in enumerate(st.session_state.history[:6]):
        with hist_cols[i]:
            if st.button(hist_kw[:15], key=f"h{i}"):
                st.session_state.current_keywords = hist_kw
                st.rerun()

st.divider()

# ── 분석 실행 ────────────────────────────────────────
if run_btn and keyword_input.strip():
    keywords = [k.strip() for k in keyword_input.replace("，", ",").split(",") if k.strip()]

    # 히스토리 저장
    joined = ", ".join(keywords)
    if joined not in st.session_state.history:
        st.session_state.history.insert(0, joined)
        st.session_state.history = st.session_state.history[:10]

    # 분석 키워드 표시
    chips = " ".join([f'<span class="kw-chip">{k}</span>' for k in keywords])
    st.markdown(f"**분석 키워드:** {chips}", unsafe_allow_html=True)

    # 수집 + 분석
    with st.spinner("📡 검색량 수집 중..."):
        stats = fetch_keyword_stats(tuple(keywords))

    with st.spinner("📝 블로그/카페 수집 중..."):
        all_posts = []
        for kw in keywords:
            all_posts.extend(fetch_blog_cafe(kw))

    with st.spinner("🤖 Claude AI 분석 중..."):
        result = analyze_with_claude(
            keyword=", ".join(keywords),
            posts_json=json.dumps(all_posts, ensure_ascii=False),
            stats_json=json.dumps(stats, ensure_ascii=False),
        )

    st.success(f"✅ 분석 완료! (블로그/카페 {len(all_posts)}건 분석)")

    # ── 결과 탭 ────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📈 검색량", "🔍 소비자 언어", "✍️ 광고 카피", "💡 인사이트"])

    with tab1:
        if not stats:
            st.info("검색광고 API 데이터가 없습니다.")
        else:
            df = pd.DataFrame(stats).sort_values("monthly_total", ascending=False)
            top3 = df.head(3)
            cols = st.columns(min(3, len(top3)))
            for i, (_, row) in enumerate(top3.iterrows()):
                with cols[i]:
                    st.metric(row["keyword"], f"{row['monthly_total']:,}",
                              f"PC {row['monthly_pc']:,} / 모바일 {row['monthly_mobile']:,}")

            fig = px.bar(df.head(15), x="keyword", y="monthly_total",
                         color="monthly_total", color_continuous_scale="Greens",
                         labels={"keyword": "키워드", "monthly_total": "월간 검색량"})
            fig.update_layout(coloraxis_showscale=False, height=380)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                df[["keyword", "monthly_total", "monthly_pc", "monthly_mobile", "competition"]].rename(
                    columns={"keyword": "키워드", "monthly_total": "합계", "monthly_pc": "PC",
                             "monthly_mobile": "모바일", "competition": "경쟁도"}
                ), hide_index=True, use_container_width=True
            )

    with tab2:
        st.info(f"💬 {result.get('consumer_insight', '')}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔴 페인포인트**")
            for p in result.get("pain_points", []):
                st.markdown(f"- {p}")
            st.markdown("**🔥 트렌드 표현**")
            for t in result.get("trends", []):
                st.markdown(f"- {t}")
        with col2:
            st.markdown("**🟢 혜택 / 결과**")
            for b in result.get("benefits", []):
                st.markdown(f"- {b}")
            st.markdown("**📌 카피 소재 키워드**")
            chips = " ".join([f'<span class="kw-chip">{k}</span>' for k in result.get("copy_materials", [])])
            st.markdown(chips, unsafe_allow_html=True)

        if all_posts:
            with st.expander(f"📄 수집된 게시글 ({len(all_posts)}건)"):
                st.dataframe(
                    pd.DataFrame(all_posts)[["type", "title", "description", "date"]].rename(
                        columns={"type": "출처", "title": "제목", "description": "내용", "date": "날짜"}
                    ), hide_index=True, use_container_width=True
                )

    with tab3:
        angle_filter = st.multiselect("소구점 필터", ["상황", "기능", "감성"],
                                       default=["상황", "기능", "감성"])
        copies = [c for c in result.get("ad_copies", []) if c.get("angle") in angle_filter]
        for copy in copies:
            st.markdown(
                f'<div class="copy-card">'
                f'<strong style="font-size:15px">{copy["headline"]}</strong>&nbsp;&nbsp;{tag_html(copy.get("angle",""))}'
                f'<br><small style="color:#888">{copy.get("note","")}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )
        if copies:
            df_copies = pd.DataFrame([
                {"카피": c["headline"], "소구점": c.get("angle",""), "설명": c.get("note","")}
                for c in copies
            ])
            st.download_button(
                "📥 카피 CSV 다운로드",
                df_copies.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"카피_{keyword_input}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

    with tab4:
        st.success(f"📊 {result.get('trend_summary', '')}")
        st.warning(f"⏰ {result.get('peak_insight', '')}")

elif run_btn:
    st.warning("키워드를 입력해주세요.")

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

anthropic>=0.25.0
requests>=2.31.0
streamlit>=1.32.0
pandas>=2.0.0
plotly>=5.18.0

"""
매일 자동 실행 파이프라인
GitHub Actions에서 매일 오전 9시 실행
"""
import json
import os
from datetime import datetime
from pathlib import Path

from collector.naver_searchad import get_keyword_stats, get_related_keywords
from collector.naver_open_api import collect_all
from analyzer.claude_analyzer import run_full_analysis


# 분석할 키워드 목록 (필요 시 수정)
TARGET_KEYWORDS = [
    "야간러닝",
    "새벽러닝",
    "실내러닝",
    "여름러닝",
    "여름러닝웨어",
    "러닝웨어 추천",
    "기능성 러닝웨어",
]

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def save_json(data: dict, filename: str):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 저장 완료: {path}")


def run():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*50}")
    print(f"🚀 분석 시작: {today}")
    print(f"{'='*50}\n")

    # 1. 검색량 수집
    print("📡 [1/3] 네이버 검색광고 API - 검색량 수집 중...")
    keyword_stats = get_keyword_stats(TARGET_KEYWORDS)
    save_json({"date": today, "stats": keyword_stats}, f"keyword_stats_{today}.json")

    # 연관 키워드 추가 수집
    related = []
    for kw in TARGET_KEYWORDS[:3]:
        related.extend(get_related_keywords(kw))
    save_json({"date": today, "related": related}, f"related_keywords_{today}.json")

    # 2. 블로그/카페 수집
    print("\n📡 [2/3] 네이버 Open API - 블로그/카페 수집 중...")
    blog_cafe_data = collect_all(TARGET_KEYWORDS)
    save_json({"date": today, **blog_cafe_data}, f"blog_cafe_{today}.json")

    # 3. AI 분석
    print("\n🤖 [3/3] Claude AI 분석 중...")
    analysis = run_full_analysis(keyword_stats, blog_cafe_data)
    save_json({"date": today, **analysis}, f"analysis_{today}.json")

    # 최신 분석 결과 덮어쓰기 (대시보드에서 latest.json 참조)
    save_json({"date": today, "keyword_stats": keyword_stats, **analysis}, "latest.json")

    print(f"\n✅ 전체 완료! data/ 폴더에 저장됨")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run()
