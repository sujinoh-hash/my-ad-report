import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Marketing Dashboard", layout="wide")
st.title("📊 마케팅 성과 통합 실시간 대시보드")

# --- 1. 여기에 구글 시트 주소를 '통째로' 붙여넣으세요 ---
# 예: "https://docs.google.com/spreadsheets/d/1u57...YdgY/edit#gid=0"
MY_SHEET_URL = "여기에_구글시트_전체_주소를_넣으세요"

# 주소에서 ID만 자동으로 뽑아내는 함수
def extract_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

SHEET_ID = extract_id(MY_SHEET_URL)

def get_data(sheet_id):
    # CSV로 내보내기 위한 특수 주소 조합
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url)
        # 시트의 1~7열(일자~광고비) 강제 지정
        df = df.iloc[:, :7]
        df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
        return df
    except Exception as e:
        st.error(f"⚠️ 연결 실패: {e}")
        return None

if st.button("🔄 데이터 실시간 동기화 (Sync)"):
    if not SHEET_ID:
        st.error("❌ 구글 시트 주소가 올바르지 않습니다.")
    else:
        with st.spinner("데이터를 가져오는 중..."):
            final_df = get_data(SHEET_ID)

        if final_df is not None:
            # 숫자 데이터 정제 (숫자 외 문자 제거)
            for c in ['노출', '클릭', '채널 친구 수', '광고비']:
                final_df[c] = pd.to_numeric(final_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
            # 날짜 정제
            final_df['일자'] = pd.to_datetime(final_df['일자'], errors='coerce').dt.date
            final_df = final_df.dropna(subset=['일자'])
            
            st.success("✅ 동기화 성공!")
            
            # 상단 지표
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 총 광고비", f"{final_df['광고비'].sum():,.0f}원")
            c2.metric("👁️ 총 노출", f"{final_df['노출'].sum():,.0f}회")
            c3.metric("🖱️ 총 클릭", f"{final_df['클릭'].sum():,.0f}회")

            # 그래프
            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(px.pie(final_df, values='광고비', names='매체', title="매체별 비중", hole=0.4), use_container_width=True)
            with g2:
                daily = final_df.groupby('일자')['광고비'].sum().reset_index()
                st.plotly_chart(px.line(daily, x='일자', y='광고비', title="일자별 추이", markers=True), use_container_width=True)

            st.subheader("📋 상세 데이터 리스트")
            st.dataframe(final_df.sort_values('일자', ascending=False), use_container_width=True)
