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

    # [0] 최우선 필터링 (Unknown 처리 5종 및 빈값)
    unknown_keywords = ["_adef-", "_br_", "brandsearch", "ps_naver_daily", "ps_naver_campaign"]
    if any(x in cid_low for x in unknown_keywords) or cid_raw == "":
        return "Unknown"

    # 기본 특수 매체
    if "navershopping" in cid_low: return "Naver shopping"
    if "sms" in cid_low: return "SMS_Senders"
    
    # [1] 고정 매칭 규칙
    # dsp_kakao-kw 고정
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"
    
    # kakaooptin (kakaopn, kakao-opt-in, pu_, transactional) 고정
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    # 브랜드존 (naver-brandzone, daum-brandzone) 고정
    if "naver-brandzone" in cid_low:
        sub = "naverbsmo" if any(x in cid_low for x in ["_mo-", "-mo-"]) else "naverbspc"
        return f"alwayson-BS-dm-pro-{sub}"
    if "daum-brandzone" in cid_low:
        sub = "kakaobsmo" if any(x in cid_low for x in ["_mo-", "-mo-"]) else "kakaobspc"
        return f"alwayson-BS-dm-pro-{sub}"

    # [2] PS_ 검색 광고 (Google / Naver / Daum)
    if "ps_naver" in cid_low or "ps_google" in cid_low or "ps_daum" in cid_low:
        if "ps_naver" in cid_low:
            m_fin = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
            t_fin = "pro"
        elif "ps_google" in cid_low:
            m_fin = "google"
            t_fin = "retargeting" if "retargeting" in cid_low else "prospecting"
        else: # ps_daum
            m_fin = "kakaomo" if "-mo-" in cid_low else "kakaopc"
            t_fin = "prospecting"

        if "brand" in cid_low: c_fin = "brand"
        elif "product" in cid_low: c_fin = "product"
        elif "activity" in cid_low: c_fin = "activity"
        else: c_fin = "brand"

        if "lower" in cid_low: l_fin = "lower-dm"
        elif any(x in cid_low for x in ["middle", "product", "activity"]): l_fin = "middle-dm"
        else: l_fin = "lower-dm"
        return f"{c_fin}-{l_fin}-{t_fin}-{m_fin}"

    # [3] PMAX 엄격 규칙
    if "pmax" in cid_low:
        if "w_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxW"
        if "m_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxM"
        if "prospecting-demo-all" in cid_low: return "alwayson-middle-dm-prospecting-pmaxC"
        return "Unknown"

    # [4] 일반 매체 판별
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
    elif "kakaotalksa" in cid_low or "kakaochannel" in cid_low: media = "kakaotalksa"

    # [5] 캠페인 키 (Prefix) 결정 - 우선순위 정밀 조정
    # Criteo는 무조건 alwayson
    if media == "criteo":
        camp = "alwayson"
    # 1. Holiday 강제
    elif any(x in cid_low for x in ["becalm", "steadystate", "bigcozy"]):
        camp = "Holiday"
    # 2. [추가] Runingstorekw 우선 (Run으로 시작)
    elif "prospecting-custom-runnigstorekw" in cid_low or "logorun" in cid_low:
        camp = "Run"
    # 3. 주요 캠페인 태그
    elif "train-winter2025-train" in cid_low: camp = "Train"
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "holiday-winter2025-general" in cid_low: camp = "Holiday"
    elif "bottoms-spring2026-otm" in cid_low:
        camp = "pants" if media == "naverda" else "Pants"
    elif "men-2026-alwayson" in cid_low:
        camp = "men"
    # 4. 시즌형 Alwayson 보호
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson"]):
        camp = "alwayson"
    else:
        camp = "alwayson"

    # [6] 단계 (Funnel)
    if "lower" in cid_low or "retargeting" in cid_low: lvl = "lower-dm"
    elif "upper" in cid_low or "prospecting" in cid_low: lvl = "upper-dm"
    else: lvl = "middle-dm"

    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"

    # [7] 타겟 (Target)
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    if media in ["navermo", "naverpc", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]: 
        target = "pro"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행 UI ---
if st.button("🚀 전수 검사 최종 마스터 버전 실행"):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            if camp_col:
                # 대소문자 무시 비교로 일치율 극대화
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip().lower() == str(x['AI_조립결과']).strip().lower() else "❌ 불일치", axis=1)
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                st.success(f"검사 완료! 일치: {len(df)-len(mismatches):,} / 불일치: {len(mismatches):,}")
                st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
    except Exception as e:
        st.error(f"오류: {e}")
