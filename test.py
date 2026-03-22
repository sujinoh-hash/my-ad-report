import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="6만행 전수 검사 최종", layout="wide")

# 1. 시트 설정 (사용자님의 시트 ID와 맵핑 탭 GID)
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" 

def has_token(text, token):
    return re.search(rf'(^|[_-]){re.escape(token)}([_-]|$)', text) is not None

def build_perfect_key(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # [0] 필터링 및 특수 매체 (엑셀 수식 반영)
    if cid_raw == "" or "_adef-" in cid_low: return "Unknown"
    if "navershopping" in cid_low: return "Naver shopping"
    if "sms" in cid_low: return "SMS_Senders"
    if "welcomemessage" in cid_low or "kakaopn" in cid_low: 
        suffix = "transactional" if "transactional" in cid_low else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    # [1] 매체(Media) 판별 (주신 수식 및 조건 반영)
    media = "google"
    if "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low:
        media = "kakaodaD" if "_pcmo" in cid_low else "kakaoda"
        if "catalog" in cid_low or "biz" in cid_low: media = "kakaodaC" if "catalog" in cid_low else media
    elif any(x in cid_low for x in ["meta", "smp_fbig", "smp_ig"]):
        if any(x in cid_low for x in ["alwayson-na-na", "catalog"]): media = "metaC"
        elif "prospecting-na-na" in cid_low: media = "metam3"
        else: media = "meta"
    elif "pmax" in cid_low:
        for p in ["pmaxa", "pmaxw", "pmaxm", "pmaxc"]:
            if p in cid_low: media = p.replace("pmax", "pmax").replace("a","A").replace("w","W").replace("m","M").replace("c","C"); break
    elif any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver"]):
        media = "naverbsmo" if "_mo" in cid_low else "naverbspc"
    elif any(x in cid_low for x in ["kakaobsp", "ps_daum_brand"]):
        media = "kakaobsmo" if "_mo" in cid_low else "kakaobspc"
    elif "kakaochannelkeyword" in cid_low or "kakaotalksa" in cid_low: media = "kakaotalksa"
    elif "criteo" in cid_low: media = "criteo"
    elif "demandgen" in cid_low: media = "demandgen"

    # [2] 캠페인 키(Prefix) 판별 (주신 상세 조건 우선순위)
    camp = "alwayson"
    if any(x in cid_low for x in ["becalm", "steadystate", "bigcozy"]): camp = "Holiday"
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "train-winter2025-train" in cid_low or "train_mo" in cid_low: camp = "Train"
    elif any(x in cid_low for x in ["bottoms-spring2026-otm", "otm_mo", "otm_pcmo", "pants"]):
        camp = "pants" if media == "naverda" else "Pants"
    elif any(x in cid_low for x in ["holiday-winter2025-general", "general_mo", "general_pcmo"]): camp = "Holiday"
    elif "runnigstorekw" in cid_low or "logorun" in cid_low: camp = "Run"
    elif "men-2026-alwayson" in cid_low: camp = "men"
    elif "otw" in cid_low and media == "naverda": camp = "otw"
    elif media in ["google", "YouTube"]:
        if "product" in cid_low: camp = "product"
        elif "activity" in cid_low: camp = "activity"
        elif "brand" in cid_low: camp = "brand"

    # [3] 단계(Funnel) 및 타겟(Target)
    lvl = "middle-dm"
    if "upper" in cid_low or "prospecting" in cid_low: lvl = "upper-dm"
    elif "lower" in cid_low or "retargeting" in cid_low: lvl = "lower-dm"
    
    # 예외: naverda lower -> middle
    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"
    # 예외: 브랜드 검색 BS-dm
    if any(x in cid_low for x in ["brandzone", "naverbsp", "kakaobsp"]): lvl = "BS-dm"

    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    if media in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]:
        target = "pro"

    # [4] 브랜드 검색형 최종 보정 (수식 반영)
    if "ps_naver" in cid_low and "brand" in cid_low: return f"brand-lower-dm-pro-{media}"
    if "ps_google" in cid_low and "brand" in cid_low: return f"brand-lower-dm-{target}-google"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행부 ---
if st.button("🚀 구글 시트 데이터 불러와서 전수 검사"):
    try:
        # GID를 포함하여 맵핑 시트를 정확히 호출
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(URL)
        
        df.columns = [c.strip() for c in df.columns]
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            if camp_col:
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip() == str(x['AI_조립결과']).strip() else "❌ 불일치", axis=1)
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                st.success(f"검사 완료! 일치: {len(df)-len(mismatches):,}건 / 불일치: {len(mismatches):,}건")
                st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
            else:
                st.info("비교할 '캠페인명' 열이 없어 조립 결과만 표시합니다.")
                st.dataframe(df[[cid_col, 'AI_조립결과']].head(500))
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류 발생: {e}")
