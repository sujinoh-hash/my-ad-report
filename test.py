import streamlit as st
import pandas as pd

def build_perfect_key(cid):
    if pd.isna(cid) or str(cid).strip() == "" or "_adef-" in cid:
        return "Unknown"
    
    cid = str(cid).lower().strip()
    
    # 1. 매체명(Media) 판별
    media = "google"
    if "navershopping" in cid: return "Naver shopping"
    if "brandzone" in cid or "naverbsp" in cid or "ps_naver" in cid:
        media = "naverbsmo" if "mo-" in cid else "naverbspc"
    elif "kakaobsp" in cid:
        media = "kakaobsmo" if "mo-" in cid else "kakaobspc"
    elif "dsp_yt" in cid: media = "YouTube" # 유튜브 독립
    elif "dsp_naver" in cid: media = "naverda"
    elif "dsp_kakao" in cid:
        media = "kakaodaD" if "native" in cid else "kakaoda"
    elif "meta" in cid or "fbig" in cid:
        media = "metaC" if "catalog" in cid and ("advantage" in cid or "pixel" in cid) else "meta"
        if "prospecting-na-na" in cid: media = "metam3"
    elif "pmax" in cid:
        if any(x in cid for x in ["w_prospecting", "demo-women", "pmaxw"]): media = "pmaxW"
        elif "pmaxm" in cid: media = "pmaxM"
        else: media = "pmaxC"
    elif "kakao-kw" in cid or "kakaotalksa" in cid: media = "kakaotalksa"
    elif "naverpc" in cid: media = "naverpc"
    elif "navermo" in cid: media = "navermo"
    elif "criteo" in cid: media = "criteo"

    # 2. 캠페인키(Prefix) 판별
    camp = "alwayson"
    if "brand" in cid: camp = "brand"
    elif "product" in cid: camp = "product"
    elif "activity" in cid: camp = "activity"
    elif "yet-spring2026-run" in cid: camp = "26Run"
    elif "men-2026" in cid: camp = "men"
    elif "bottoms-spring2026-otm" in cid: camp = "pants" # 소문자 pants
    elif "winter-2026-alwayson" in cid:
        camp = "Run" if "run" in cid else "Holiday"
    elif "train-winter" in cid: camp = "Train"

    # 3. 단계(Funnel) 및 타겟팅(Target) 조립
    lvl = "middle-dm" # 기본값
    if "upper" in cid: lvl = "upper-dm"
    elif "lower" in cid: lvl = "lower-dm"
    
    # [특수 규칙] 특정 캠페인은 단계를 middle-dm으로 강제 고정
    if camp in ["product", "activity"] and lvl == "upper-dm": lvl = "middle-dm"
    if camp in ["pants", "Holiday"] and lvl == "lower-dm": lvl = "middle-dm"
    if camp == "26Run" and media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"
    if "brandzone" in cid or "naverbsp" in cid or "ps_naver" in cid or "kakaobsp" in cid: lvl = "BS-dm"

    target = "retargeting" if "retargeting" in cid else "prospecting"
    
    # [특수 규칙] 타겟팅 명칭 보정 (pro)
    if any(x in media for x in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        target = "pro"

    # 4. 최종 조립
    return f"{camp}-{lvl}-{target}-{media}"

# --- Streamlit 실행 부분 ---
st.title("🚀 6만 행 불일치 해결 검증기")
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"
ADOBE_GID = "1818457274"

if st.button("📊 다시 전수 검사하기"):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={ADOBE_GID}"
    df = pd.read_csv(url)
    df['AI_조립결과'] = df['CID'].apply(build_perfect_key)
    df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x['캠페인명']).strip() == str(x['AI_조립결과']).strip() else "❌ 불일치", axis=1)
    
    st.success(f"검사 완료! 일치: {len(df[df['일치여부']=='✅ 일치']):,}행 / 불일치: {len(df[df['일치여부']=='❌ 불일치']):,}행")
    st.dataframe(df[df['일치여부'] == "❌ 불일치"].head(100))
