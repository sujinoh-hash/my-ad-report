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
NAVER_AD_CUSTOMER_ID = "여기에입력"
NAVER_AD_ACCESS_LICENSE = "여기에입력"
NAVER_AD_SECRET_KEY = "여기에입력"
NAVER_CLIENT_ID = "여기에입력"
NAVER_CLIENT_SECRET = "여기에입력"
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
