import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="룰루레몬 자동화 도구 [v9]", layout="wide")

# --- [로직] v7 매핑 함수 (엄격한 기준 유지) ---
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

# --- [날짜 처리 로직] ---
def get_date_final(content, filename):
    for line in content:
        if "# 날짜:" in line:
            nums = re.findall(r'\d+', line)
            if len(nums) >= 3: return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
    file_nums = re.findall(r'\d{6}', filename)
    if file_nums:
        d = file_nums[0]
        return f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
    return datetime.now().strftime("%Y-%m-%d")

# --- UI 레이아웃 ---
tab1, tab2 = st.tabs(["🎯 1단계: 어도비 검수", "📊 2단계: 데이터 통합"])

with tab1:
    st.header("어도비 Raw 데이터 통합 검수")
    files = st.file_uploader("어도비 파일(들)을 올려주세요.", type="csv", accept_multiple_files=True)
    
    if files:
        all_dfs = []
        for f in files:
            content = f.getvalue().decode('utf-8-sig').splitlines()
            file_date = get_date_final(content, f.name)
            
            # 데이터 시작점 찾기
            idx = 0
            for i, line in enumerate(content):
                if "방문 횟수" in line:
                    idx = i
                    break
            
            df = pd.read_csv(io.StringIO("\n".join(content[idx:])))
            df.rename(columns={df.columns[0]: '코드'}, inplace=True)
            df = df.iloc[1:].reset_index(drop=True)
            df.insert(0, '날짜', file_date)
            all_dfs.append(df)
            
        full_adobe = pd.concat(all_dfs, ignore_index=True)
        full_adobe['AI_제안명'] = full_adobe['코드'].apply(build_perfect_key_v7)
        
        # [수정] 표에 노출할 열을 명확하게 지정
        cols_to_show = ['날짜', '코드', '방문 횟수', 'Cart Adds', 'Orders', 'Revenue', 'AI_제안명']
        # 실제 데이터에 있는 열만 필터링 (오타 방지)
        existing_cols = [c for c in cols_to_show if c in full_adobe.columns]
        
        st.subheader("🧐 검수용 실적 테이블")
        st.dataframe(full_adobe[existing_cols].head(1000))
        
        st.download_button("📥 검수 완료 파일 다운로드", full_adobe.to_csv(index=False).encode('utf-8-sig'), "adobe_v9_checked.csv")

# --- 2단계 로직 (생략 없이 이전과 동일) ---
