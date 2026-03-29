import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="룰루레몬 자동화 도구", layout="wide")

# --- [로직] v5+ 매핑 함수 (어도비 용) ---
def build_perfect_key_v5(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # [수정] 네이버 쇼핑 통합 규칙
    if "navershopping" in cid_low: return "Naver shopping"
    
    # 1. 고정 매칭
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"
    if "payco" in cid_low: return "alwayson-lower-dm-prospecting-payco"
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    # 2. 브랜드검색
    if "brandzone" in cid_low:
        if "brandzone-na" not in cid_low: return "Unknown"
        sub = ("naverbsmo" if "naver" in cid_low else "kakaobsmo") if any(x in cid_low for x in ["_mo", "-mo"]) else ("naverbspc" if "naver" in cid_low else "kakaobspc")
        return f"alwayson-BS-dm-pro-{sub}"
        
    # 3. 크리테오 (Prospecting 예외 적용)
    if "criteo" in cid_low:
        if "dsp_criteo" in cid_low and ("w_prospecting-demo-women" in cid_low or "m_prospecting-demo-men" in cid_low):
            return "alwayson-upper-dm-prospecting-criteo"
        if "lower" not in cid_low: return "Unknown"
        return "alwayson-lower-dm-retargeting-criteo"

    # 4. 검색광고
    if any(x in cid_low for x in ["ps_naver", "ps_google", "ps_daum"]):
        if not any(x in cid_low for x in ["prospecting-keyword", "retargeting-keyword"]): return "Unknown"
        if "keyword-generic" in cid_low:
            sub_gen = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
            return f"generic-middle-dm-pro-{sub_gen}"
        m_fin = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
        if "ps_google" in cid_low: m_fin = "google"
        elif "ps_daum" in cid_low: m_fin = "kakaomo" if any(x in cid_low for x in ["-mo-", "_mo"]) else "kakaopc"
        t_fin = "pro" if "ps_naver" in cid_low else ("retargeting" if "retargeting" in cid_low else "prospecting")
        c_fin = "product" if any(x in cid_low for x in ["product", "dailywear", "waterbottle"]) else ("activity" if "activity" in cid_low else "brand")
        l_fin = "middle-dm" if c_fin in ["product", "activity"] else "lower-dm"
        return f"{c_fin}-{l_fin}-{t_fin}-{m_fin}"

    # 5. 기타 일반 캠페인
    media = "google"
    if "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low: media = "kakaoda"
    elif any(x in cid_low for x in ["meta", "smp_fbig", "smp_ig"]): media = "meta"
    if any(x in cid_low for x in ["sn-spring2026-casualigc", "sn-spring2026-casualdbe"]): camp = "Springstory"
    elif any(x in cid_low for x in ["holiday", "becalm", "steadystate", "bigcozy"]): camp = "Holiday"
    else: camp = "alwayson"
    lvl = "lower-dm" if ("lower" in cid_low or "retargeting" in cid_low) else "middle-dm"
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    return f"{camp}-{lvl}-{target}-{media}"

# --- 날짜 변환 함수 ---
def format_adobe_date(date_str):
    nums = re.findall(r'\d+', date_str)
    if len(nums) >= 3:
        return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
    return date_str

# --- [UI] ---
st.title("🏃 룰루레몬 하이브리드 자동화 도구")
tab1, tab2 = st.tabs(["🎯 1단계: 어도비 검수", "📊 2단계: 데이터 통합"])

# --- 1단계 로직 ---
with tab1:
    st.header("어도비 Raw 데이터 일괄 업로드 (7개 이상 가능)")
    uploaded_files = st.file_uploader("어도비 CSV 파일들을 드래그하세요.", type="csv", accept_multiple_files=True)
    
    if uploaded_files:
        all_dfs = []
        for f in uploaded_files:
            content = f.getvalue().decode('utf-8-sig').splitlines()
            file_date, data_start_idx = "날짜미상", 0
            for i, line in enumerate(content):
                if "# 날짜:" in line: file_date = format_adobe_date(line.split(":")[-1].strip())
                if "방문 횟수" in line and "," in line:
                    data_start_idx = i
                    break
            temp_df = pd.read_csv(io.StringIO("\n".join(content[data_start_idx:])))
            temp_df.rename(columns={temp_df.columns[0]: '코드'}, inplace=True)
            temp_df = temp_df.iloc[1:].reset_index(drop=True)
            temp_df.insert(0, '날짜', file_date)
            all_dfs.append(temp_df)
        
        full_adobe = pd.concat(all_dfs, ignore_index=True)
        full_adobe['AI_제안명'] = full_adobe['코드'].apply(build_perfect_key_v5)
        
        st.subheader("🧐 통합 검수 (날짜/카트/주문 포함)")
        only_unknown = st.checkbox("Unknown만 보기")
        display_df = full_adobe[full_adobe['AI_제안명'] == "Unknown"] if only_unknown else full_adobe
        cols = ['날짜', '코드', '방문 횟수', 'Cart Adds', 'Orders', 'Revenue', 'AI_제안명']
        st.dataframe(display_df[[c for c in cols if c in display_df.columns]].head(500))
        st.download_button("📥 검수 완료 파일 다운로드", full_adobe.to_csv(index=False).encode('utf-8-sig'), "adobe_checked.csv")

# --- 2단계 로직 ---
with tab2:
    st.header("📊 데이터 최종 통합 리포트")
    c1, c2 = st.columns(2)
    with c1: adobe_file = st.file_uploader("1. 검수한 어도비 파일 업로드", type="csv")
    with c2: media_files = st.file_uploader("2. 매체 Raw 파일 업로드 (여러 개 가능)", type=["csv", "xlsx"], accept_multiple_files=True)
    
    if adobe_file and media_files:
        df_a = pd.read_csv(adobe_file)
        all_media_list = []
        
        for mf in media_files:
            # 매체별 로딩 및 표준화
            df_m = pd.read_excel(mf) if mf.name.endswith('xlsx') else pd.read_csv(mf)
            
            # [수정] 열 이름 표준화
            rename_map = {'일':'일', 'Day':'일', '일자':'일', '일별':'일', '시작일':'일', '날짜':'일',
                          '캠페인 이름':'캠페인명', 'Campaign':'캠페인명', '메시지명':'캠페인명', '광고상품':'캠페인명', 'AD Type':'캠페인명', '캠페인':'캠페인명',
                          '노출수':'노출', '노출':'노출', 'Displays':'노출',
                          '클릭수':'클릭', '클릭(전체)':'클릭', 'Clicks':'클릭',
                          '비용':'광고비', '지출 금액 (KRW)':'광고비', 'Cost':'광고비', '최종광고비':'광고비', '집행금액':'광고비', '총비용(VAT포함)':'광고비', '결제 금액':'광고비',
                          '친구 추가수(7일)':'채널친구수', '전환수':'채널친구수', '집행 전환수':'채널친구수', '친구 추가 수 (7일) ':'채널친구수'}
            df_m.rename(columns=rename_map, inplace=True)
            
            # [고정값 처리 1] 카카오 메시지 / CPK / 쇼핑파트너
            if "메시지보고서" in mf.name or "msg" in str(df_m.columns).lower():
                df_m['캠페인명'] = "alwayson-lower-dm-kakaooptin-kakaopn"
            if "cpk" in mf.name.lower():
                df_m['캠페인명'] = "Kakao Offerwall"
            if "쇼핑파트너" in mf.name or "결제 금액" in df_m.columns:
                df_m['캠페인명'] = "쇼핑파트너센터"
                df_m['광고비'] = df_m['광고비'].apply(lambda x: abs(float(str(x).replace(',',''))) if pd.notna(x) else 0)
                df_m['노출'], df_m['클릭'] = 0, 0
                
            # [고정값 처리 2] kakaopn 노출 = 열람수
            if '열람수' in df_m.columns:
                df_m.loc[df_m['캠페인명'].str.contains('kakaopn', na=False), '노출'] = df_m['열람수']
            
            # [고정값 처리 3] 네이버 쇼핑 통합
            df_m['캠페인명'] = df_m['캠페인명'].replace(['navershopping_w', 'navershopping_m'], 'Naver shopping')
            
            all_media_list.append(df_m[['일', '캠페인명', '노출', '클릭', '광고비', '채널친구수'] if '채널친구수' in df_m.columns else ['일', '캠페인명', '노출', '클릭', '광고비']])

        df_m_total = pd.concat(all_media_list).groupby(['일', '캠페인명']).sum().reset_index()
        
        if st.button("🚀 매체 + 어도비 최종 통합"):
            df_a_sum = df_a.groupby(['날짜', 'AI_제안명']).agg({'방문 횟수':'sum', 'Cart Adds':'sum', 'Orders':'sum', 'Revenue':'sum'}).reset_index()
            final = pd.merge(df_m_total, df_a_sum, left_on=['일', '캠페인명'], right_on=['날짜', 'AI_제안명'], how='outer')
            st.dataframe(final.head(100))
            st.download_button("📥 통합 리포트 다운로드", final.to_csv(index=False).encode('utf-8-sig'), "lululemon_total_report.csv")
