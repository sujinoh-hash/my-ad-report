import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Marketing Dashboard", layout="wide")
st.title("📊 마케팅 성과 통합 실시간 대시보드")

# --- 설정: 본인의 시트 ID ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"

def get_data(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url)
        if not df.empty:
            df = df.iloc[:, :7] 
            df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
            df['일자'] = pd.to_datetime(df['일자'], errors='coerce').dt.date
            # 숫자 데이터 정제
            for c in ['노출', '클릭', '채널 친구 수', '광고비']:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"⚠️ 연결 실패: {e}")
        return None

# 데이터 불러오기
raw_df = get_data(SHEET_ID)

if raw_df is not None:
    # --- 사이드바 필터 설정 ---
    st.sidebar.header("🔍 데이터 필터")
    
    # 1. 날짜 필터
    min_date = min(raw_df['일자'])
    max_date = max(raw_df['일자'])
    start_date, end_date = st.sidebar.date_input("조회 기간 선택", [min_date, max_date])
    
    # 2. 매체 필터
    media_list = ['전체'] + list(raw_df['매체'].unique())
    selected_media = st.sidebar.selectbox("매체 선택", media_list)

    # --- 데이터 필터링 적용 ---
    mask = (raw_df['일자'] >= start_date) & (raw_df['일자'] <= end_date)
    if selected_media != '전체':
        mask = mask & (raw_df['매체'] == selected_media)
    
    filtered_df = raw_df[mask]

    # --- 화면 출력 ---
    if st.button("🔄 최신 데이터 동기화"):
        st.rerun()

    # 상단 요약 지표 (필터링된 데이터 기준)
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 선택 기간 총 광고비", f"{filtered_df['광고비'].sum():,.0f}원")
    c2.metric("👁️ 총 노출수", f"{filtered_df['노출'].sum():,.0f}회")
    c3.metric("🖱️ 총 클릭수", f"{filtered_df['클릭'].sum():,.0f}회")

    st.divider()

    # 그래프 (필터링된 데이터 기준)
    g1, g2 = st.columns(2)
    with g1:
        fig_pie = px.pie(filtered_df, values='광고비', names='매체', title=f"[{selected_media}] 매체별 비중")
        st.plotly_chart(fig_pie, use_container_width=True)
    with g2:
        daily_trend = filtered_df.groupby('일자')['광고비'].sum().reset_index()
        fig_line = px.line(daily_trend, x='일
