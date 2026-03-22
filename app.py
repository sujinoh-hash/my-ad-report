import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Total Marketing Dashboard", layout="wide")
st.title("🚀 통합 성과 & ROAS 대시보드")

# --- 설정: 본인의 시트 ID ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"

def get_sheet_data(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        if df.empty: return None
        return df
    except:
        return None

# 1. 광고 매체 데이터 가져오기 (Naver 탭: gid=0)
ad_df = get_sheet_data(SHEET_ID, "0")
# 2. 어도비 매출 데이터 가져오기 (Adobe 탭: gid 확인 필요, 예시는 임시 gid)
# Adobe 탭의 실제 gid 숫자로 아래 "12345"를 수정해 주세요!
adobe_df = get_sheet_data(SHEET_ID, "1818457274")

if ad_df is not None:
    # 광고 데이터 정제
    ad_df = ad_df.iloc[:, :7]
    ad_df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
    ad_df['일자'] = pd.to_datetime(ad_df['일자'], errors='coerce').dt.date
    for c in ['노출', '클릭', '광고비']:
        ad_df[c] = pd.to_numeric(ad_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

    # --- 사이드바 필터 ---
    st.sidebar.header("🔍 데이터 필터")
    media_list = ['전체'] + list(ad_df['매체'].unique())
    selected_media = st.sidebar.selectbox("매체 선택", media_list)
    
    # 날짜 필터링 적용
    mask = ad_df['일자'].notnull()
    if selected_media != '전체':
        mask = mask & (ad_df['매체'] == selected_media)
    
    filtered_ad = ad_df[mask]

    # --- 상단 주요 지표 ---
    total_spend = filtered_ad['광고비'].sum()
    total_click = filtered_ad['클릭'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 총 광고비", f"{total_spend:,.0f}원")
    c2.metric("🖱️ 총 클릭", f"{total_click:,.0f}회")
    
    # 어도비 매출 연동 시 ROAS 계산
    if adobe_df is not None:
        adobe_df['일자'] = pd.to_datetime(adobe_df.iloc[:,0], errors='coerce').dt.date
        revenue_col = adobe_df.columns[3] # 매출액 컬럼
        total_revenue = pd.to_numeric(adobe_df[revenue_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
        roas = (total_revenue / total_spend * 100) if total_spend > 0 else 0
        c3.metric("💵 총 매출 (Adobe)", f"{total_revenue:,.0f}원")
        c4.metric("📈 ROAS", f"{roas:,.1f}%")
    else:
        c3.info("Adobe 데이터를 추가해 주세요.")

    st.divider()

    # --- 그래프 ---
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("매체별 지출 비중")
        fig_pie = px.pie(filtered_ad, values='광고비', names='매체', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    with g2:
        st.subheader("일자별 광고비 추이")
        daily_trend = filtered_ad.groupby('일자')['광고비'].sum().reset_index()
        fig_line = px.line(daily_trend, x='일자', y='광고비', markers=True)
        st.plotly
