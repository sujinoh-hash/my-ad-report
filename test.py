import streamlit as st
import pandas as pd

st.set_page_config(page_title="CID 매핑 검증기", layout="wide")

st.title("🧪 CID -> 캠페인명 조립 실험실 (최종 규칙 반영)")

def build_campaign_key_v5(cid):
    if pd.isna(cid): return "Unknown"
    cid = str(cid).lower().strip()
    
    # [1] 매체 및 특수 규칙 (브랜드검색 등 우선 처리)
    # 네이버 브랜드검색 예시: ps_naver-brandzone... -> alwayson-BS-dm-pro-naverbsmo
    if "brandzone" in cid or "naverbsp" in cid or "ps_naver" in cid:
        media = "naverbsmo" if "mo-" in cid else "naverbspc"
        return f"alwayson-BS-dm-pro-{media}"
    
    # [2] 캠페인 키워드 판별 (dsp_kakao, fbig, dsp_naver 이외에는 alwayson)
    camp = "alwayson"
    if "dsp_kakao" in cid or "fbig" in cid or "dsp_naver" in cid or "meta" in cid:
        if "yet-spring2026-run" in cid: camp = "26Run"
        elif "train-winter2025" in cid: camp = "Train"
        elif "bottoms-spring2026" in cid: camp = "Pants"
        elif "holiday-winter2025" in cid: camp = "Holiday"
        elif "men-2026" in cid: camp = "men"
    
    # [3] 단계/퍼널 (dm)
    level = "middle-dm" # 기본값
    if "upper" in cid: level = "upper-dm"
    elif "lower" in cid: level = "lower-dm"
    
    # [4] 타겟팅 (리스트 기반: prospecting / retargeting)
    target = "prospecting" 
    if "retargeting" in cid: target = "retargeting"
    
    # [5] 매체명 상세 번역
    media_final = ""
    if "dsp_kakao" in cid:
        media_final = "kakaodaD" if "native" in cid or "kakaodad" in cid else "kakaoda"
    elif "meta" in cid or "smp_fbig" in cid:
        if "catalog" in cid: media_final = "metaC"
        elif "prospecting-na-na" in cid: media_final = "metam3"
        else: media_final = "meta"
    elif "dsp_naver" in cid: media_final = "naverda"
    elif "kakao-kw" in cid: media_final = "kakaotalksa"
    
    return f"{camp}-{level}-{target}-{media_final}"

# UI 부분
input_text = st.text_area("검수할 CID를 입력하세요", value="ps_naver-brandzone_run_lower_dm_ko-kr_a_prospecting-brandzone-na_yet-spring2026-run_mo-homelink-run-260303-lululemon")

if st.button("조립 결과 확인"):
    cids = [c.strip() for c in input_text.split('\n') if c.strip()]
    res = [{"원본": c, "결과": build_campaign_key_v5(c)} for c in cids]
    st.table(pd.DataFrame(res))
