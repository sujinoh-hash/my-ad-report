import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="14개 매체 통합 퍼포먼스 대시보드", layout="wide")

st.title("📊 14개 매체 통합 성과 대시보드")

if st.button("🔄 데이터 실시간 동기화 (Sync)"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# --- 1. 설정: 시트 ID 및 GID ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MEDIA_GID = "0"          
ADOBE_GID = "1818457274"  

# --- 2. 데이터 정제 함수 (날짜 & 매체명 지능형 통합) ---
def clean_data(df, is_adobe=False):
    if df is None or df.empty: return None
    
    if is_adobe:
        df = df.iloc[:, :6].copy()
        df.columns = ['일자', '캠페인명', '방문수', '장바구니수', '주문수', '매출액']
    else:
        df = df.iloc[:, :7].copy()
        df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']

    # [날짜 정제] 점(.) -> 하이픈(-) 자동 변환 및 날짜형식 통일
    df['일자'] = df['일자'].astype(str).str.strip().str.replace('.', '-', regex=False)
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce').dt.date
    df = df.dropna(subset=['일자'])

    # [매체명 지능형 통합 로직] 
    if '매체' in df.columns:
        df['매체'] = df['매체'].astype(str).str.strip()
        
        # 1. 네이버쇼핑 통합 (m, w 구분 없이 하나로)
        df.loc[df['매체'].str.lower().str.contains('navershopping|네이버쇼핑', na=False), '매체'] = '네이버쇼핑'
        
        # 2. 카카오 PN 시리즈 통합 (공백/대소문자 무시)
        # '카카오 pn', '카카오  PN', 'KAKAO PN' 등을 모두 '카카오pn'으로 통일
        df.loc[df['매체'].str.replace(' ', '').str.lower().str.contains('카카오pn', na=False), '매체'] = '카카오pn'
        
        # 3. 기타 매체명 깔끔하게 정리 (선택 사항: 원하는 이름으로 고정 가능)
        # 예: '카카오 da' -> '카카오da'
        df.loc[df['매체'].str.replace(' ', '').str.lower() == '카카오da', '매체'] = '카카오da'
        df.loc[df['매체'].str.replace(' ', '').str.lower() == '카카오fr', '매체'] = '카카오fr'

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
    st.sidebar.header("🔍 필터")
    
    # 날짜 필터
    all_dates = sorted(ad_df['일자'].unique())
    date_range = st.sidebar.date_input("조회 기간", [min(all_dates), max(all_dates)])
    
    # 매체 필터 (정렬된 14개 매체 목록)
    media_list = ['전체'] + sorted(list(ad_df['매체'].unique()))
    selected_media = st.sidebar.selectbox("매체 선택", media_list)

    # 필터링 적용
    if len(date_range) == 2:
        f_ad = ad_df[(ad_df['일자'] >= date_range[0]) & (ad_df['일자'] <= date_range[1])]
        f_adobe = adobe_df[(adobe_df['일자'] >= date_range[0]) & (adobe_df['일자'] <= date_range[1])] if adobe_df is not None else pd.DataFrame()
    else:
        f_ad, f_adobe = ad_df, adobe_df

    if selected_media != '전체':
        f_ad = f_ad[f_ad['매체'] == selected_media]
    
    # 캠페인명 기반 어도비 매칭
    target_campaigns = f_ad['캠페인명'].unique()
    f_adobe_matched = f_adobe[f_adobe['캠페인명'].isin(target_campaigns)] if not f_adobe.empty else pd.DataFrame()

    # --- 5. 상단 지표 ---
    total_spend = f_ad['광고비'].sum()
    total_rev = f_adobe_matched['매출액'].sum() if not f_adobe_matched.empty else 0
    roas = (total_rev / total_spend * 100) if total_spend > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 {selected_media} 광고비", f"{total_spend:,.0f}원")
    m2.metric(f"💵 연동 매출액", f"{total_rev:,.0f}원")
    m3.metric("📈 ROAS", f"{roas:,.1f}%")

    st.divider()

    # --- 6. 상세 성과 요약 (모든 지표 포함) ---
    st.subheader("📋 매체별/캠페인별 성과 상세 리포트")
    
    ad_sum = f_ad.groupby('캠페인명').agg({'광고비':'sum', '노출':'sum', '클릭':'sum'}).reset_index()
    if not f_adobe_matched.empty:
        adobe_sum = f_adobe_matched.groupby('캠페인명').agg({'방문수':'sum', '주문수':'sum', '매출액':'sum'}).reset_index()
        final_table = pd.merge(ad_sum, adobe_sum, on='캠페인명', how='left').fillna(0)
    else:
        final_table = ad_sum
        for col in ['방문수', '주문수', '매출액']: final_table[col] = 0
    
    final_table['ROAS(%)'] = (final_table['매출액'] / final_table['광고비'] * 100).fillna(0)
    final_table['CTR(%)'] = (final_table['클릭'] / final_table['노출'] * 100).fillna(0)
    
    # 컬럼 순서 조정
    cols = ['캠페인명', '광고비', '매출액', 'ROAS(%)', '노출', '클릭', 'CTR(%)', '방문수', '주문수']
    st.dataframe(final_table[cols].sort_values('광고비', ascending=False), use_container_width=True)

else:
    st.error("데이터를 불러오지 못했습니다. 시트 설정을 확인하세요.")
