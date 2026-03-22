import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="CID 매핑 검증기", layout="wide")

st.title("🧪 CID -> 캠페인명 조립 실험실")
st.write("사용자님이 주신 규칙: **[캠페인키]-[퍼널/단계]-dm-[타겟팅]-[매체명]**")

def build_campaign_key_final(cid):
    if pd.isna(cid): return "Unknown"
    cid = str(cid).lower().strip()
    
    # 1. [캠페인키] - 브랜드존(ps_naver) 등 특수 케이스 먼저 처리
    camp = "alwayson" 
    if "yet-spring2026-run" in cid: camp = "26Run"
    elif "train-winter2025" in cid: camp = "Train"
    elif "bottoms-spring" in cid: camp = "Pants"
    elif "ps_naver" in cid: camp = "alwayson" # 브랜드존은 예시대로 alwayson

    # 2. [퍼널/단계] + [dm]
    funnel = "middle"
    if "brandzone" in cid or "naverbsp" in cid or "kakaobsp" in cid: funnel = "BS"
    elif "upper" in cid: funnel = "upper"
    elif "lower" in cid: funnel = "lower"
    
    # 3. [타겟팅]
    target = "pro"
    if "retargeting" in cid: target = "retargeting"
    elif "prospecting" in cid or "pro-" in cid: target = "pro"

    # 4. [매체명] - dsp_kakao, smp_fbig 등 암호 해독
    media = ""
    if "brandzone" in cid or "naverbsp" in cid:
        media = "naverbsmo" if "mo-" in cid else "naverbspc"
    elif "dsp_kakao" in cid:
        if "native" in cid: media = "kakaodaD"
        else: media = "kakaoda"
    elif "smp_fbig" in cid or "meta" in cid:
        if "catalog" in cid: media = "metaC"
        else: media = "meta"
    elif "kakao-kw" in cid: media = "kakaotalksa"
    elif "naverda" in cid: media = "naverda"
    
    # 5. 최종 조립: [캠페인키]-[퍼널]-dm-[타겟팅]-[매체명]
    return f"{camp}-{funnel}-dm-{target}-{media}"

# --- 화면 UI ---
input_text = st.text_area("검수할 어도비 CID를 입력하세요 (한 줄에 하나씩)", 
                         value="ps_naver-brandzone_run_lower_dm_ko-kr_a_prospecting-brandzone-na_yet-spring2026-run_mo-homelink-run-260303-lululemon",
                         height=200)

if st.button("🚀 조립 결과 확인"):
    cids = [c.strip() for c in input_text.split('\n') if c.strip()]
    results = []
    for c in cids:
        results.append({
            "원본 CID (Adobe)": c,
            "조립된 캠페인명 (Dashboard)": build_campaign_key_final(c)
        })
    st.table(pd.DataFrame(results))
