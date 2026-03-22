import streamlit as st
import pandas as pd

st.set_page_config(page_title="Hybrid Marketing Dashboard", layout="wide")
st.title("🚀 하이브리드 성과 통합 대시보드")

# --- 설정 (본인의 시트 ID를 넣으세요) ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"

TABS = {
    "Naver": "0",
    "Meta": "12345678", 
    "Kakao": "98765432"
}

def get_sheet_data(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        if df.empty: return None
        return df
    except:
        return None

if st.button("🔄 구글 시트 데이터 실시간 동기화"):
    all_data = []
    
    with st.spinner("데이터를 불러오는 중..."):
        for name, gid in TABS.items():
            df = get_sheet_data(SHEET_ID, gid)
            if df is not None:
                # 💡 사용자가 요청한 순서: 일자, 매체, 캠페인명, 노출, 클릭, 채널 친구 수, 광고비
                cols = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
                
                # 없는 컬럼은 0 또는 빈값 처리
                for c in cols:
                    if c not in df.columns: df[c] = 0
                
                # 숫자 데이터 정제
                for num_col in ['노출', '클릭', '채널 친구 수', '광고비']:
                    df[num_col] = pd.to_numeric(df[num_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
                
                all_data.append(df[cols])

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # 날짜순 정렬 (일자 컬럼이 날짜 형식일 경우)
        final_df['일자'] = pd.to_datetime(final_df['일자'], errors='coerce').dt.date
        final_df = final_df.sort_values(by='일자', ascending=False)
        
        st.success(f"✅ 데이터를 성공적으로 불러왔습니다!")
        
        # 상단 요약 지표
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 광고비", f"{final_df['광고비'].sum():,.0f}원")
        c2.metric("총 노출", f"{final_df['노출'].sum():,.0f}회")
        c3.metric("총 클릭", f"{final_df['클릭'].sum():,.0f}회")
        c4.metric("총 채널친구", f"{final_df['채널 친구 수'].sum():,.0f}명")

        st.divider()
        st.subheader("📊 통합 매체 성과 리포트")
        st.dataframe(final_df, use_container_width=True)
    else:
        st.error("⚠️ 데이터를 불러오지 못했습니다. 구글 시트의 헤더명(일자,
