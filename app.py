import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Marketing Data Master", layout="wide")
st.title("🏆 마케팅 성과 통합 자동화 솔루션 (v1.2)")

# --- 1. 파일 읽기 함수 (인코딩 오류 완벽 해결 버전) ---
def load_data(uploaded_file):
    if uploaded_file is not None:
        filename = uploaded_file.name
        try:
            if filename.endswith('.csv'):
                # 1차 시도: utf-8-sig (엑셀 호환 한국어)
                try:
                    return pd.read_csv(uploaded_file, encoding='utf-8-sig')
                except:
                    # 2차 시도: cp949 (일반적인 윈도우 한국어)
                    try:
                        uploaded_file.seek(0) # 파일 읽기 위치 초기화
                        return pd.read_csv(uploaded_file, encoding='cp949')
                    except:
                        # 3차 시도: utf-16 (0xff 오류가 날 때 주로 사용)
                        uploaded_file.seek(0)
                        return pd.read_csv(uploaded_file, encoding='utf-16', sep='\t')
            else:
                # 엑셀 파일 읽기
                return pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"'{filename}' 파일을 읽는 중 오류가 발생했습니다: {e}")
    return None

def clean_media(df, mapping):
    if df is None: return None
    # 항목 이름 변경
    df = df.rename(columns=mapping)
    # 필요한 컬럼만 추출 (매체에 따라 없는 컬럼은 0으로 채움)
    cols = ['날짜', '캠페인명', '광고비', '노출', '클릭']
    for col in cols:
        if col not in df.columns:
            df[col] = 0
            
    # 광고비 숫자화 (콤마, 원화 기호 제거)
    df['광고비'] = pd.to_numeric(df['광고비'].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''), errors='coerce').fillna(0)
    return df[cols]

# --- 2. 사이드바 구성 ---
st.sidebar.header("📁 데이터 업로드")
up_naver = st.sidebar.file_uploader("1. 네이버")
up_meta = st.sidebar.file_uploader("2. 메타")
up_kakao = st.sidebar.file_uploader("3. 카카오")
up_adobe = st.sidebar.file_uploader("4. 어도비")

# --- 3. 통합 로직 ---
if st.sidebar.button("🚀 통합 분석 시작"):
    all_media_list = []
    
    # 각 매체별 로드 및 정리
    if up_naver:
        df = load_data(up_naver)
        all_media_list.append(clean_media(df, {'일별':'날짜', '캠페인':'캠페인명', '노출수':'노출', '클릭수':'클릭', '총비용(VAT포함,원)':'광고비'}))
    if up_meta:
        df = load_data(up_meta)
        all_media_list.append(clean_media(df, {'일':'날짜', '캠페인 이름':'캠페인명', '지출 금액 (KRW)':'광고비', '클릭(전체)':'클릭'}))
    if up_kakao:
        df = load_data(up_kakao)
        all_media_list.append(clean_media(df, {'일':'날짜', '비용':'광고비', '노출수':'노출', '클릭수':'클릭'}))

    if all_media_list:
        media_df = pd.concat(all_media_list, ignore_index=True)
        
        # 어도비 합치기
        df_adobe = load_data(up_adobe)
        if df_adobe is not None:
            df_adobe = df_adobe.rename(columns={'방문 횟수':'방문', 'Revenue':'매출', 'Orders':'주문'})
            # 여기서 암호 번역(Mapping)을 추가할 수 있습니다.
            # 일단 캠페인명이 같다고 가정하고 합칩니다.
            final_df = pd.merge(media_df, df_adobe, on='캠페인명', how='left').fillna(0)
            st.success("✅ 매체 및 어도비 통합 완료!")
            st.dataframe(final_df)
        else:
            st.success("✅ 매체 통합 완료 (어도비 미포함)")
            st.dataframe(media_df)
    else:
        st.warning("먼저 파일을 업로드해주세요.")
