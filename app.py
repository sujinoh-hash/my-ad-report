import streamlit as st
import pandas as pd

st.set_page_config(page_title="Hybrid Marketing Dashboard", layout="wide")
st.title("🚀 하이브리드 성과 통합 대시보드")

# --- 설정 (여기에 본인의 구글 시트 주소를 넣으세요) ---
# 시트 주소 예시: https://docs.google.com/spreadsheets/d/시트아이디/edit#gid=0
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"

# 각 탭의 GID (주소창 끝에 gid= 다음에 나오는 숫자입니다)
TABS = {
    "Naver": "0",          # 기본 첫번째 탭은 보통 0입니다.
    "Meta": "12345678",    # 실제 시트 하단 탭을 클릭했을 때 주소창의 gid 숫자를 넣으세요.
    "Kakao": "98765432",
    "Adobe": "11223344"
}

def get_sheet_data(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        return pd.read_csv(url)
    except:
        return None

# --- 대시보드 로직 ---
if st.button("🔄 구글 시트 데이터 실시간 동기화"):
    st.info("구글 시트에서 데이터를 불러오는 중입니다...")
    all_data = []

    for name, gid in TABS.items():
        df = get_sheet_data(SHEET_ID, gid)
        if df is not None:
            # 필수 컬럼 순서 고정 및 숫자 정제
            cols = ['매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
            for c in cols:
                if c not in df.columns: df[c] = 0
            
            # 숫자 데이터 클리닝
            for num_col in ['노출', '클릭', '채널 친구 수', '광고비']:
                df[num_col] = pd.to_numeric(df[num_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
            all_data.append(df[cols])

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # 성과 요약 (KPI)
        c1, c2, c3 = st.columns(3)
        c1.metric("총 광고 집행비", f"{final_df['광고비'].sum():,.0f}원")
        c2.metric("총 노출수", f"{final_df['노출'].sum():,.0f}회")
        c3.metric("총 클릭수", f"{final_df['클릭'].sum():,.0f}회")

        st.divider()
        st.subheader("📊 통합 매체 성과표")
        st.dataframe(final_df, use_container_width=True)
        
        # 매체별 비중 그래프 (옵션)
        st.bar_chart(final_df.groupby('매체')['광고비'].sum())
    else:
        st.error("데이터를 불러오지 못했습니다. 시트 ID와 GID를 확인해주세요.")

st.sidebar.markdown("### 💡 하이브리드 가이드")
st.sidebar.write("1. 구글 시트에 데이터를 붙여넣습니다.")
st.sidebar.write("2. '동기화' 버튼을 누릅니다.")
st.sidebar.write("3. 끝! 코드는 더 이상 건드리지 마세요.")
