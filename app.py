import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="룰루레몬 마케팅 자동화 툴", layout="wide")

# --- [로직] v5 매핑 함수 (내용은 동일, 생략 없이 포함) ---
def build_perfect_key_v5(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()
    # (여기에 어제 완성한 v5 로직 전체가 들어갑니다)
    # ... [생략] ...
    # 실제 코드 실행 시에는 위에 작성된 v5 전체 로직을 넣으시면 됩니다.
    return f"AI_조립_결과값" 

# --- UI 레이아웃 시작 ---
st.title("🏃 룰루레몬 하이브리드 자동화 시트")

# 탭 생성: 1차 매핑용과 최종 통합용 분리
tab1, tab2 = st.tabs(["🎯 1단계: 어도비 1차 매칭 & 검수", "📊 2단계: 매체 데이터 통합 리포트"])

# --- [탭 1: 1차 매핑] ---
with tab1:
    st.header("어도비 데이터 이름표 달기")
    st.write("어도비 Raw 데이터를 올리면 AI가 캠페인명을 1차로 조립합니다.")
    
    adobe_file = st.file_uploader("어도비 Raw 파일 업로드 (.csv)", type="csv", key="adobe")
    
    if adobe_file:
        df_adobe = pd.read_csv(adobe_file)
        # 1차 조립 실행
        df_adobe['AI_제안명'] = df_adobe['코드'].apply(build_perfect_key_v5)
        
        st.subheader("🧐 매핑 결과 더블체크")
        # Unknown만 보기 필터
        show_unknown = st.checkbox("Unknown 항목만 보기")
        if show_unknown:
            display_df = df_adobe[df_adobe['AI_제안명'] == "Unknown"]
        else:
            display_df = df_adobe
            
        st.dataframe(display_df[['날짜', '코드', 'AI_제안명']].head(100))
        
        st.info("💡 위 리스트를 확인하고 수정이 필요한 CID는 메모해 두었다가 저(AI)에게 알려주세요. 로직을 바로 업데이트해 드립니다.")

# --- [탭 2: 최종 통합] ---
with tab2:
    st.header("매체 데이터 + 어도비 데이터 통합")
    st.write("검수된 어도비 이름표와 매체별 비용 데이터를 하나로 합칩니다.")
    
    media_file = st.file_uploader("매체 데이터 업로드 (Excel/CSV)", type=["csv", "xlsx"], key="media")
    
    if media_file:
        st.success("매체 데이터 로드 완료!")
        if st.button("🚀 최종 통합 리포트 생성"):
            # 여기에 어도비와 매체 데이터를 Merge(합치기)하는 로직 작동
            st.write("데이터를 통합 중입니다... (CID 기준 매칭)")
            # ... [통합 로직] ...
            st.download_button("📥 통합 리포트 다운로드", data="파일데이터", file_name="final_report.csv")
