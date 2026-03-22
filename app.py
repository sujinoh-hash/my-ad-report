import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Marketing Dashboard", layout="wide")
st.title("📊 마케팅 성과 통합 실시간 대시보드")

# --- 설정: 본인의 시트 ID만 따옴표 안에 넣으세요 ---
# 예: https://docs.google.com/spreadsheets/d/1u57...YdgY/edit 에서 1u57...YdgY 부분
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"

def get_data(sheet_id):
    # CSV 내보내기용 고정 주소 (gid=0은 첫 번째 탭입니다)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url)
        # 데이터가 있으면 컬럼명을 강제로 맞춤
        if not df.empty:
            df = df.iloc[:, :7] # A열부터 G열까지 7개만 가져옴
            df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
        return df
    except Exception as e:
        st.error(f"⚠️ 연결 실패: {e}")
        return None

if st.button("🔄 데이터 실시간 동기화 (Sync)"):
    with st.spinner("구글 시트에서 데이터를 가져오는 중..."):
        final_df = get_data(SHEET_ID)

    if final_df is not None:
        # 숫자 데이터에서 콤마(,) 등 제거하고 숫자로 변환
        for c in ['노출', '클릭', '채널 친구 수', '광고비']:
            final_df[c] = pd.to_numeric(final_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        # 날짜 정제
        final_df['일자'] = pd.to_datetime(final_df['일자'], errors='coerce').dt.date
        final_df = final_df.dropna(subset=['일자'])
        
        st.success("✅ 동기화 성공!")
        
        # 지표 출력
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 총 광고비", f"{final_df['광고비'].sum():,.0f}원")
        c2.metric("👁️ 총 노출", f"{final_df['노출'].sum():,.0f}회")
        c3.metric("🖱️ 총 클릭", f"{final_df['클릭'].sum():,.0f}회")

        # 그래프
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(final_df, values='광고비', names='매체', title="매체별 비중"), use_container_width=True)
        with g2:
            daily = final_df.groupby('일자')['광고비'].sum().reset_index()
            st.plotly_chart(px.line(daily, x='일자', y='광고비', title="일자별 추이", markers=True), use_container_width=True)

        st.dataframe(final_df.sort_values('일자', ascending=False), use_container_width=True)
