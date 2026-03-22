import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Smart Marketing Dashboard", layout="wide")

st.title("📊 통합 성과 대시보드 (오류 수정 버전)")

# 동기화 버튼
if st.button("🔄 데이터 실시간 동기화 (Sync)"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# --- 1. 설정: 시트 ID 및 GID ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MEDIA_GID = "0"          # 광고 데이터 탭 (Media)
ADOBE_GID = "1818457274"  # 어도비 데이터 탭 (Adobe)

# --- 2. 데이터 정제 함수 ---
def clean_data(df, is_adobe=False):
    if df is None or df.empty: return None
    
    # [수정포인트] 컬럼 개수 맞추기
    if is_adobe:
        # 어도비: 일자, 캠페인명, 방문수, 장바구니수, 주문수, 매출액 (총 6개)
        df = df.iloc[:, :6].copy()
        df.columns = ['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액']
    else:
        # 광고: 일자, 매체, 캠페인명, 노출, 클릭, 채널 친구 수, 광고비 (총 7개)
        df = df.iloc[:, :7].copy()
        df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']

    # 날짜 정제 (점/하이픈 자동 변환)
    df['일자'] = df['일자'].astype(str).str.strip().str.replace('.', '-', regex=False)
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce').dt.date
    df = df.dropna(subset=['일자'])

    # [특정 매체명 통합] navershopping_m, navershopping_w만 'Naver shopping'으로 변경
    if '매체' in df.columns:
        df['매체'] = df['매체'].astype(str).str.strip()
        target_names = ['navershopping_m', 'navershopping_w']
        df.loc[df['매체'].isin(target_names), '매체'] = 'Naver shopping'

    # 숫자 정제 (콤마 제거)
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
    st.sidebar.header("🔍 검색 필터")
    
    # 날짜 필터
    all_dates = sorted(ad_df['일자'].unique())
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
    
    # [중요] 캠페인명 기반으로 광고 데이터와 어도비 데이터 매칭
    target_campaigns = f_ad['캠페인명'].unique()
    f_adobe_matched = f_adobe[f_adobe['캠페인명'].isin(target_campaigns)] if not f_adobe.empty else pd.DataFrame()

    # --- 5. 지표 계산 및 출력 ---
    total_spend = f_ad['광고비'].sum()
    total_rev = f_adobe_matched['매출액'].sum() if not f_adobe_matched.empty else 0
    roas = (total_rev / total_spend * 100) if total_spend > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 {selected_media} 광고비", f"{total_spend:,.0f}원")
    m2.metric(f"💵 연동 매출액 (Adobe)", f"{total_rev:,.0f}원")
    m3.metric("📈 ROAS", f"{roas:,.1f}%")

    st.divider()

   # --- 상세 성과 표 (모든 지표 통합) ---
    st.subheader("📋 캠페인별 통합 성과 상세 (Full Metrics)")

    # 1. 광고 데이터 요약 (노출, 클릭 추가)
    ad_sum = f_ad.groupby('캠페인명').agg({
        '광고비': 'sum',
        '노출': 'sum',
        '클릭': 'sum'
    }).reset_index()

    # 2. 어도비 데이터 요약 (장바구니수 추가)
    if not f_adobe_matched.empty:
        adobe_sum = f_adobe_matched.groupby('캠페인명').agg({
            '방문수': 'sum',
            '장바구니수': 'sum',
            '주문수': 'sum',
            '매출액': 'sum'
        }).reset_index()
        final_table = pd.merge(ad_sum, adobe_sum, on='캠페인명', how='left').fillna(0)
    else:
        final_table = ad_sum
        for col in ['방문수', '장바구니수', '주문수', '매출액']: final_table[col] = 0

    # 3. 계산 지표 추가 (CTR, CVR, ROAS)
    final_table['CTR(%)'] = (final_table['클릭'] / final_table['노출'] * 100).fillna(0)
    final_table['CVR(%)'] = (final_table['주문수'] / final_table['방문수'] * 100).fillna(0)
    final_table['ROAS(%)'] = (final_table['매출액'] / final_table['광고비'] * 100).replace([float('inf')], 0).fillna(0)
    final_table['CPC'] = (final_table['광고비'] / final_table['클릭']).replace([float('inf')], 0).fillna(0)

    # 4. 보기 좋게 정렬 및 출력
    display_cols = [
        '캠페인명', '광고비', '매출액', 'ROAS(%)', 
        '노출', '클릭', 'CTR(%)', 'CPC',
        '방문수', '장바구니수', '주문수', 'CVR(%)'
    ]
    
    # 숫자 포맷팅 (소수점 정리)
    st.dataframe(
        final_table[display_cols].sort_values('광고비', ascending=False), 
        use_container_width=True
    )
