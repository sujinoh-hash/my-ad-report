import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Total Marketing Dashboard", layout="wide")

# --- 타이틀 및 동기화 버튼 ---
st.title("📊 통합 성과 & 어도비 대시보드")
if st.button("🔄 데이터 강제 동기화 (Sync)"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# --- 설정: 본인의 시트 ID 및 Adobe GID ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"
NAVER_GID = "0"
ADOBE_GID = "1818457274"

def get_sheet_data(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        return df if not df.empty else None
    except:
        return None

# 데이터 로드
ad_raw = get_sheet_data(SHEET_ID, NAVER_GID)
adobe_raw = get_sheet_data(SHEET_ID, ADOBE_GID)

if ad_raw is not None:
    # 1. 광고 데이터 정제
    ad_df = ad_raw.iloc[:, :7].copy()
    ad_df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
    ad_df['일자'] = pd.to_datetime(ad_df['일자'], errors='coerce').dt.date
    ad_df = ad_df.dropna(subset=['일자'])
    for c in ['노출', '클릭', '광고비']:
        ad_df[c] = pd.to_numeric(ad_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

    # 2. 어도비 데이터 정제
    if adobe_raw is not None:
        adobe_df = adobe_raw.iloc[:, :6].copy()
        adobe_df.columns = ['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액']
        adobe_df['일자'] = pd.to_datetime(adobe_df['일자'], errors='coerce').dt.date
        for c in ['방문수', '장바구니수', '주문수', '매출액']:
            adobe_df[c] = pd.to_numeric(adobe_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    else:
        adobe_df = pd.DataFrame(columns=['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액'])

    # --- 3. 사이드바 필터 (날짜 & 매체) ---
    st.sidebar.header("🔍 검색 필터")
    
    # 날짜 필터 안전하게 설정
    if not ad_df.empty:
        min_date = min(ad_df['일자'])
        max_date = max(ad_df['일자'])
        date_range = st.sidebar.date_input("조회 기간", [min_date, max_date])
    else:
        date_range = []

    media_list = ['전체'] + list(ad_df['매체'].unique())
    selected_media = st.sidebar.selectbox("매체 선택", media_list)

    # --- 4. 데이터 필터링 적용 ---
    if len(date_range) == 2:
        start_d, end_d = date_range
        f_ad = ad_df[(ad_df['일자'] >= start_d) & (ad_df['일자'] <= end_d)]
        f_adobe = adobe_df[(adobe_df['일자'] >= start_d) & (adobe_df['일자'] <= end_d)]
    else:
        f_ad, f_adobe = ad_df, adobe_df

    if selected_media != '전체':
        f_ad = f_ad[f_ad['매체'] == selected_media]

    # --- 5. 결과 출력 ---
    if f_ad.empty:
        st.warning("선택한 필터 조건에 맞는 데이터가 없습니다.")
    else:
        total_spend = f_ad['광고비'].sum()
        total_rev = f_adobe['매출액'].sum()
        roas = (total_rev / total_spend * 100) if total_spend > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 광고비", f"{total_spend:,.0f}원")
        c2.metric("💵 매출액", f"{total_rev:,.0f}원")
        c3.metric("📈 ROAS", f"{roas:,.1f}%")

        st.divider()

        # 그래프
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(f_ad, values='광고비', names='매체', title="매체별 비중"), use_container_width=True)
        with g2:
            daily = f_ad.groupby('일자')['광고비'].sum().reset_index()
            st.plotly_chart(px.line(daily, x='일자', y='광고비', title="일자별 추이"), use_container_width=True)

        st.subheader("📋 상세 현황")
        st.dataframe(f_ad.sort_values('일자', ascending=False), use_container_width=True)

else:
    st.error("구글 시트 연결 실패. 공유 설정과 ID를 확인하세요.")

st.sidebar.info("💡 팁: 날짜 범위를 넓게 조정해 보세요.")
