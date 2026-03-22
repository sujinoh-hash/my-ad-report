import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="6만행 매핑 최종 검증기", layout="wide")

# 1. 시트 설정
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" 

def has_token(text, token):
    return re.search(rf'(^|[_-]){re.escape(token)}([_-]|$)', text) is not None

def build_perfect_key(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # [0] 최우선 필터링 (Naver Shopping / SMS)
    if "navershopping" in cid_low: return "Naver shopping"
    if "sms" in cid_low: return "SMS_Senders"
    
    # [1] kakaooptin (kakaopn, kakao-opt-in, pu_, transactional)
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        # pu_ 또는 transactional 포함 시 transactional로 마감
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    # [2] 브랜드존 (naver-brandzone, daum-brandzone) -> 캠페인키 alwayson 고정
    if "naver-brandzone" in cid_low:
        sub = "naverbsmo" if any(x in cid_low for x in ["_mo-", "-mo-"]) else "naverbspc"
        return f"alwayson-BS-dm-pro-{sub}"
    if "daum-brandzone" in cid_low:
        sub = "kakaobsmo" if any(x in cid_low for x in ["_mo-", "-mo-"]) else "kakaobspc"
        return f"alwayson-BS-dm-pro-{sub}"

    # [3] PS_ 검색 광고 (Google / Naver / Daum) -> brand, product, activity로만 시작
    # ps_naver-brandzone은 제외 (위에서 처리됨)
    if "ps_naver" in cid_low or "ps_google" in cid_low or "ps_daum" in cid_low:
        # 매체 결정
        if "ps_naver" in cid_low:
            media_final = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
            target_final = "pro"
        elif "ps_google" in cid_low:
            media_final = "google"
            target_final = "retargeting" if "retargeting" in cid_low else "prospecting"
        else: # ps_daum
            media_final = "kakaomo" if "-mo-" in cid_low else "kakaopc"
            target_final = "prospecting"

        # 캠페인키 결정 (brand, product, activity 순서)
        if "brand" in cid_low: camp_final = "brand"
        elif "product" in cid_low: camp_final = "product"
        elif "activity" in cid_low: camp_final = "activity"
        else: camp_final = "brand" # 기본값

        # 단계 결정
        if "lower" in cid_low: lvl_final = "lower-dm"
        elif "middle" in cid_low or "product" in cid_low or "activity" in cid_low: lvl_final = "middle-dm"
        else: lvl_final = "lower-dm" # brand 기본

        return f"{camp_final}-{lvl_final}-{target_final}-{media_final}"

    # [4] PMAX 엄격 규칙
    if "pmax" in cid_low:
        if "w_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxW"
        if "m_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxM"
        if "prospecting-demo-all" in cid_low: return "alwayson-middle-dm-prospecting-pmaxC"
        return "Unknown"

    # [5] 일반 매체 (Meta, YouTube, DA, Criteo 등)
    media = "google"
    if "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low:
        media = "kakaodaD" if "_pcmo" in cid_low else "kakaoda"
        if "catalog" in cid_low: media = "kakaodaC"
    elif any(x in cid_low for x in ["meta", "smp_fbig", "smp_ig"]):
        media = "metaC" if any(x in cid_low for x in ["catalog", "alwayson-na-na"]) else "meta"
        if "prospecting-na-na" in cid_low: media = "metam3"
    elif "criteo" in cid_low: media = "criteo"
    elif "kakaotalksa" in cid_low: media = "kakaotalksa"

    # 캠페인 키 (Prefix)
    # Criteo는 무조건 alwayson
    if media == "criteo":
        camp = "alwayson"
    elif any(x in cid_low for x in ["becalm", "steadystate", "bigcozy"]): camp = "Holiday"
    elif "train-winter2025-train" in cid_low: camp = "Train"
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "bottoms-spring2026-otm" in cid_low: camp = "pants" if media == "naverda" else "Pants"
    elif "men-2026-alwayson" in cid_low: camp = "men"
    elif "holiday-winter2025-general" in cid_low: camp = "Holiday"
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson"]): camp = "alwayson"
    elif "logorun" in cid_low: camp = "Run"
    else: camp = "alwayson"

    # 단계 (Funnel)
    if "lower" in cid_low or "retargeting" in cid_low: lvl = "lower-dm"
    elif "upper" in cid_low or "prospecting" in cid_low: lvl = "upper-dm"
    else: lvl = "middle-dm"

    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"

    # 타겟 (Target)
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    if media in ["navermo", "naverpc", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]: target = "pro"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행부 ---
if st.button("🚀 전체 규칙 통합 최종 검사 시작"):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            if camp_col:
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip().lower() == str(x['AI_조립결과']).strip().lower() else "❌ 불일치", axis=1)
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                st.success(f"검사 완료! 일치: {len(df)-len(mismatches):,} / 불일치: {len(mismatches):,}")
                st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
    except Exception as e:
        st.error(f"오류: {e}")
