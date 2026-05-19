"""
Streamlit 대시보드 - 키워드 검색량 + 블로그/카페 수집
분석은 Claude.ai 에 붙여넣기해서 사용
"""
import os
import time
import requests
import re
import hmac
import hashlib
import base64
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="키워드 수집 대시보드", page_icon="📊", layout="wide")

st.markdown("""
<style>
.kw-chip { display:inline-block; background:#f1f3f4; border-radius:16px; padding:4px 12px; margin:3px; font-size:13px; color:#333; }
.tip-box { background:#e8f4fd; border-left:4px solid #1a73e8; border-radius:4px; padding:12px 16px; font-size:13px; margin:12px 0; }
.source-tag { font-size:11px; color:#888; margin-top:4px; }
</style>
""", unsafe_allow_html=True)


def to_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def get_ad_headers(method, path):
    ts = str(int(time.time() * 1000))
    msg = f"{ts}.{method}.{path}"
    sig = hmac.new(os.environ["NAVER_AD_SECRET_KEY"].encode(), msg.encode(), hashlib.sha256)
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": ts,
        "X-API-KEY": os.environ["NAVER_AD_ACCESS_LICENSE"],
        "X-Customer": os.environ["NAVER_AD_CUSTOMER_ID"],
        "X-Signature": base64.b64encode(sig.digest()).decode(),
    }


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text).replace("&quot;", '"').replace("&amp;", "&").strip()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_keyword_stats(keywords_tuple, expand=False):
    path = "/keywordstool"
    url = "https://api.naver.com" + path
    results = []
    seen = set()

    def fetch_batch(batch):
        try:
            headers = get_ad_headers("GET", path)
            resp = requests.get(url, headers=headers,
                                params={"hintKeywords": ",".join(batch), "showDetail": 1},
                                timeout=10)
            resp.raise_for_status()
            for item in resp.json().get("keywordList", []):
                kw = str(item.get("relKeyword", ""))
                if kw in seen:
                    continue
                seen.add(kw)
                pc = to_int(item.get("monthlyPcQcCnt", 0))
                mobile = to_int(item.get("monthlyMobileQcCnt", 0))
                results.append({
                    "keyword": kw,
                    "monthly_pc": pc,
                    "monthly_mobile": mobile,
                    "monthly_total": pc + mobile,
                    "competition": str(item.get("compIdx", "-")),
                    "expanded": kw not in keywords_tuple,
                })
        except Exception as e:
            st.warning(f"검색광고 API 오류: {e}")
        time.sleep(0.3)

    # 입력 키워드 수집
    for i in range(0, len(keywords_tuple), 5):
        batch = list(keywords_tuple[i:i+5])
        fetch_batch(batch)

    # 연관 키워드 확장 수집
    if expand:
        related_seeds = list(keywords_tuple)[:3]
        for kw in related_seeds:
            fetch_batch([kw])

    return results


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_blog_cafe(keyword, display=100):
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
                    "description": strip_html(item.get("description", ""))[:200],
                    "date": item.get("postdate", ""),
                    "link": item.get("link", ""),
                })
        except Exception as e:
            st.warning(f"Open API 오류 ({source}): {e}")
    return results


def build_prompt(keywords, stats, posts):
    stats_text = "\n".join([
        f"- {s['keyword']}: 월 {s['monthly_total']:,}회 (PC {s['monthly_pc']:,} / 모바일 {s['monthly_mobile']:,}, 경쟁도: {s['competition']})"
        for s in sorted(stats, key=lambda x: x["monthly_total"], reverse=True)[:20]
    ]) if stats else "데이터 없음"

    posts_text = "\n".join([
        f"[{p['type']}] {p['title']} / {p['description']}"
        for p in posts[:30]
    ]) if posts else "데이터 없음"

    lines = [
        "다음은 네이버에서 수집한 키워드 데이터예요. 분석해줘.",
        "",
        f"키워드: {', '.join(keywords)}",
        "",
        "[검색량 데이터 - 네이버 검색광고 API 기준 월간 검색량]",
        stats_text,
        "",
        "[블로그/카페 게시글 - 최신순 수집]",
        posts_text,
        "",
        "아래 내용 분석해줘:",
        "1. 트렌드 요약 (2줄)",
        "2. 소비자 페인포인트 5개",
        "3. 혜택/결과 키워드 5개",
        "4. 광고 카피 소재 키워드 8개",
        "5. 네이버 검색광고 헤드카피 6개 (상황/기능/감성 각 2개씩, 15자 이내)",
        "6. 광고 집행 타이밍 인사이트",
    ]
    return "\n".join(lines)


# 환경변수 체크
required_envs = ["NAVER_AD_CUSTOMER_ID", "NAVER_AD_ACCESS_LICENSE", "NAVER_AD_SECRET_KEY",
                 "NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"]
missing = [e for e in required_envs if not os.environ.get(e)]
if missing:
    st.error(f"환경변수 미설정: {', '.join(missing)}")
    st.stop()


# UI
st.title("📊 키워드 수집 대시보드")
st.caption("네이버 검색광고 + 블로그/카페 수집 → Claude.ai에서 분석")

if "history" not in st.session_state:
    st.session_state.history = []
if "current_keywords" not in st.session_state:
    st.session_state.current_keywords = ""

col_input, col_btn = st.columns([5, 1])
with col_input:
    keyword_input = st.text_input(
        label="키워드",
        placeholder="예: 야간러닝   또는 여러 개: 야간러닝, 새벽러닝, 실내러닝",
        value=st.session_state.current_keywords,
        label_visibility="collapsed",
    )
with col_btn:
    run_btn = st.button("🔍 수집", use_container_width=True, type="primary")

# 옵션
expand_kw = st.checkbox("🔗 연관 키워드 자동 확장 (입력 키워드 기반으로 관련 키워드 추가 수집)", value=False)

if st.session_state.history:
    st.markdown("**최근 검색:**")
    hist_cols = st.columns(min(len(st.session_state.history), 6))
    for i, hist_kw in enumerate(st.session_state.history[:6]):
        with hist_cols[i]:
            if st.button(hist_kw[:15], key=f"h{i}"):
                st.session_state.current_keywords = hist_kw
                st.rerun()

st.divider()

if run_btn and keyword_input.strip():
    keywords = [k.strip() for k in keyword_input.replace("，", ",").split(",") if k.strip()]
    joined = ", ".join(keywords)
    if joined not in st.session_state.history:
        st.session_state.history.insert(0, joined)
        st.session_state.history = st.session_state.history[:10]

    chips = " ".join([f'<span class="kw-chip">{k}</span>' for k in keywords])
    st.markdown(f"**수집 키워드:** {chips}", unsafe_allow_html=True)

    with st.spinner("📡 검색량 수집 중..."):
        stats = fetch_keyword_stats(tuple(keywords), expand=expand_kw)

    with st.spinner("📝 블로그/카페 수집 중... (최대 100건/키워드)"):
        all_posts = []
        for kw in keywords:
            all_posts.extend(fetch_blog_cafe(kw))

    st.success(f"✅ 수집 완료! 키워드 {len(stats)}개 / 게시글 {len(all_posts)}건")

    tab1, tab2, tab3 = st.tabs(["📈 검색량", "📝 블로그/카페", "🤖 Claude 분석용 복사"])

    with tab1:
        if not stats:
            st.info("검색광고 API 데이터가 없습니다.")
        else:
            st.caption("출처: 네이버 검색광고 API (api.naver.com) · 월간 검색량 기준")

            df = pd.DataFrame(stats)
            df["monthly_total"] = pd.to_numeric(df["monthly_total"], errors="coerce").fillna(0).astype(int)
            df["monthly_pc"] = pd.to_numeric(df["monthly_pc"], errors="coerce").fillna(0).astype(int)
            df["monthly_mobile"] = pd.to_numeric(df["monthly_mobile"], errors="coerce").fillna(0).astype(int)
            df = df.sort_values("monthly_total", ascending=False)

            # 확장 키워드 구분 표시
            if expand_kw and "expanded" in df.columns:
                input_df = df[~df["expanded"]]
                expanded_df = df[df["expanded"]]
                if not expanded_df.empty:
                    st.markdown(f"입력 키워드 **{len(input_df)}개** + 연관 확장 **{len(expanded_df)}개**")

            top3 = df.head(3)
            cols = st.columns(min(3, len(top3)))
            for i, (_, row) in enumerate(top3.iterrows()):
                with cols[i]:
                    st.metric(row["keyword"], f"{row['monthly_total']:,}",
                              f"PC {row['monthly_pc']:,} / 모바일 {row['monthly_mobile']:,}")

            fig = px.bar(df.head(20), x="keyword", y="monthly_total",
                         color="monthly_total", color_continuous_scale="Greens",
                         labels={"keyword": "키워드", "monthly_total": "월간 검색량"})
            fig.update_layout(coloraxis_showscale=False, height=380)
            st.plotly_chart(fig, use_container_width=True)

            show_cols = ["keyword", "monthly_total", "monthly_pc", "monthly_mobile", "competition"]
            st.dataframe(
                df[show_cols].rename(
                    columns={"keyword": "키워드", "monthly_total": "합계", "monthly_pc": "PC",
                             "monthly_mobile": "모바일", "competition": "경쟁도"}
                ), hide_index=True, use_container_width=True
            )
            st.download_button("📥 검색량 CSV", df.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"검색량_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    with tab2:
        if not all_posts:
            st.info("수집된 게시글이 없습니다.")
        else:
            st.caption("출처: 네이버 Open API · 최신순 수집 · 키워드당 최대 100건 (블로그 + 카페)")

            df_posts = pd.DataFrame(all_posts)
            source_filter = st.multiselect("출처 필터", ["블로그", "카페"], default=["블로그", "카페"])
            filtered = df_posts[df_posts["type"].isin(source_filter)]
            st.dataframe(
                filtered[["type", "title", "description", "date"]].rename(
                    columns={"type": "출처", "title": "제목", "description": "내용", "date": "날짜"}
                ), hide_index=True, use_container_width=True, height=400
            )
            st.download_button("📥 게시글 CSV", filtered.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"게시글_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    with tab3:
        st.markdown('<div class="tip-box">💡 아래 내용을 전체 복사해서 <strong>Claude.ai 채팅창</strong>에 붙여넣으면 바로 분석해드려요!</div>', unsafe_allow_html=True)
        prompt = build_prompt(keywords, stats, all_posts)
        st.text_area("Claude 분석 프롬프트", value=prompt, height=420, label_visibility="collapsed")
        st.caption("텍스트박스 클릭 → Ctrl+A (전체선택) → Ctrl+C (복사)")

elif run_btn:
    st.warning("키워드를 입력해주세요.")
