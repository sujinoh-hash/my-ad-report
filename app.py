import streamlit as st
import pandas as pd

# 1. 웹 화면 설정 (MBO용 멋진 제목)
st.set_page_config(page_title="AD-Adobe Data Integration System", layout="wide")
st.title("🚀 마케팅 성과 통합 자동화 솔루션 (v1.0)")
st.markdown("---")

# 2. 사이드바: 파일 업로드 공간
st.sidebar.header("📁 리포트 업로드 (Excel/CSV)")
uploaded_naver = st.sidebar.file_uploader("1. 네이버 리포트")
uploaded_meta = st.sidebar.file_uploader("2. 메타 리포트")
uploaded_kakao = st.sidebar.file_uploader("3. 카카오 리포트")
uploaded_adobe = st.sidebar.file_uploader("4. 어도비 리포트")

# 3. 데이터 통합 로직 (핵심 엔진)
def process_data():
    all_media = []
    
    # [네이버 처리]
    if uploaded_naver:
        df = pd.read_csv(uploaded_naver) if "csv" in uploaded_naver.name else pd.read_excel(uploaded_naver)
        df = df.rename(columns={'일별': '날짜', '캠페인': '캠페인명', '총비용(VAT포함,원)': '광고비', '노출수': '노출', '클릭수': '클릭'})
        all_media.append(df[['날짜', '캠페인명', '노출', '클릭', '광고비']])

    # [메타 처리]
    if uploaded_meta:
        df = pd.read_excel(uploaded_meta) # 보통 메타는 엑셀
        df = df.rename(columns={'일': '날짜', '캠페인 이름': '캠페인명', '지출 금액 (KRW)': '광고비', '클릭(전체)': '클릭'})
        all_media.append(df[['날짜', '캠페인명', '노출', '클릭', '광고비']])

    # [카카오 처리]
    if uploaded_kakao:
        df = pd.read_excel(uploaded_kakao)
        df = df.rename(columns={'일': '날짜', '비용': '광고비', '노출수': '노출', '클릭수': '클릭'})
        all_media.append(df[['날짜', '캠페인명', '노출', '클릭', '광고비']])

    if not all_media:
        st.warning("매체 리포트를 하나 이상 업로드해주세요.")
        return None

    # 매체 통합
    df_media = pd.concat(all_media)

    # [어도비 처리 & 매핑]
    if uploaded_adobe:
        df_adobe = pd.read_excel(uploaded_adobe)
        # 아까 정한 암호번역기 로직 (샘플)
        # 실제로는 '단서' 컬럼을 기준으로 '캠페인명'을 만들어주는 과정이 들어갑니다.
        # 여기서는 날짜와 캠페인명 기준으로 단순 병합 예시를 보여줍니다.
        df_final = pd.merge(df_media, df_adobe, on=['날짜', '캠페인명'], how='left')
        return df_final

# 4. 결과 출력 및 대시보드
if st.sidebar.button("📊 통합 대시보드 생성"):
    final_df = process_data()
    if final_df is not None:
        st.success("✅ 데이터 통합 성공!")
        
        # 주요 지표 (KPI)
        col1, col2, col3 = st.columns(3)
        col1.metric("총 광고비", f"{final_df['광고비'].sum():,.0}원")
        col2.metric("총 매출", f"{final_df['Revenue'].sum():,.0}원")
        col3.metric("평균 ROAS", f"{(final_df['Revenue'].sum()/final_df['광고비'].sum()*100):.1f}%")

        # 성과 테이블
        st.dataframe(final_df)
        
        # 다운로드 버튼
        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("💾 통합 리포트 다운로드(CSV)", data=csv, file_name="integrated_report.csv")
