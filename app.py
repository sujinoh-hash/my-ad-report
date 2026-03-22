import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Marketing Dashboard", layout="wide")

st.title("📊 통합 성과 & 어도비 대시보드")
if st.button("🔄 데이터 강제 동기화 (Sync)"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# --- 설정 ---
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

ad_raw = get_sheet_data(SHEET_ID, NAVER_GID)
adobe_raw = get_sheet_data(SHEET_ID, ADOBE_GID)

# 1. 광고 데이터 처리
if ad_raw is not None:
    ad_df = ad_raw.iloc[:, :7].copy()
    ad_df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
    ad_df['일자'] = pd.to_datetime(ad_df['일자'], errors='coerce').dt.date
    ad_df = ad_df.dropna(subset=['일자']) # 날짜 오류 행 제거
    
    for c in ['노출', '클릭', '광고비']:
        ad_df[c] = pd.to_numeric(ad_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

    # 2. 어도비 데이터 처리
    if adobe_raw is not None:
        adobe_df = adobe_raw.iloc[:, :6].copy()
        adobe_df.columns = ['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액']
        adobe_df['일자'] = pd.to_datetime(adobe_df['일자'], errors='coerce').dt.date
        for c in ['방문수', '장바구니수', '주문수', '매출액']:
            adobe_df[c] = pd.to_numeric(adobe_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    else:
        adobe_df = pd.DataFrame(columns=['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액'])

    # --- 사이드바 필터 ---
    st.sidebar.header("🔍 필터 설정")
    
    # 날짜 범위 설정 (안전 장치 추가)
    min_date = min(ad_df['일자']) if not ad_df.empty else None
    max_date = max(ad_df['일자']) if not ad_df.empty else None
    
    if min_date and max_date:
        date_range = st.sidebar.date_input("조회 기간", [min_date, max_date])
    else:
        date_range = []

    media_list = ['전체'] + list(ad_df['매체'].unique())
    selected_media = st.sidebar.selectbox("매체 선택", media_list)

    # --- 데이터 필터링 ---
    if len(date_range) == 2:
        start_d, end_d = date_range
        f_ad = ad_df[(ad_df['일자'] >= start_d) & (ad_df['일자'] <= end_d)]
        f_adobe = adobe_df[(adobe_df['일자'] >= start_d) & (adobe_df['일자'] <= end_d)]
    else:
        f_ad, f_adobe = ad_df, adobe_df

    if selected_media != '전체':
        f_ad = f_ad[f_ad['매체'] == selected_media]

    # --- 화면 출력부 ---
    if f_ad.empty:
        st.warning("선택한 조건(날짜/매체)에 맞는 광고 데이터가 없습니다. 필터를 조절해 보세요.")
    else:
        # 지표 계산
        total_spend = f_ad['광고비'].sum()
        total_rev = f_adobe['매출액'].sum() if not f_adobe.empty else 0
        roas = (total_rev / total_spend * 100) if total_spend > 0 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("💰 광고비", f"{total_spend:,.0f}원")
        m2.metric("💵 매출액", f"{total_rev:,.0f}원")
        m3.metric("📈 ROAS", f"{roas:,.1f}%")

        st.divider()
        
        # 그래프 및 테이블
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(f_ad, values='광고비', names='매체', title="매체별 비중"), use_container_width=True)
        with c2:
            daily = f_ad.groupby('일자')['광고비'].sum().reset_index()
            st.plotly_chart(px.line(daily, x='일자', y='광고비', title="일자별 추이"), use_container_
