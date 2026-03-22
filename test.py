import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="6만행 매핑 마스터 최종형", layout="wide")

# 1. 시트 설정
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" 

def build_perfect_key(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # [STEP 0] 최우선 순위: kakao-opt-in / kakaopn (필터보다 먼저!)
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    # [STEP 1] 최우선 순위: Naver Shopping (ps_navershopping 포함)
    if "navershopping" in cid_low:
        return "Naver shopping"

    # [STEP 2] Unknown 필터링 (토큰 정밀 검증)
    unknown_keywords = ["_adef-", "_br_", "brandsearch", "ps_naver_daily", "ps_naver_campaign"]
    for kw in unknown_keywords:
        if kw in cid_low:
            # ps_naver_dailywear 보호 로직
            if kw == "ps_naver_daily" and "dailywear" in cid_low:
                continue
            return "Unknown"
    if cid_raw == "": return "Unknown"

    # [STEP 3] 엑셀 수식 기반 검색 광고 (ps_google, ps_daum, ps_naver)
    # 1. ps_google
    if "ps_google" in cid_low:
        if "retargeting-keyword-brand_alwayson-na-na_pcmo" in cid_low: return "brand-lower-dm-retargeting-google"
        if "prospecting-keyword-brand_alwayson-na-na_pcmo" in cid_low: return "brand-lower-dm-prospecting-google"
        if "prospecting-keyword-product_alwayson-na-na_pcmo" in cid_low: return "product-middle-dm-prospecting-google"
        if "prospecting-keyword-activity_alwayson-na-na_pcmo" in cid_low: return "activity-middle-dm-prospecting-google"
    
    # 2. ps_daum (brandzone 제외)
    if "ps_daum" in cid_low and "brandzone" not in cid_low:
        # ps_daum_brand 포함 시 분기
        if "brand" in cid_low:
            sub = "kakaomo" if any(x in cid_low for x in ["-mo-", "_mo"]) else "kakaopc"
            return f"brand-lower-dm-prospecting-{sub}"

    # 3. ps_naver (brand, product, activity 6종 및 waterbottle 등)
    if "ps_naver" in cid_low and "brandzone" not in cid_low:
        # 엑셀 하드코딩 수식들
        if "keyword-brand_alwayson-na-na_mo" in cid_low: return "brand-lower-dm-pro-navermo"
        if "keyword-brand_alwayson-na-na_pc" in cid_low: return "brand-lower-dm-pro-naverpc"
        if "keyword-product_alwayson-na-na_mo" in cid_low: return "product-middle-dm-pro-navermo"
        if "keyword-product_alwayson-na-na_pc" in cid_low: return "product-middle-dm-pro-naverpc"
        if "keyword-activity_alwayson-na-na_mo" in cid_low: return "activity-middle-dm-pro-navermo"
        if "keyword-activity_alwayson-na-na_pc" in cid_low: return "activity-middle-dm-pro-naverpc"
        
        # [해결] waterbottle, dailywear 등 자동 조립
        m_fin = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
        c_fin = "product" if any(x in cid_low for x in ["product", "dailywear", "waterbottle"]) else ("activity" if "activity" in cid_low else "brand")
        l_fin = "middle-dm" if c_fin in ["product", "activity"] else "lower-dm"
        return f"{c_fin}-{l_fin}-pro-{m_fin}"

    # [STEP 4] 고정 매칭 (Brandzone, PMAX, SMS 등)
    if "brandzone" in cid_low:
        sub = ("naverbsmo" if "naver" in cid_low else "kakaobsmo") if any(x in cid_low for x in ["_mo", "-mo"]) else ("naverbspc" if "naver" in cid_low else "kakaobspc")
        return f"alwayson-BS-dm-pro-{sub}"
    if "pmax" in cid_low:
        if "w_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxW"
        if "m_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxM"
        if "prospecting-demo-all" in cid_low: return "alwayson-middle-dm-prospecting-pmaxC"
        return "Unknown"
    if "sms" in cid_low: return "SMS_Senders"
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"

    # [STEP 5] 일반 매체 조립 (Meta, Criteo, DA 등)
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

    # [STEP 6] 캠페인 키 Prefix 결정 (Holiday 우선순위 상향)
    if media == "criteo": 
        camp = "alwayson"
    elif any(x in cid_low for x in ["holiday-winter2025-general", "becalm", "steadystate", "bigcozy"]): 
        camp = "Holiday"
    elif "prospecting-custom-runnigstorekw" in cid_low or "logorun" in cid_low:
        camp = "Run"
    elif "train-winter2025-train" in cid_low: camp = "Train"
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "bottoms-spring2026-otm" in cid_low:
        camp = "pants" if media == "naverda" else "Pants"
    elif "men-2026-alwayson" in cid_low: camp = "men"
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson"]):
        camp = "alwayson"
    else:
        camp = "alwayson"

    # [STEP 7] 단계 & 타겟 조립
    lvl = "lower-dm" if ("lower" in cid_low or "retargeting" in cid_low) else ("upper-dm" if ("upper" in cid_low or "prospecting" in cid_low) else "middle-dm")
    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    
    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행 UI ---
if st.button("🚀 모든 요청 사항 반영 최종 검사 시작"):
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
