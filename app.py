import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Ad Dashboard v3.0", layout="wide")
st.title("📊 마케팅 성과 통합 실시간 대시보드")

# --- 설정 (ID 확인 필수!) ---
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"
TABS = {"Naver": "0", "Meta": "12345678", "Kakao": "98765432"}

def get_sheet_data(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        if df.empty: return None
        
        # 💡 [무적 보정 로직] 헤더의 공백을 제거하고 이름을 강제로 표준화합니다.
        df.columns = [str(c).replace(' ', '').strip() for c in df.columns]
        
        # 우리가 필요한 표준 이름들
        standard_cols = {'일자':'일자', '매체':'매체', '캠페인명':'캠페인명', '노출':'노출', '클릭':'클릭', '채널친구수':'채널 친구 수', '광고비':'광고비'}
        df = df.rename(columns=standard_cols)
        
        return df
    except:
        return None

if st.button("🔄 구글 시트 데이터 실시간 동기화"):
    all_data = []
    with st.spinner("데이터를 정밀 분석하며 가져오고 있습니다..."):
        for name, gid in TABS.items():
            df = get_sheet_data(SHEET_ID, gid)
            if df is not None:
                # 💡 부족한 컬럼은 자동으로 0으로 채워넣기
                target_cols = ['일자', '매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
                for col in target_cols:
                    if col not in df.columns:
                        df[col] = 0
                
                # 숫자 데이터 강제 변환 (문자가 섞여있어도 숫자로 바꿈)
                for c in ['노출', '클릭', '채널 친구 수', '광고비']:
                    df[c] = pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
                
                all_data.append(df[target_cols])

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # 날짜 형식 정리
        final_df['일자'] = pd.to_datetime(final_df['일자'], errors='coerce').dt.date
        final_df = final_df.dropna(subset=['일자']) # 날짜 없는 줄은 버림
        
        # --- 결과 출력 ---
        st.success("✅ 동기화에 성공했습니다!")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 총 광고비", f"{final_df['광고비'].sum():,.0f}원")
        c2.metric("👁️ 총 노출", f"{final_df['노출'].sum():,.0f}회")
        c3.metric("🖱️ 총 클릭", f"{final_df['클릭'].sum():,.0f}회")
        # CTR (클릭률) 자동 계산 서비스!
        ctr = (final_df['클릭'].sum() / final_df['노출'].sum() * 100) if final_df['노출'].sum() > 0 else 0
        c4.metric("📈 평균 클릭률(CTR)", f"{ctr:.2f}%")

        # 그래프
        col_left, col_right = st.columns(2)
        with col_left:
            st.plotly_chart(px.pie(final_df, values='광고비', names='매체', title="매체별 지출 비중"), use_container_width=True)
        with col_right:
            daily_trend = final_df.groupby('일자')['광고비'].sum().reset_index()
            st.plotly_chart(px.line(daily_trend, x='일자', y='광고비', title="일자별 광고비 추이"), use_container_width=True)

        st.subheader("📋 통합 데이터 상세 보기")
        st.dataframe(final_df.sort_values('일자', ascending=False), use_container_width=True)
    else:
        st.error("⚠️ 시트에서 유효한 데이터를 찾지 못했습니다. 시트 공유 설정과 데이터가 입력되었는지 다시 확인해주세요.")
