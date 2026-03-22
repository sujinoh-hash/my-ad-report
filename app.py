import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Performance Dashboard", layout="wide")

st.title("📊 통합 성과 & CID 기반 ROAS 대시보드")
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
    ad_df['일자'] = pd.to_datetime(ad_df['일자'], errors='coerce').dt.date
    # 캠페인명/매체명 앞뒤 공백 제거 (매칭 정확도 향상)
    ad_df['캠페인명'] = ad_df['캠페인명'].astype(str).str.strip()
    ad_df['매체'] = ad_df['매체'].astype(str).str.strip()
    
    for c in ['노출', '클릭', '광고비']:
        ad_df[c] = pd.to_numeric(ad_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

    # 2. 어도비 데이터 정제 (CID 규칙 캠페인명 기준)
    if adobe_raw is not None:
        adobe_df = adobe_raw.iloc[:, :6].copy()
        adobe_df.columns = ['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액']
        adobe_df['일자'] = pd.to_datetime(adobe_df['일자'], errors='coerce').dt.date
        adobe_df['캠페인명'] = adobe_df['캠페인명'].astype(str).str.strip()
        for c in ['방문수', '장바구니수', '주문수', '매출액']:
            adobe_df[c] = pd.to_numeric(adobe_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    else:
        adobe_df = pd.DataFrame()

    # --- 3. 사이드바 필터 ---
    st.sidebar.header("🔍 필터")
    media_list = ['전체'] + sorted(list(ad_df['매체'].unique()))
    selected_media = st.sidebar.selectbox("매체 선택", media_list)
    
    min_d, max_d = min(ad_df['일자']), max(ad_df['일자'])
    date_range = st.sidebar.date_input("기간 선택", [min_d, max_d])

    # --- 4. 필터링 및 데이터 결합 (핵심!) ---
    if len(date_range) == 2:
        start_d, end_d = date_range
        f_ad = ad_df[(ad_df['일자'] >= start_d) & (ad_df['일자'] <= end_d)]
        f_adobe = adobe_df[(adobe_df['일자'] >= start_d) & (adobe_df['일자'] <= end_d)]
    else:
        f_ad, f_adobe = ad_df, adobe_df

    if selected_media != '전체':
        f_ad = f_ad[f_ad['매체'] == selected_media]
        # 💡 광고 데이터의 캠페인명 리스트를 추출하여 어도비 데이터에서 해당 캠페인만 필터링
        target_campaigns = f_ad['캠페인명'].unique()
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

    # 그래프 및 상세 테이블
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(px.pie(f_ad, values='광고비', names='매체', title="매체별 지출 비중"), use_container_width=True)
    with g2:
        daily_ad = f_ad.groupby('일자')['광고비'].sum().reset_index()
        st.plotly_chart(px.line(daily_ad, x='일자', y='광고비', title="일자별 광고비 추이"), use_container_width=True)

    st.subheader("📋 광고 성과 상세")
    st.dataframe(f_ad.sort_values('일자', ascending=False), use_container_width=True)
    
    if not f_adobe.empty:
        st.subheader("🛒 어도비 전환 상세 (필터링된 캠페인 기준)")
        st.dataframe(f_adobe.sort_values('일자', ascending=False), use_container_width=True)
else:
    st.error("데이터를 불러오지 못했습니다.")
