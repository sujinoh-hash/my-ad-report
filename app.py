import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="룰루레몬 자동화 도구", layout="wide")

# --- [로직] v7 매핑 함수 (기존의 엄격한 기준 유지) ---
def build_perfect_key_v7(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    if "navershopping" in cid_low: return "Naver shopping"
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        return "alwayson-lower-dm-kakaooptin-kakaopn"

    if "brandzone" in cid_low:
        if "brandzone-na" not in cid_low: return "Unknown"
        sub = "naverbsmo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverbspc"
        if "kakao" in cid_low: sub = sub.replace("naver", "kakao")
        return f"alwayson-BS-dm-pro-{sub}"

    if cid_low.startswith("ps_"):
        if "keyword-" not in cid_low: return "Unknown"
        m = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
        if "google" in cid_low: m = "google"
        elif "daum" in cid_low: m = "kakaomo" if "mo" in m else "kakaopc"
        f = "lower-dm" if "lower" in cid_low else "middle-dm"
        t = "retargeting" if "retargeting" in cid_low else "pro"
        c = "brand"
        if any(x in cid_low for x in ["product", "dailywear"]): c = "product"
        elif "activity" in cid_low: c = "activity"
        return f"{c}-{f}-{t}-{m}"

    if "criteo" in cid_low:
        if "prospecting-demo" in cid_low: return "alwayson-upper-dm-prospecting-criteo"
        if "lower" in cid_low: return "alwayson-lower-dm-retargeting-criteo"
        return "Unknown"

    if "pmax" in cid_low:
        suffix = "W" if "w_pros" in cid_low else ("M" if "m_pros" in cid_low else "C")
        return f"alwayson-middle-dm-prospecting-pmax{suffix}"
    
    media = "google"
    if "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low: media = "kakaoda"
    elif "meta" in cid_low or "smp_fbig" in cid_low: media = "meta"
    camp = "Springstory" if "spring2026" in cid_low else "alwayson"
    return f"{camp}-upper-dm-prospecting-{media}"

# --- [날짜 처리 핵심 수정] ---
def get_date_final(content, filename):
    # 1. 파일 내용에서 찾기 (# 날짜:2026년 3월 23일)
    for line in content:
        if "# 날짜:" in line:
            nums = re.findall(r'\d+', line)
            if len(nums) >= 3:
                return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
    
    # 2. 파일 이름에서 6자리 숫자 찾기 (예: 260323)
    file_nums = re.findall(r'\d{6}', filename)
    if file_nums:
        d = file_nums[0] # '260323'
        return f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
    
    # 3. 위 방법 모두 실패 시 오늘 날짜
    return datetime.now().strftime("%Y-%m-%d")

# --- UI ---
st.title("🏃 룰루레몬 하이브리드 자동화 도구 [v8]")
tab1, tab2 = st.tabs(["🎯 1단계: 어도비 검수", "📊 2단계: 데이터 통합"])

with tab1:
    st.header("어도비 Raw 데이터 일괄 업로드")
    uploaded_files = st.file_uploader("어도비 CSV들을 올려주세요.", type="csv", accept_multiple_files=True)
    if uploaded_files:
        all_dfs = []
        for f in uploaded_files:
            # 파일 읽기
            raw_bytes = f.getvalue()
            content = raw_bytes.decode('utf-8-sig').splitlines()
            
            # [수정된 날짜 로직 적용]
            file_date = get_date_final(content, f.name)
            
            # 데이터 시작점 찾기
            data_start_idx = 0
            for i, line in enumerate(content):
                if "방문 횟수" in line and "," in line:
                    data_start_idx = i
                    break
            
            df = pd.read_csv(io.StringIO("\n".join(content[data_start_idx:])))
            df.rename(columns={df.columns[0]: '코드'}, inplace=True)
            df = df.iloc[1:].reset_index(drop=True)
            df.insert(0, '날짜', file_date) # 인식된 날짜 삽입
            all_dfs.append(df)
        
        full_adobe = pd.concat(all_dfs, ignore_index=True)
        full_adobe['AI_제안명'] = full_adobe['코드'].apply(build_perfect_key_v7)
        st.dataframe(full_adobe[['날짜', '코드', 'AI_제안명']].head(500))
        st.download_button("📥 검수용 다운로드", full_adobe.to_csv(index=False).encode('utf-8-sig'), "adobe_v8_result.csv")

# 2단계 코드는 고정값/음수보정 로직을 포함하여 기존과 동일하게 유지
