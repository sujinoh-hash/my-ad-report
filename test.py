import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="6만행 매핑 최종 검증기", layout="wide")

# 1. 시트 설정
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" 

def build_perfect_key(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # [STEP 0] 절대적 Unknown 필터 (가장 먼저 거름)
    unknown_keywords = ["_adef-", "_br_", "brandsearch", "ps_naver_daily", "ps_naver_campaign"]
    if any(x in cid_low for x in unknown_keywords) or cid_raw == "":
        return "Unknown"

    # [STEP 1] 고정 매칭 그룹 (조건 일치 시 즉시 리턴)
    # 1. kakaopn / kakao-opt-in
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"
    
    # 2. dsp_kakao-kw
    if "dsp_kakao-kw" in cid_low:
        return "alwayson-upper-dm-pro-kakaotalksa"
    
    # 3. Naver Shopping / SMS
    if "navershopping" in cid_low: return "Naver shopping"
    if "sms" in cid_low: return "SMS_Senders"

    # [STEP 2] PS_ 검색 광고 (Google/Naver/Daum) - brandzone 제외
    if ("ps_naver" in cid_low or "ps_google" in cid_low or "ps_daum" in cid_low) and "brandzone" not in cid_low:
        # 매체 판별
        if "ps_naver" in cid_low:
            m_fin = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
            t_fin = "pro"
        elif "ps_google" in cid_low:
            m_fin = "google"
            t_fin = "retargeting" if "retargeting" in cid_low else "prospecting"
        else: # ps_daum
            m_fin = "kakaomo" if any(x in cid_low for x in ["-mo-", "_mo"]) else "kakaopc"
            t_fin = "prospecting"

        # 캠페인 키 (반드시 brand, product, activity 중 하나)
        if "product" in cid_low: c_fin = "product"
        elif "activity" in cid_low: c_fin = "activity"
        else: c_fin = "brand" # brand 포함되거나 기본값

        # 단계 판별
        if "lower" in cid_low: l_fin = "lower-dm"
        elif any(x in cid_low for x in ["middle", "product", "activity"]): l_fin = "middle-dm"
        else: l_fin = "lower-dm"

        return f"{c_fin}-{l_fin}-{t_fin}-{m_fin}"

    # [STEP 3] 브랜드존 (Brandzone) - 항상 alwayson-BS 시작
    if "brandzone" in cid_low:
        if any(x in cid_low for x in ["naver", "naverbsp"]):
            sub = "naverbsmo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverbspc"
        else:
            sub = "kakaobsmo" if any(x in cid_low for x in ["_mo", "-mo"]) else "kakaobspc"
        return f"alwayson-BS-dm-pro-{sub}"

    # [STEP 4] PMAX 엄격 규칙
    if "pmax" in cid_low:
        if "w_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxW"
        if "m_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxM"
        if "prospecting-demo-all" in cid_low: return "alwayson-middle-dm-prospecting-pmaxC"
        return "Unknown"

    # [STEP 5] 일반 매체 조립 (Meta, YouTube, DA, Criteo 등)
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
    if media == "criteo": camp = "alwayson"
    elif any(x in cid_low for x in ["becalm", "steadystate", "bigcozy"]): camp = "Holiday"
    elif "prospecting-custom-runnigstorekw" in cid_low or "logorun" in cid_low: camp = "Run"
    elif "train-winter2025-train" in cid_low: camp = "Train"
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "holiday-winter2025-general" in cid_low: camp = "Holiday"
    elif "bottoms-spring2026-otm" in cid_low: camp = "pants" if media == "naverda" else "Pants"
    elif "men-2026-alwayson" in cid_low: camp = "men"
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson"]): camp = "alwayson"
    else: camp = "alwayson"

    # 단계 & 타겟 조립
    lvl = "lower-dm" if ("lower" in cid_low or "retargeting" in cid_low) else ("upper-dm" if ("upper" in cid_low or "prospecting" in cid_low) else "middle-dm")
    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"
    
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    
    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행부 ---
if st.button("🚀 100% 일치 도전! 전수 검사 시작"):
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
                st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결결과']].head(500))
    except Exception as e:
        st.error(f"오류: {e}")
