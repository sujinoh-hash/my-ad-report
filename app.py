import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Smart Marketing Dashboard", layout="wide")

st.title("📊 통합 성과 대시보드 (자동 정제 버전)")

# 동기화 버튼
if st.button("🔄 데이터 실시간 동기화 (Sync)"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# --- 1. 설정: 시트 ID 및 GID ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MEDIA_GID = "0"          # 광고 데이터 탭
ADOBE_GID = "1818457274"  # 어도비 데이터 탭

# --- 2. 데이터 정제 함수 (날짜 & 특정 매체명 통합) ---
def clean_data(df, is_adobe=False):
    if df is None or df.empty: return None
    
    # 컬럼 구조 잡기
    if is_adobe:
        # 어도비: 일자, 매체, 캠페인명, 방문수, 장바구니수, 주문수, 매출액 (7개 가정)
        df = df.iloc[:, :7].copy()
        df.columns = ['일자', '매체', '캠페인명', '방문수', '장바구니수', '주문수', '매출액']
    else:
        # 광고: 일자, 매체, 캠페인명, 노출, 클릭, 채널 친구 수, 광고비 (7개)
        df = df.iloc[:, :7].copy()
        df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']

    # [날짜 정제] 점(.)을 하이픈(-)으로 바꾸고 날짜 형식으로 변환 (네이버/메타 혼용 해결)
    df['일자'] = df['일자'].astype(str).str.strip().str.replace('.', '-', regex=False)
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce').dt.date
    df = df.dropna(subset=['일자']) # 날짜 없는 행 제거

    # [특정 매체명 통합] navershopping_m, navershopping_w만 'Naver shopping'으로 변경
    if '매체' in df.columns:
        df['매체'] = df['매체'].astype(str).str.strip()
        target_names = ['navershopping_m', 'navershopping_w']
        # 해당 이름들만 변경하고 나머지는 유지
        df.loc[df['매체'].isin(target_names), '매체'] = 'Naver shopping'

    # [숫자 정제] 콤마 제거 및 숫자 변환
    num_cols = ['방문수', '장바구니수', '주문수', '매출액'] if is_adobe else ['노출', '클릭', '광고비']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    
    if '캠페인명' in df.columns:
        df['캠페인명'] = df['캠페인명'].astype(str).str.strip()
        
    return df

# --- 3. 데이터 로드 ---
def load_full_data():
    try:
        ad_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MEDIA_GID}"
        adobe_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={ADOBE_GID}"
        return pd.read_csv(ad_url), pd.read_csv(adobe_url)
    except:
        return None, None

ad_raw, adobe_raw = load_full_data()
ad_df = clean_data(ad_raw, is_adobe=False)
adobe_df = clean_data(adobe_raw, is_adobe=True)

# --- 4. 대시보드 메인 로직 ---
if ad_df is not None and not ad_df.empty:
    # 사이드바 필터
    st.sidebar.header("🔍 검색 필터")
    
    # 날짜 필터
    all_dates = sorted(ad_df['일자'].unique())
    if all_dates:
        date_range = st.sidebar.date_input("조회 기간", [min(all_dates), max(all_dates)])
    
    # 매체 필터
    media_list = ['전체'] + sorted(list(ad_df['매체'].unique()))
    selected_media = st.sidebar.selectbox("매체 선택", media_list)

    # 데이터 필터링 적용
    if len(date_range) == 2:
        f_ad = ad_df[(ad_df['일자'] >= date_range[0]) & (ad_df['일자'] <= date_range[1])]
        f_adobe = adobe_df[(adobe_df['일자'] >= date_range[0]) & (adobe_df['일자'] <= date_range[1])] if adobe_df is not None else pd.DataFrame()
    else:
        f_ad, f_adobe = ad_df, adobe_df

    if selected_media != '전체':
        f_ad = f_ad[f_ad['매체'] == selected_media]
        if not f_adobe.empty:
            f_adobe = f_adobe[f_adobe['매체'] == selected_media]

    # --- 5. 지표 계산 및 출력 ---
    total_spend = f_ad['광고비'].sum()
    total_rev = f_adobe['매출액'].sum() if not f_adobe.empty else 0
    roas = (total_rev / total_spend * 100) if total_spend > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 {selected_media} 광고비", f"{total_spend:,.0f}원")
    m2.metric(f"💵 연동 매출액", f"{total_rev:,.0f}원")
    m3.metric("📈 ROAS", f"{roas:,.1f}%")

    st.divider()

    # 그래프
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(f_ad, values='광고비', names='매체', title="매체별 비중", hole=0.4), use_container_width=True)
    with col2:
        daily_trend = f_ad.groupby('일자')['광고비'].sum().reset_index()
        st.plotly_chart(px.line(daily_trend, x='일자', y='광고비', title="일자별 광고비 추이", markers=True), use_container_width=True)

    # 상세 성과 표
    st.subheader("📋 성과 상세 데이터")
    st.dataframe(f_ad.sort_values('일자', ascending=False), use_container_width=True)

else:
    st.error("데이터를 불러올 수 없습니다. 시트의 공유 설정과 GID를 확인하세요.")
