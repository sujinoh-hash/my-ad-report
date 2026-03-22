import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marketing Analytics Master", layout="wide")
st.title("🏆 마케팅 성과 통합 자동화 솔루션 (Final)")

def load_data(uploaded_file):
    if uploaded_file is None: return None
    filename = uploaded_file.name
    try:
        if filename.endswith('.csv'):
            for enc in ['utf-8-sig', 'cp949', 'utf-16', 'latin1']:
                try:
                    uploaded_file.seek(0)
                    # #으로 시작하는 주석은 무시
                    df = pd.read_csv(uploaded_file, encoding=enc, sep=None, engine='python', comment='#', skip_blank_lines=True)
                    if not df.empty: return df
                except: continue
            return None
        else:
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"'{filename}' 읽기 오류: {e}")
        return None

def clean_df(df, mapping, is_adobe=False):
    if df is None or df.empty: return None
    
    temp_df = df.copy()
    # 진짜 헤더 찾기 (20줄 이내 탐색)
    for i in range(min(len(temp_df), 20)):
        row_values = [str(v).strip() for v in temp_df.iloc[i].values]
        # 어도비 항목명(방문 횟수, Revenue 등)이나 매체 키워드가 있는지 확인
        if any(k in row_values for k in ['방문 횟수', 'Revenue', '일별', '캠페인', '캠페인 이름']):
            temp_df.columns = row_values
            temp_df = temp_df.iloc[i+1:].reset_index(drop=True)
            break
            
    temp_df.columns = [str(c).strip() for c in temp_df.columns]
    
    # 💡 [어도비 특수 처리] 첫 번째 열을 '캠페인명'으로 강제 지정
    if is_adobe and len(temp_df.columns) > 0:
        first_col = temp_df.columns[0]
        temp_df = temp_df.rename(columns={first_col: '캠페인명'})
    
    temp_df = temp_df.rename(columns=mapping)
    return temp_df

# --- 사이드바 ---
st.sidebar.header("📁 데이터 업로드")
up_naver = st.sidebar.file_uploader("1. 네이버")
up_meta = st.sidebar.file_uploader("2. 메타")
up_kakao = st.sidebar.file_uploader("3. 카카오")
up_adobe = st.sidebar.file_uploader("4. 어도비 리포트")

if st.sidebar.button("🚀 통합 분석 시작"):
    all_media_list = []
    
    # 1. 매체 데이터 정리
    if up_naver:
        all_media_list.append(clean_df(load_data(up_naver), {'일별':'날짜', '캠페인':'캠페인명', '노출수':'노출', '클릭수':'클릭', '총비용(VAT포함,원)':'광고비'}))
    if up_meta:
        all_media_list.append(clean_df(load_data(up_meta), {'일':'날짜', '캠페인 이름':'캠페인명', '지출 금액 (KRW)':'광고비', '클릭(전체)':'클릭'}))
    if up_kakao:
        all_media_list.append(clean_df(load_data(up_kakao), {'일':'날짜', '캠페인 이름':'캠페인명', '비용':'광고비', '노출수':'노출', '클릭수':'클릭'}))

    if all_media_list:
        media_df = pd.concat(all_media_list, ignore_index=True)
        for c in ['광고비', '노출', '클릭']:
            media_df[c] = pd.to_numeric(media_df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

        # 2. 어도비 정리
        df_adobe_raw = load_data(up_adobe)
        if df_adobe_raw is not None:
            # 주신 항목명 그대로 매핑
            adobe_mapping = {
                '방문 횟수': '방문',
                'Revenue': '매출',
                'Orders': '주문',
                'Cart Adds': '장바구니'
            }
            df_adobe = clean_df(df_adobe_raw, adobe_mapping, is_adobe=True)
            
            # 매출 데이터 숫자화
            if '매출' in df_adobe.columns:
                df_adobe['매출'] = pd.to_numeric(df_adobe['매출'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

            # 3. 결합 (Merge)
            # 매체 데이터의 '캠페인명'과 어도비의 '캠페인명(첫번째 열)'을 합칩니다.
            final_df = pd.merge(media_df, df_adobe[['캠페인명', '매출']], on='캠페인명', how='left').fillna(0)
            
            st.success("✅ 매체 데이터와 어도비 매출이 통합되었습니다!")
            
            # 성과 요약
            col1, col2, col3 = st.columns(3)
            col1.metric("총 광고비", f"{final_df['광고비'].sum():,.0f}원")
            col2.metric("총 매출", f"{final_df['매출'].sum():,.0f}원")
            roas = (final_df['매출'].sum() / final_df['광고비'].sum() * 100) if final_df['광고비'].sum() > 0 else 0
            col3.metric("통합 ROAS", f"{roas:.1f}%")
            
            st.dataframe(final_df)
        else:
            st.success("✅ 매체 데이터 통합 완료 (어도비 미포함)")
            st.dataframe(media_df)
