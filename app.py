import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Marketing Analytics Master", layout="wide")
st.title("🏆 마케팅 성과 통합 자동화 솔루션 (v1.5)")

def load_data(uploaded_file):
    if uploaded_file is None: return None
    filename = uploaded_file.name
    try:
        if filename.endswith('.csv'):
            # 모든 인코딩과 구분자를 시도하는 무적의 읽기 로직
            for enc in ['utf-8-sig', 'cp949', 'utf-16', 'latin1']:
                try:
                    uploaded_file.seek(0)
                    # 헤더(첫줄)를 찾기 위해 빈 줄은 무시하고 읽기
                    df = pd.read_csv(uploaded_file, encoding=enc, sep=None, engine='python', on_bad_lines='skip')
                    if not df.empty: return df
                except:
                    continue
            return None
        else:
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"'{filename}' 읽기 오류: {e}")
        return None

def clean_media(df, mapping):
    if df is None: return None
    
    # 💡 [중요] 컬럼명에 공백이 있을 수 있으니 공백 제거
    df.columns = [str(c).strip() for c in df.columns]
    
    # 💡 [중요] 실제 데이터가 시작되는 행 찾기 (헤더가 첫 줄이 아닐 경우 대비)
    # 매핑하려는 단어 중 하나라도 포함된 행을 찾습니다.
    target_keys = list(mapping.keys())
    for i in range(len(df)):
        row_values = [str(v) for v in df.iloc[i].values]
        if any(key in row_values for key in target_keys):
            df.columns = row_values
            df = df.iloc[i+1:].reset_index(drop=True)
            break

    df = df.rename(columns=mapping)
    cols = ['날짜', '캠페인명', '광고비', '노출', '클릭']
    
    # 없는 컬럼은 0으로 생성
    for col in cols:
        if col not in df.columns: df[col] = 0
            
    # 숫자 데이터 정제
    for col in ['광고비', '노출', '클릭']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    
    return df[cols]

# --- 화면 구성 ---
st.sidebar.header("📁 데이터 업로드")
up_naver = st.sidebar.file_uploader("1. 네이버")
up_meta = st.sidebar.file_uploader("2. 메타")
up_kakao = st.sidebar.file_uploader("3. 카카오")
up_adobe = st.sidebar.file_uploader("4. 어도비")

if st.sidebar.button("🚀 통합 분석 시작"):
    all_media_list = []
    
    if up_naver:
        df = load_data(up_naver)
        # 네이버 항목 이름 정확히 매칭 (일별, 캠페인)
        all_media_list.append(clean_media(df, {'일별':'날짜', '캠페인':'캠페인명', '노출수':'노출', '클릭수':'클릭', '총비용(VAT포함,원)':'광고비'}))
    if up_meta:
        df = load_data(up_meta)
        all_media_list.append(clean_media(df, {'일':'날짜', '캠페인 이름':'캠페인명', '지출 금액 (KRW)':'광고비', '클릭(전체)':'클릭'}))
    if up_kakao:
        df = load_data(up_kakao)
        # 카카오는 '캠페인 이름', '비용' 등을 씁니다.
        all_media_list.append(clean_media(df, {'일':'날짜', '캠페인 이름':'캠페인명', '비용':'광고비', '노출수':'노출', '클릭수':'클릭'}))

    if all_media_list:
        media_df = pd.concat(all_media_list, ignore_index=True)
        
        # 어도비 처리 (매출 합치기)
        df_adobe = load_data(up_adobe)
        if df_adobe is not None:
            # 어도비의 컬럼명 공백 제거 및 이름 변경
            df_adobe.columns = [str(c).strip() for c in df_adobe.columns]
            df_adobe = df_adobe.rename(columns={'캠페인':'캠페인명', 'Revenue':'매출', 'Orders':'주문'})
            
            # 매출 데이터 숫자화
            if '매출' in df_adobe.columns:
                df_adobe['매출'] = pd.to_numeric(df_adobe['매출'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
            # 최종 결합
            final_df = pd.merge(media_df, df_adobe[['캠페인명', '매출']], on='캠페인명', how='left').fillna(0)
            st.success("✅ 매체 및 어도비 통합 성공!")
            st.dataframe(final_df)
            
            # KPI 요약
            st.metric("총 통합 광고비", f"{final_df['광고비'].sum():,.0f}원")
            st.metric("총 통합 매출", f"{final_df['매출'].sum():,.0f}원")
        else:
            st.success("✅ 매체 데이터 통합 완료!")
            st.dataframe(media_df)
