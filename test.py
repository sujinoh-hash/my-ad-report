import streamlit as st
import pandas as pd

st.set_page_config(page_title="CID 매핑 규칙 검증기", layout="wide")

st.title("🧪 CID -> 캠페인명 조립 실험실 (test.py)")
st.write("어도비 로데이터(CID)를 입력하여 광고 시트의 이름과 일치하는지 확인하세요.")

def build_campaign_key_v3(cid):
    if pd.isna(cid): return "Unknown"
    cid = str(cid).lower().strip()
    
    # 1. 캠페인 키워드 (Campaign)
    camp = "alwayson"
    if "yet-spring2026-run" in cid: camp = "26Run"
    elif "bottoms-spring2026-otm" in cid: camp = "Pants"
    elif "train-winter2025" in cid: camp = "Train"
    elif "holiday-winter2025" in cid: camp = "Holiday"
    elif "men-2026-alwayson" in cid: camp = "alwayson"
    elif "spring-2026-alwayson" in cid: camp = "alwayson"
    
    # 2. 레벨 (Level)
    level = ""
    if "upper" in cid: level = "upper-dm"
    elif "middle" in cid: level = "middle-dm"
    elif "lower" in cid: level = "lower-dm"
    
    # 3. 타겟팅 (Targeting)
    target = ""
    if "prospecting" in cid: target = "prospecting"
    elif "retargeting" in cid: target = "retargeting"

    # 4. 매체 상세 규칙 (사용자님 피드백 반영)
    media = ""
    
    # [카카오] native가 있으면 kakaodaD, biz가 있으면 kakaoda
    if "dsp_kakao" in cid:
        if "native" in cid: media = "kakaodaD"
        else: media = "kakaoda" # biz 포함 혹은 기본

    # [메타] catalog와 특정 타겟팅 조건이 맞아야 metaC
    elif "smp_fbig" in cid or "meta" in cid:
        if "catalog" in cid:
            # advantage나 pixel-order 같은 조건이 붙을 때 C
            if "advantage" in cid or "pixel" in cid: media = "metaC"
            else: media = "meta"
        elif "prospecting-na-na" in cid:
            media = "metam3"
        else: media = "meta"
            
    # [네이버]
    elif "dsp_naver" in cid or "naverda" in cid:
        media = "naverda"

    # 5. 최종 조립
    parts = [camp, level, target, media]
    return "-".join([p for p in parts if p])

# 화면 구성
input_text = st.text_area("검수할 어도비 CID 리스트 (한 줄에 하나씩)", height=200)

if st.button("🔎 변환 결과 확인"):
    cids = [c.strip() for c in input_text.split('\n') if c.strip()]
    res = []
    for c in cids:
        res.append({"원본 CID": c, "조립된 캠페인명": build_campaign_key_v3(c)})
    st.table(pd.DataFrame(res))
