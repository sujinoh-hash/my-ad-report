import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Performance Dashboard", layout="wide")

st.title("📊 통합 성과 & ROAS 대시보드")
if st.button("🔄 데이터 실시간 동기화 (Sync)"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# --- 설정 ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MEDIA_GID = "0"
ADOBE_GID = "1818457274"

def get_sheet_data(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        return df if not df.empty else None
    except:
        return None

ad_raw = get_sheet_data(SHEET_ID, MEDIA_GID)
adobe_raw = get_sheet_data(SHEET_ID, ADOBE_GID)

if ad_raw is not None:
    # 1. 광고 데이터 정제
    ad_df = ad_raw.iloc[:, :7].copy()
    ad_df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
    
    # 날짜 변환 (오류 데이터는 NaT로 처리)
    ad_df['일자'] = pd.to_datetime(ad_df['일자'], errors='coerce').dt.date
    # 날짜가 없는(비어있는) 행은 과감히 삭제
    ad_df = ad_df.dropna(subset=['일자'])
    
    ad_df['캠페인명'] = ad_df['캠페인명'].astype(str).str.strip()
    ad_df['매체'] = ad_df['매체'].astype(str).str.strip()
    
    for c in ['노출', '클릭', '광고비']:
        ad_df[c] = pd.to_numeric(ad_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

    # 2. 어도비 데이터 정제
    if adobe_raw is not None:
        adobe_df = adobe_raw.iloc[:, :6].copy()
        adobe_df.columns = ['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액']
        adobe_df['일자'] = pd.to_datetime(adobe_df['일자'], errors='coerce').dt.date
        adobe_df = adobe_df.dropna(subset=['일자']) # 어도비도 날짜 없는 행 삭제
        adobe_df['캠페인명'] = adobe_df['캠페인명'].astype(str).str.strip()
        for c in ['방문수', '장바구니수', '주문수', '매출액']:
            adobe_df[c] = pd.to_numeric(adobe_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    else:
        adobe_df = pd.DataFrame()

    # --- 3. 사이드바 필터 ---
    st.sidebar.header("🔍 필터")
    
    # 날짜 필터 안전장치: 데이터가 있을 때만 계산
    if not ad_df.empty:
        valid_dates = ad_df['일자'].dropna()
        min_d, max_d = min(valid_dates), max(valid_dates)
        date_range = st.sidebar.date_input("기간 선택", [min_d, max_d])
    else:
        st.error("❗ 유효한 날짜 데이터가 시트에 없습니다.")
        st.stop()

    media_list = ['전체'] + sorted(list(ad_df['매체'].unique()))
    selected_media = st.sidebar.selectbox("매체 선택", media_list)

    # --- 4. 필터링 적용 ---
    if len(date_range) == 2:
        start_d, end_d = date_range
        f_ad = ad_df[(ad_df['일자'] >= start_d) & (ad_df['일자'] <= end_d)]
        f_adobe = adobe_df[(adobe_df['일자'] >= start_d) & (adobe_df['일자'] <= end_d)] if not adobe_df.empty else adobe_df
    else:
        f_ad, f_adobe = ad_df, adobe_df

    if selected_media != '전체':
        f_ad = f_ad[f_ad['매체'] == selected_media]
        target_campaigns = f_ad['캠페인명'].unique()
        if not f_adobe.empty:
            f_adobe = f_adobe[f_adobe['캠페인명'].isin(target_campaigns)]

    # --- 5. 결과 출력 ---
    total_spend = f_ad['광고비'].sum()
    total_rev = f_adobe['매출액'].sum() if not f_adobe.empty else 0
    roas = (total_rev / total_spend * 100) if total_spend > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric(f"💰 {selected_media} 광고비", f"{total_spend:,.0f}원")
    c2.metric(f"💵 연동 매출액 (Adobe)", f"{total_rev:,.0f}원")
    c3.metric("📈 ROAS", f"{roas:,.1f}%")

    st.divider()

    # 그래프
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(px.pie(f_ad, values='광고비', names='매체', title="매체별 지출 비중"), use_container_width=True)
    with g2:
        daily_ad = f_ad.groupby('일자')['광고비'].sum().reset_index()
        st.plotly_chart(px.line(daily_ad, x='일자', y='광고비', title="일자별 지출 추이", markers=True), use_container_width=True)

    st.subheader("📋 광고 성과 상세")
    st.dataframe(f_ad.sort_values('일자', ascending=False), use_container_width=True)

else:
    st.error("데이터를 불러오지 못했습니다. 시트의 첫 번째 탭에 데이터가 있는지 확인하세요.")
