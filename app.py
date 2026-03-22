import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Marketing Analytics Master", layout="wide")
st.title("🏆 마케팅 성과 통합 자동화 솔루션")

def load_data(uploaded_file):
    if uploaded_file is None: return None
    try:
        if uploaded_file.name.endswith('.csv'):
            for enc in ['utf-8-sig', 'cp949', 'utf-16', 'latin1']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=enc, sep=None, engine='python', comment='#', skip_blank_lines=True)
                    if not df.empty: return df
                except: continue
        else:
            return pd.read_excel(uploaded_file)
    except: return None
    return None

def find_actual_header(df, keywords):
    """파일 상단의 불필요한 행을 건너뛰고 진짜 제목줄을 찾는 함수"""
    for i in range(len(df)):
        # 해당 행의 모든 값을 문자열로 변환해서 합침
        row_str = " ".join([str(v) for v in df.iloc[i].values])
        # 키워드 중 하나라도 해당 행에 있으면 그 줄이 헤더!
        if any(k in row_str for k in keywords):
            new_df = df.iloc[i+1:].copy()
            new_df.columns = [str(v).strip() for v in df.iloc[i].values]
            return new_df.reset_index(drop=True)
    return df

def clean_and_standardize(df, mapping, keywords):
    if df is None or df.empty: return None
    
    # 1. 진짜 헤더 찾기
    df = find_actual_header(df, keywords)
    
    # 2. 항목명 통일 (Mapping)
    df = df.rename(columns=mapping)
    
    # 3. 필요한 컬럼만 추출
    target_cols = ['날짜', '캠페인명', '광고비', '노출', '클릭']
    for c in target_cols:
        if c not in df.columns: df[c] = 0
            
    # 4. 숫자 데이터 정제 (문자 섞인 숫자 해결)
    for c in ['광고비', '노출', '클릭']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
    return df[target_cols]

# --- 사이드바 ---
st.sidebar.header("📁 데이터 업로드")
up_naver = st.sidebar.file_uploader("1. 네이버 리포트")
up_meta = st.sidebar.file_uploader("2. 메타 리포트")
up_kakao = st.sidebar.file_uploader("3. 카카오 리포트")
up_adobe = st.sidebar.file_uploader("4. 어도비 리포트")

if st.sidebar.button("🚀 통합 분석 시작"):
    combined_list = []
    
    # 네이버 (키워드: 일별, 총비용)
    if up_naver:
        d = clean_standardize(load_data(up_naver), {'일별':'날짜', '캠페인':'캠페인명', '노출수':'노출', '클릭수':'클릭', '총비용(VAT포함,원)':'광고비'}, ['일별', '캠페인', '총비용'])
        if d is not None: combined_list.append(d)
        
    # 메타 (키워드: 캠페인 이름, 지출 금액)
    if up_meta:
        d = clean_standardize(load_data(up_meta), {'일':'날짜', '캠페인 이름':'캠페인명', '지출 금액 (KRW)':'광고비', '클릭(전체)':'클릭'}, ['캠페인 이름', '지출 금액'])
        if d is not None: combined_list.append(d)
        
    # 카카오 (키워드: 비용, 노출수)
    if up_kakao:
        d = clean_standardize(load_data(up_kakao), {'일':'날짜', '캠페인 이름':'캠페인명', '비용':'광고비', '노출수':'노출', '클릭수':'클릭'}, ['비용', '캠페인 이름'])
        if d is not None: combined_list.append(d)

    if combined_list:
        media_df = pd.concat(combined_list, ignore_index=True)
        
        # 어도비 처리
        raw_adobe = load_data(up_adobe)
        if raw_adobe is not None:
            # 어도비는 첫 번째 열을 무조건 캠페인명으로 간주하는 로직 포함
            df_adobe = find_actual_header(raw_adobe, ['Revenue', '방문 횟수', 'Orders'])
            if not df_adobe.empty:
                df_adobe = df_adobe.rename(columns={df_adobe.columns[0]: '캠페인명', 'Revenue':'매출'})
                df_adobe['매출'] = pd.to_numeric(df_adobe['매출'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
                
                # 병합
                final_df = pd.merge(media_df, df_adobe[['캠페인명', '매출']], on='캠페인명', how='left').fillna(0)
                st.success("✅ 모든 데이터 통합 완료!")
                st.dataframe(final_df)
                st.metric("총 광고비", f"{final_df['광고비'].sum():,.0f}원")
                st.metric("총 매출", f"{final_df['매출'].sum():,.0f}원")
            else:
                st.dataframe(media_df)
        else:
            st.success("✅ 매체 데이터 통합 완료")
            st.dataframe(media_df)
