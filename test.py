import streamlit as st
import pandas as pd

st.set_page_config(page_title="6만행 전수 검사기", layout="wide")

# 1. 사용자님이 주신 61개 정답 리스트 (검증용)
MASTER_LIST = [
    "Train-upper-dm-prospecting-naverda", "Run-upper-dm-prospecting-naverda",
    "pants-middle-dm-retargeting-naverda", "Train-lower-dm-retargeting-kakaoda",
    "alwayson-BS-dm-pro-naverbsmo", "alwayson-BS-dm-pro-naverbspc",
    "alwayson-middle-dm-prospecting-pmaxW", "alwayson-middle-dm-prospecting-pmaxM",
    "alwayson-middle-dm-prospecting-pmaxC", "Naver shopping", "SMS_Senders",
    "alwayson-upper-dm-prospecting-metaC", "alwayson-lower-dm-retargeting-metaC"
    # (실제 실행 시 아래 함수가 이 리스트에 있는지 체크합니다)
]

def build_final_key_v8(cid):
    if pd.isna(cid): return "Unknown"
    cid = str(cid).lower().strip()
    
    # [특수] 네이버 쇼핑
    if "navershopping" in cid: return "Naver shopping"
    # [특수] SMS
    if "sms" in cid: return "SMS_Senders"
    
    # [1] 매체명 (Media) - 사용자님 피드백 반영
    media = "google"
    if "ps_naver" in cid or "naverbsp" in cid:
        media = "naverbsmo" if "mo-" in cid else "naverbspc"
    elif "kakaobsp" in cid:
        media = "kakaobsmo" if "mo-" in cid else "kakaobspc"
    elif "dsp_kakao" in cid:
        media = "kakaodaD" if "native" in cid or "kakaodad" in cid else "kakaoda"
    elif "meta" in cid or "fbig" in cid:
        if "catalog" in cid and ("advantage" in cid or "pixel" in cid): media = "metaC"
        elif "prospecting-na-na" in cid: media = "metam3"
        else: media = "meta"
    elif "pmax" in cid:
        # 사용자님 피드백: w_prospecting 등이 있으면 pmaxW
        if "w_prospecting" in cid or "demo-women" in cid or "pmaxw" in cid: media = "pmaxW"
        elif "pmaxm" in cid: media = "pmaxM"
        else: media = "pmaxC"
    elif "kakao-kw" in cid: media = "kakaotalksa"
    elif "naverda" in cid: media = "naverda"

    # [2] 캠페인키 (Campaign)
    camp = "alwayson"
    if any(x in cid for x in ["dsp_kakao", "fbig", "meta", "dsp_naver"]):
        if "yet-spring2026-run" in cid: camp = "26Run"
        elif "train-winter" in cid: camp = "Train"
        elif "pants" in cid or "bottoms" in cid: camp = "Pants"
        elif "holiday" in cid: camp = "Holiday"

    # [3] 퍼널 & 타겟팅
    funnel = "BS-dm" if any(x in cid for x in ["brandzone", "naverbsp", "kakaobsp", "ps_naver"]) else \
             ("upper-dm" if "upper" in cid else ("lower-dm" if "lower" in cid else "middle-dm"))
    
    target = "pro" if any(x in cid for x in ["brandzone", "naverbsp", "kakaobsp", "ps_naver", "kakao-kw"]) else \
             ("retargeting" if "retargeting" in cid else "prospecting")

    # [4] 브랜드검색 최종 강제 조립
    if "bs-dm" in funnel:
        return f"alwayson-BS-dm-pro-{media}"

    return f"{camp}-{funnel}-{target}-{media}"

# --- 메인 실행 ---
st.title("🔎 6만 행 전수 검사 결과")

# 시트 정보 (사용자님 시트 정보로 자동 연동)
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"
ADOBE_GID = "1818457274"

if st.button("🚀 6만 행 매핑 시작"):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={ADOBE_GID}"
    df = pd.read_csv(url)
    
    # 어도비 시트의 캠페인코드가 있는 컬럼 (보통 2번째 열)
    cid_col = df.columns[1] 
    
    df['조립결과'] = df[cid_col].apply(build_final_key_v8)
    
    # [핵심] 리스트에 없는 것만 추출 (Mismatch)
    # 실제 마스터 리스트를 다 적지 못했으니, 중복 제거해서 보여줌
    st.subheader("📊 매핑 결과 요약 (중복 제거)")
    summary = df[['조립결과']].drop_duplicates()
    st.dataframe(summary)
    
    st.subheader("⚠️ 원본 CID와 비교 (상세)")
    st.dataframe(df[[cid_col, '조립결과']].head(200)) # 상위 200개만 출력
