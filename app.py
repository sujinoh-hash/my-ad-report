import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="룰루레몬 자동화 도구", layout="wide")

# --- [로직] v5 매핑 함수 (동일) ---
def build_perfect_key_v5(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()
    
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"
    if "payco" in cid_low: return "alwayson-lower-dm-prospecting-payco"
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"
    if "navershopping" in cid_low: return "Naver shopping"
    if "brandzone" in cid_low:
        if "brandzone-na" not in cid_low: return "Unknown"
        sub = ("naverbsmo" if "naver" in cid_low else "kakaobsmo") if any(x in cid_low for x in ["_mo", "-mo"]) else ("naverbspc" if "naver" in cid_low else "kakaobspc")
        return f"alwayson-BS-dm-pro-{sub}"
    if "criteo" in cid_low:
        if "dsp_criteo" in cid_low and ("w_prospecting-demo-women" in cid_low or "m_prospecting-demo-men" in cid_low):
            return "alwayson-upper-dm-prospecting-criteo"
        if "lower" not in cid_low: return "Unknown"
        return "alwayson-lower-dm-retargeting-criteo"
    if "dsp_naver" in cid_low and "prospecting-demo-all" in cid_low:
        camp_das = "alwayson"
        if any(x in cid_low for x in ["holiday", "becalm", "steadystate", "bigcozy"]): camp_das = "Holiday"
        lvl_das = "upper-dm" if "upper" in cid_low else "middle-dm"
        return f"{camp_das}-{lvl_das}-prospecting-naverdas"
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
    # '2026년 3월 16일' -> '2026-03-16' 변환
    nums = re.findall(r'\d+', date_str)
    if len(nums) >= 3:
        return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
    return date_str

# --- UI 레이아웃 ---
st.title("🏃 룰루레몬 하이브리드 자동화 도구")

tab1, tab2 = st.tabs(["🎯 1단계: 어도비 통합 검수", "📊 2단계: 데이터 통합"])

with tab1:
    st.header("어도비 Raw 데이터 일괄 업로드")
    uploaded_files = st.file_uploader("여러 날짜의 어도비 CSV 파일들을 한꺼번에 올리세요.", type="csv", accept_multiple_files=True)
    
    if uploaded_files:
        all_dfs = []
        for uploaded_file in uploaded_files:
            content = uploaded_file.getvalue().decode('utf-8-sig').splitlines()
            
            # 날짜 찾기 및 변환
            raw_date = "날짜미상"
            data_start_idx = 0
            for i, line in enumerate(content):
                if "# 날짜:" in line:
                    raw_date = format_adobe_date(line.split(":")[-1].strip())
                if "방문 횟수" in line and "," in line:
                    data_start_idx = i
                    break
            
            # 데이터 로딩
            temp_df = pd.read_csv(io.StringIO("\n".join(content[data_start_idx:])))
            temp_df.rename(columns={temp_df.columns[0]: '코드'}, inplace=True)
            temp_df = temp_df.iloc[1:].reset_index(drop=True)
            
            # 날짜 삽입
            temp_df.insert(0, '날짜', raw_date)
            all_dfs.append(temp_df)
        
        full_df = pd.concat(all_dfs, ignore_index=True)
        full_df['AI_제안명'] = full_df['코드'].apply(build_perfect_key_v5)
        
        st.subheader(f"🧐 통합 검수 리스트 (총 {len(full_df)}행)")
        
        # 필터링 및 노출
        only_unknown = st.checkbox("Unknown만 모아보기")
        display_df = full_df[full_df['AI_제안명'] == "Unknown"] if only_unknown else full_df
        
        cols = ['날짜', '코드', '방문 횟수', 'Cart Adds', 'Orders', 'Revenue', 'AI_제안명']
        existing = [c for c in cols if c in display_df.columns]
        st.dataframe(display_df[existing].head(1000))
        
        # 다운로드
        st.download_button(
            label="📥 전체 매핑 결과 다운로드 (CSV)",
            data=full_df.to_csv(index=False).encode('utf-8-sig'),
            file_name="adobe_merged_report.csv",
            mime="text/csv"
        )
