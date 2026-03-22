import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Marketing & Adobe Dashboard", layout="wide")

# --- 1. 상단 타이틀 및 동기화 버튼 ---
st.title("📊 통합 성과 & 어도비 ROAS 대시보드")
if st.button("🔄 데이터 실시간 동기화 (Sync)"):
    st.rerun()

st.divider()

# --- 2. 설정: 본인의 시트 ID 및 GID ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"
NAVER_GID = "0"          # 네이버/매체 탭 GID
ADOBE_GID = "1818457274"  # 어도비 탭 GID

def get_sheet_data(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        if df.empty: return None
        return df
    except:
        return None

# 데이터 로드
ad_raw = get_sheet_data(SHEET_ID, NAVER_GID)
adobe_raw = get_sheet_data(SHEET_ID, ADOBE_GID)

if ad_raw is not None:
    # --- 광고 데이터 정제 ---
    ad_df = ad_raw.iloc[:, :7].copy()
    ad_df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
    ad_df['일자'] = pd.to_datetime(ad_df['일자'], errors='coerce').dt.date
    for c in ['노출', '클릭', '광고비']:
        ad_df[c] = pd.to_numeric(ad_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    ad_df = ad_df.dropna(subset=['일자'])

    # --- 어도비 데이터 정제 (일자, 캠페인명, 방문수, 장바구니수, 주문수, 매출액) ---
    if adobe_raw is not None:
        adobe_df = adobe_raw.iloc[:, :6].copy()
        adobe_df.columns = ['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액']
        adobe_df['일자'] = pd.to_datetime(adobe_df['일자'], errors='coerce').dt.date
        for c in ['방문수', '장바구니수', '주문수', '매출액']:
            adobe_df[c] = pd.to_numeric(adobe_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        adobe_df = adobe_df.dropna(subset=['일자'])
    else:
        adobe_df = pd.DataFrame()

    # --- 3. 사이드바 필터 (날짜 & 매체) ---
    st.sidebar.header("🔍 검색 필터")
    
    # 날짜 필터 추가
    all_dates = sorted(ad_df['일자'].unique())
    if all_dates:
        start_default = all_dates[0]
        end_default = all_dates[-1]
        date_range = st.sidebar.date_input("조회 기간", [start_default, end_default])
    
    # 매체 필터
    media_options = ['전체'] + list(ad_df['매체'].unique())
    selected_media = st.sidebar.selectbox("매체 선택", media_options)

    # --- 4. 데이터 필터링 적용 ---
    if len(date_range) == 2:
        start_d, end_d = date_range
        # 광고 데이터 필터
        f_ad = ad_df[(ad_df['일자'] >= start_d) & (ad_df['일자'] <= end_d)]
        # 어도비 데이터 필터
        f_adobe = adobe_df[(adobe_df['일자'] >= start_d) & (adobe_df['일자'] <= end_d)]
        
        if selected_media != '전체':
            f_ad = f_ad[f_ad['매체'] == selected_media]
            # 어도비는 매체 정보가 따로 없으므로 캠페인명 등으로 매칭해야 하지만, 
            # 일단 전체 매출로 계산하거나 시트 구조에 맞춰 보정 필요
    else:
        f_ad, f_adobe = ad_df, adobe_df

    # --- 5. 주요 지표 출력 ---
    total_spend = f_ad['광고비'].sum()
    total_rev = f_adobe['매출액'].sum() if not f_adobe.empty else 0
    total_visit = f_adobe['방문수'].sum() if not f_adobe.empty else 0
    total_cart = f
