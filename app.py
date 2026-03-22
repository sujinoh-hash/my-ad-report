import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="AD-Adobe Integration", layout="wide")
st.title("🚀 마케팅 성과 통합 자동화 솔루션 (Multi-Format)")

# --- 파일 읽기 통합 함수 (CSV/Excel 모두 대응) ---
def load_data(uploaded_file):
    if uploaded_file is not None:
        filename = uploaded_file.name
        try:
            if filename.endswith('.csv'):
                # CSV 파일 읽기 (한국어 깨짐 방지용 encoding 추가)
                return pd.read_csv(uploaded_file, encoding='utf-8-sig')
            else:
                # 엑셀 파일 읽기
                return pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"{filename} 파일을 읽는 중 오류가 발생했습니다: {e}")
    return None

def clean_and_unify(df, mapping_dict):
    if df is None: return None
    df = df.rename(columns=mapping_dict)
    cols_to_keep = ['날짜', '캠페인명', '광고비', '노출', '클릭']
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    
    # 광고비 숫자 변환 (콤마 제거 등)
    if '광고비' in df.columns:
        df['광고비'] = pd.to_numeric(df['광고비'].astype(str).str.replace(',', '').str.replace('₩', ''), errors='coerce').fillna(0)
    
    return df[existing_cols]

# --- 사이드바 및 업로드 ---
st.sidebar.header("📁 매체별 리포트 업로드")
up_naver = st.sidebar.file_uploader("1. 네이버 (CSV/Excel)")
up_meta = st.sidebar.file_uploader("2. 메타 (CSV/Excel)")
up_kakao = st.sidebar.file_uploader("3. 카카오 (CSV/Excel)")

if st.sidebar.button("📊 통합 리포트 생성"):
    combined_list = []

    # 네이버
    df_n = load_data(up_naver)
    if df_n is not None:
        c_n = clean_and_unify(df_n, {'일별':'날짜', '캠페인':'캠페인명', '노출수':'노출', '클릭수':'클릭', '총비용(VAT포함,원)':'광고비'})
        c_n['매체'] = '네이버'
        combined_list.append(c_n)

    # 메타
    df_m = load_data(up_meta)
    if df_m is not None:
        c_m = clean_and_unify(df_m, {'일':'날짜', '캠페인 이름':'캠페인명', '지출 금액 (KRW)':'광고비', '클릭(전체)':'클릭'})
        c_m['매체'] = '메타'
        combined_list.append(c_m)

    # 카카오
    df_k = load_data(up_kakao)
    if df_k is not None:
        c_k = clean_and_unify(df_k, {'일':'날짜', '비용':'광고비', '노출수':'노출', '클릭수':'클릭'})
        c_k['매체'] = '카카오'
        combined_list.append(c_k)

    if combined_list:
        final_df = pd.concat(combined_list, ignore_index=True)
        st.success("✅ 통합 완료!")
        st.metric("총 광고비", f"{final_df['광고비'].sum():,.0f}원")
        st.dataframe(final_df)
    else:
        st.warning("파일을 먼저 업로드해 주세요.")
