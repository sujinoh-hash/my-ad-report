import streamlit as st
import pandas as pd

st.set_page_config(page_title="AD-Adobe Integration", layout="wide")
st.title("🚀 마케팅 성과 통합 자동화 솔루션 (Multi-Channel)")

# --- 데이터 처리 함수 (이름 통일 엔진) ---
def clean_and_unify(df, mapping_dict):
    # 1. 항목 이름 변경 (번역기 돌리기)
    df = df.rename(columns=mapping_dict)
    
    # 2. 필요한 핵심 항목만 추출 (없으면 에러 방지용)
    cols_to_keep = ['날짜', '캠페인명', '광고비', '노출', '클릭']
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    
    # 3. 데이터 타입 정리 (숫자에 콤마나 문자가 섞여있을 때를 대비)
    if '광고비' in df.columns:
        df['광고비'] = pd.to_numeric(df['광고비'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
    return df[existing_cols]

# --- 파일 업로드 ---
st.sidebar.header("📁 매체별 리포트 업로드")
up_naver = st.sidebar.file_uploader("1. 네이버")
up_meta = st.sidebar.file_uploader("2. 메타")
up_kakao = st.sidebar.file_uploader("3. 카카오")
up_adobe = st.sidebar.file_uploader("4. 어도비")

if st.sidebar.button("📊 통합 리포트 생성"):
    combined_list = []

    # 네이버 번역 규칙
    if up_naver:
        df = pd.read_csv(up_naver) if "csv" in up_naver.name else pd.read_excel(up_naver)
        df_clean = clean_and_unify(df, {'일별':'날짜', '캠페인':'캠페인명', '노출수':'노출', '클릭수':'클릭', '총비용(VAT포함,원)':'광고비'})
        df_clean['매체'] = '네이버'
        combined_list.append(df_clean)

    # 메타 번역 규칙
    if up_meta:
        df = pd.read_excel(up_meta)
        df_clean = clean_and_unify(df, {'일':'날짜', '캠페인 이름':'캠페인명', '지출 금액 (KRW)':'광고비', '클릭(전체)':'클릭'})
        df_clean['매체'] = '메타'
        combined_list.append(df_clean)

    # 카카오 번역 규칙
    if up_kakao:
        df = pd.read_excel(up_kakao)
        df_clean = clean_and_unify(df, {'일':'날짜', '비용':'광고비', '노출수':'노출', '클릭수':'클릭'})
        df_clean['매체'] = '카카오'
        combined_list.append(df_clean)

    # --- 최종 결과 출력 ---
    if combined_list:
        final_df = pd.concat(combined_list, ignore_index=True)
        st.success("✅ 모든 매체 데이터가 성공적으로 통합되었습니다!")
        
        # 성과 요약 (KPI)
        total_spend = final_df['광고비'].sum()
        st.metric("총 통합 광고비", f"{total_spend:,.0f}원")
        
        # 데이터 테이블
        st.dataframe(final_df)
    else:
        st.warning("업로드된 파일이 없습니다.")
