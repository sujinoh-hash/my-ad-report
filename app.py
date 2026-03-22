import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Marketing Dashboard", layout="wide")
st.title("📊 마케팅 성과 통합 실시간 대시보드")

# --- 설정 (본인 ID 확인) ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"

def get_first_tab_data(sheet_id):
    # gid=0을 기본으로 하되, 안되면 첫번째 시트를 시도하는 주소
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df = pd.read_csv(url)
        if df.empty: return None
        # 우리가 약속한 7개 컬럼만 강제로 지정 (오류 방지)
        df = df.iloc[:, :7]
        df.columns = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
        return df
    except Exception as e:
        st.error(f"데이터 연결 오류: {e}")
        return None

if st.button("🔄 데이터 실시간 동기화 (Sync)"):
    with st.spinner("구글 시트에서 데이터를 긁어오는 중..."):
        final_df = get_first_tab_data(SHEET_ID)

    if final_df is not None:
        # 숫자 정제 (콤마 제거 등)
        for c in ['노출', '클릭', '채널 친구 수', '광고비']:
            final_df[c] = pd.to_numeric(final_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        # 날짜 정제
        final_df['일자'] = pd.to_datetime(final_df['일자'], errors='coerce').dt.date
        final_df = final_df.dropna(subset=['일자'])
        
        # --- 지표 출력 ---
        st.success("✅ 동기화 완료!")
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
            st.plotly_chart(px.line(daily, x='일자', y='광고비', title="일자별 추이"), use_container_width=True)

        st.subheader("📋 전체 상세 데이터")
        st.dataframe(final_df.sort_values('일자', ascending=False), use_container_width=True)
    else:
        st.error("⚠️ 데이터를 가져오지 못했습니다. 구글 시트 공유 설정을 다시 확인해 주세요.")
