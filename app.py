import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marketing Analytics Master", layout="wide")
st.title("🏆 마케팅 성과 통합 자동화 솔루션")

def load_data(uploaded_file):
    if uploaded_file is None: return None
    try:
        if uploaded_file.name.endswith('.csv'):
            for enc in ['utf-8-sig', 'cp949', 'utf-16', 'latin1']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=enc, sep=None, engine='python', comment='#', skip_blank_lines=True)
                    if not df.empty: return df
                except: continue
        else:
            return pd.read_excel(uploaded_file)
    except: return None
    return None

def find_actual_header(df, keywords):
    if df is None: return None
    # 데이터프레임의 상위 30줄을 뒤져서 키워드가 있는 행을 찾음
    for i in range(len(df)):
        row_values = [str(v).strip() for v in df.iloc[i].values]
        row_text = " ".join(row_values)
        if any(k in row_text for k in keywords):
            new_df = df.iloc[i+1:].copy()
            new_df.columns = row_values
            return new_df.reset_index(drop=True)
    return df

def process_and_clean(df, mapping, keywords, media_name):
    if df is None or df.empty: return None
    
    # 1. 헤더 탐색 (네이버 등의 복잡한 상단 제목 건너뛰기)
    df = find_actual_header(df, keywords)
    
    # 2. 제목 공백 제거 및 매핑
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns=mapping)
    
    # 3. 요청하신 필수 컬럼 설정 (순서 고정)
    df['매체'] = media_name
    target_cols = ['매체', '캠페인명', '노출', '클릭', '채널 친구 수', '광고비']
    
    # 없는 컬럼은 0으로 생성 (예: 네이버엔 '채널 친구 수'가 없으므로 0 처리)
    for c in target_cols:
        if c not in df.columns:
            df[c] = 0
            
    # 4. 숫자 데이터 정제
    for c in ['노출', '클릭', '채널 친구 수', '광고비']:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
    return df[target_cols]

# --- 사이드바 ---
st.sidebar.header("📁 매체 리포트 업로드")
up_naver = st.sidebar.file_uploader("1. 네이버")
up_meta = st.sidebar.file_uploader("2. 메타")
up_kakao = st.sidebar.file_uploader("3. 카카오")

if st.sidebar.button("🚀 통합 분석 시작"):
    combined_list = []
    
    # 네이버 (항목: 일별, 캠페인, 총비용 등)
    if up_naver:
        d = process_and_clean(load_data(up_naver), 
                              {'일별':'날짜', '캠페인':'캠페인명', '노출수':'노출', '클릭수':'클릭', '총비용(VAT포함,원)':'광고비'}, 
                              ['일별', '총비용', '캠페인'], "네이버")
        if d is not None: combined_list.append(d)
        
    # 메타 (항목: 캠페인 이름, 지출 금액 등)
    if up_meta:
        d = process_and_clean(load_data(up_meta), 
                              {'캠페인 이름':'캠페인명', '지출 금액 (KRW)':'광고비', '클릭(전체)':'클릭'}, 
                              ['캠페인 이름', '지출 금액'], "메타")
        if d is not None: combined_list.append(d)
        
    # 카카오 (항목: 캠페인 이름, 비용, 채널 추가 등)
    if up_kakao:
        # 카카오의 경우 '채널 추가' 항목이 있으면 '채널 친구 수'로 매핑
        d = process_and_clean(load_data(up_kakao), 
                              {'캠페인 이름':'캠페인명', '비용':'광고비', '노출수':'노출', '클릭수':'클릭', '채널 추가':'채널 친구 수'}, 
                              ['비용', '캠페인 이름'], "카카오")
        if d is not None: combined_list.append(d)

    if combined_list:
        final_df = pd.concat(combined_list, ignore_index=True)
        st.success("✅ 매체 데이터 통합 완료!")
        
        # 총액 요약
        st.metric("통합 총 광고비", f"{final_df['광고비'].sum():,.0f}원")
        
        # 결과 표 (사용자 요청 순서 반영)
        st.dataframe(final_df)
    else:
        st.warning("파일을 먼저 업로드해주세요.")
