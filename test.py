import streamlit as st
import pandas as pd

st.set_page_config(page_title="최종 CID 매핑 검증", layout="wide")
st.title("🧪 CID -> 캠페인명 최종 매핑 실험실")

def build_final_key(cid):
    if pd.isna(cid): return "Unknown"
    cid = str(cid).lower().strip()
    
    # 1. [브랜드검색/브랜드존] 우선 처리 (alwayson-BS-dm-pro-...)
    if any(x in cid for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        media = ""
        if "ps_naver" in cid or "naverbsp" in cid: media = "naverbsmo" if "mo-" in cid else "naverbspc"
        elif "kakaobsp" in cid: media = "kakaobsmo" if "mo-" in cid else "kakaobspc"
        return f"alwayson-BS-dm-pro-{media}"

    # 2. [매체명] 추출 (치환 규칙)
    media_final = "google" # ps_google 등 매체명 누락 시 기본값
    if "dsp_naver" in cid or "naverda" in cid: media_final = "naverda"
    elif "dsp_kakao" in cid:
        media_final = "kakaodaD" if "native" in cid or "kakaodad" in cid else "kakaoda"
    elif "meta" in cid or "smp_fbig" in cid:
        if "catalog" in cid and ("advantage" in cid or "pixel" in cid): media_final = "metaC"
        elif "prospecting-na-na" in cid: media_final = "metam3"
        else: media_final = "meta"
    elif "kakao-kw" in cid or "kakaotalksa" in cid: media_final = "kakaotalksa"
    elif "pmax" in cid:
        if "pmaxw" in cid: media_final = "pmaxW"
        elif "pmaxm" in cid: media_final = "pmaxM"
        else: media_final = "pmaxC"
    elif "naverpc" in cid: media_final = "naverpc"
    elif "navermo" in cid: media_final = "navermo"
    elif "youtube" in cid: media_final = "YouTube"
    elif "criteo" in cid: media_final = "criteo"
    elif "transactional" in cid: media_final = "kakaooptin-transactional"
    elif "kakaopn" in cid: media_final = "kakaooptin-kakaopn"

    # 3. [캠페인키] (dsp_kakao, meta, dsp_naver 이외엔 alwayson)
    camp = "alwayson"
    target_media = ["dsp_kakao", "meta", "smp_fbig", "dsp_naver"]
    if any(m in cid for m in target_media):
        if "yet-spring2026-run" in cid: camp = "26Run"
        elif "run-upper" in cid: camp = "Run"
        elif "train-winter" in cid: camp = "Train"
        elif "bottoms-spring" in cid or "pants" in cid: camp = "Pants"
        elif "holiday" in cid: camp = "Holiday"
        elif "men-upper" in cid: camp = "men"
    
    # 4. [퍼널/단계]
    funnel = "middle-dm"
    if "upper" in cid: funnel = "upper-dm"
    elif "lower" in cid: funnel = "lower-dm"
    
    # 5. [타겟팅]
    target = "prospecting"
    if "retargeting" in cid: target = "retargeting"
    elif "pro-" in cid: target = "pro" # 네이버/카카오 검색광고용

    # 최종 조합
    return f"{camp}-{funnel}-{target}-{media_final}"

# UI 구성
input_data = st.text_area("검수할 CID를 입력하세요", height=200)

if st.button("결과 확인"):
    cids = [c.strip() for c in input_data.split('\n') if c.strip()]
    res = [{"원본 CID": c, "매핑 결과": build_final_key(c)} for c in cids]
    st.table(pd.DataFrame(res))
