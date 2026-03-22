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

    # [STEP 0] 최우선 순위: kakao-opt-in / kakaopn (필터보다 무조건 먼저)
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    # [STEP 1] Naver Shopping (ps_navershopping 포함)
    if "navershopping" in cid_low:
        return "Naver shopping"

    # [STEP 2] Unknown 필터링 (dailywear는 살리고, 나머지는 차단)
    unknown_keywords = ["_adef-", "_br_", "brandsearch", "ps_naver_daily", "ps_naver_campaign"]
    for kw in unknown_keywords:
        if kw in cid_low:
            # ps_naver_dailywear는 Unknown 처리하지 않고 통과 (핵심 수정)
            if kw == "ps_naver_daily" and "dailywear" in cid_low:
                continue
            return "Unknown"
    if cid_raw == "": return "Unknown"

    # [STEP 3] ps_naver / ps_google / ps_daum 전용 조립 로직
    # waterbottle, dailywear가 여기서 조립되도록 로직을 분리했습니다.
    if ("ps_naver" in cid_low or "ps_google" in cid_low or "ps_daum" in cid_low) and "brandzone" not in cid_low:
        # 1. 매체 판별
        if "ps_naver" in cid_low:
            m_fin = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
            t_fin = "pro"
        elif "ps_google" in cid_low:
            m_fin = "google"
            t_fin = "retargeting" if "retargeting" in cid_low else "prospecting"
        else: # ps_daum
            m_fin = "kakaomo" if any(x in cid_low for x in ["-mo-", "_mo"]) else "kakaopc"
            t_fin = "prospecting"

        # 2. 캠페인 키 결정: waterbottle, dailywear는 무조건 product
        if any(x in cid_low for x in ["product", "dailywear", "waterbottle"]):
            c_fin = "product"
        elif "activity" in cid_low:
            c_fin = "activity"
        else:
            c_fin = "brand"

        # 3. 단계 결정
        l_fin = "middle-dm" if c_fin in ["product", "activity"] else "lower-dm"

        # 4. (예외) 엑셀 수식 12줄 (문자열 완전 일치 시 최우선)
        if "keyword-brand_alwayson-na-na_mo" in cid_low: return "brand-lower-dm-pro-navermo"
        if "keyword-brand_alwayson-na-na_pc" in cid_low: return "brand-lower-dm-pro-naverpc"
        if "keyword-product_alwayson-na-na_mo" in cid_low: return "product-middle-dm-pro-navermo"
        if "keyword-product_alwayson-na-na_pc" in cid_low: return "product-middle-dm-pro-naverpc"
        if "keyword-activity_alwayson-na-na_mo" in cid_low: return "activity-middle-dm-pro-navermo"
        if "keyword-activity_alwayson-na-na_pc" in cid_low: return "activity-middle-dm-pro-naverpc"

        # 5. 위 수식에 없어도 ps_naver_waterbottle 등은 여기서 최종 조립
        return f"{c_fin}-{l_fin}-{t_fin}-{m_fin}"

    # [STEP 4] 기타 고정 매칭 (Brandzone, PMAX, SMS, dsp_kakao-kw)
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

    # [STEP 5] 일반 매체 조립 (Meta, Criteo, YouTube 등)
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

    # [STEP 6] 캠페인 키 Prefix 결정
    if media == "criteo": camp = "alwayson"
    elif any(x in cid_low for x in ["holiday-winter2025-general", "becalm", "steadystate", "bigcozy"]): camp = "Holiday"
    elif "prospecting-custom-runnigstorekw" in cid_low or "logorun" in cid_low: camp = "Run"
    elif "train-winter2025-train" in cid_low: camp = "Train"
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "bottoms-spring2026-otm" in cid_low: camp = "pants" if media == "naverda" else "Pants"
    elif "men-2026-alwayson" in cid_low: camp = "men"
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson"]): camp = "alwayson"
    else: camp = "alwayson"

    # [STEP 7] 단계 & 타겟 조립
    lvl = "lower-dm" if ("lower" in cid_low or "retargeting" in cid_low) else ("upper-dm" if ("upper" in cid_low or "prospecting" in cid_low) else "middle-dm")
    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    
    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행 UI부 ---
if st.button("🚀 전체 로직 100% 통합 검사 시작"):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            if camp_col:
                # 대소문자 무시 비교
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip().lower() == str(x['AI_조립결과']).strip().lower() else "❌ 불일치", axis=1)
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                st.success(f"검사 완료! 일치: {len(df)-len(mismatches):,} / 불일치: {len(mismatches):,}")
                st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
    except Exception as e:
        st.error(f"오류: {e}")
