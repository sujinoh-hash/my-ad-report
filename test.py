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

    # [A] 엑셀 IFS 수식 기반 "절대 매핑" 규칙 (이게 틀리면 안 됨)
    # 1. Naver Shopping / SMS
    if "navershopping" in cid_low: return "Naver shopping"
    if "sms" in cid_low: return "SMS_Senders"
    
    # 2. PMAX 엄격 규칙
    if "pmax" in cid_low:
        if "w_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxW"
        if "m_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxM"
        if "prospecting-demo-all" in cid_low: return "alwayson-middle-dm-prospecting-pmaxC"
        return "Unknown"

    # 3. 브랜드존 (Naver/Daum) - 사용자 최신 피드백 반영
    if "naver-brandzone" in cid_low:
        sub = "naverbsmo" if any(x in cid_low for x in ["_mo-", "-mo-"]) else "naverbspc"
        return f"brand-BS-dm-pro-{sub}"
    if "daum-brandzone" in cid_low:
        sub = "kakaobsmo" if any(x in cid_low for x in ["_mo-", "-mo-"]) else "kakaobspc"
        return f"brand-BS-dm-pro-{sub}"

    # 4. PS_ 검색 광고 (Google/Naver/Daum) - 정교한 매칭
    if "ps_google" in cid_low:
        if "keyword-brand" in cid_low:
            t = "retargeting" if "retargeting" in cid_low else "prospecting"
            # IFS 수식에 따라 brand-lower-dm 고정
            if "alwayson-na-na_pcmo" in cid_low: return f"brand-lower-dm-{t}-google"
        if "prospecting-keyword-product" in cid_low: return "product-middle-dm-prospecting-google"
        if "prospecting-keyword-activity" in cid_low: return "activity-middle-dm-prospecting-google"
        # IFS에 없는 ps_google은 Unknown
        if not any(x in cid_low for x in ["retargeting", "prospecting"]): return "Unknown"

    if "ps_daum_brand" in cid_low:
        sub = "kakaomo" if "-mo-" in cid_low else "kakaopc"
        return f"brand-lower-dm-prospecting-{sub}"

    if "ps_naver" in cid_low:
        sub = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
        if "keyword-brand" in cid_low and "alwayson-na-na" in cid_low: return f"brand-lower-dm-pro-{sub}"
        if "keyword-product" in cid_low and "alwayson-na-na" in cid_low: return f"product-middle-dm-pro-{sub}"
        if "keyword-activity" in cid_low and "alwayson-na-na" in cid_low: return f"activity-middle-dm-pro-{sub}"
        if "mo-imagesublink" in cid_low and any(x in cid_low for x in ["yoga", "pilates"]): return "activity-middle-dm-pro-navermo"
        # 연도(25, 26) 없는 ps_naver는 Unknown
        if not any(x in cid_low for x in ["25", "26"]): return "Unknown"

    # [B] 일반 매체 조립 로직 (Meta, YouTube, DA 등)
    media = "google"
    if "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low:
        media = "kakaodaD" if "_pcmo" in cid_low else "kakaoda"
        if "catalog" in cid_low: media = "kakaodaC"
    elif any(x in cid_low for x in ["meta", "smp_fbig", "smp_ig"]):
        media = "metaC" if any(x in cid_low for x in ["catalog", "alwayson-na-na"]) else "meta"
        if "prospecting-na-na" in cid_low: media = "metam3"
    elif "kakaopn" in cid_low or "welcomemessage" in cid_low: media = "kakaooptin"
    elif "kakaotalksa" in cid_low or "kakaochannel" in cid_low: media = "kakaotalksa"
    elif "criteo" in cid_low: media = "criteo"

    # 캠페인 키 (Prefix)
    camp = "alwayson"
    if any(x in cid_low for x in ["becalm", "steadystate", "bigcozy"]): camp = "Holiday"
    elif "train-winter2025-train" in cid_low: camp = "Train"
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "bottoms-spring2026-otm" in cid_low: camp = "pants" if media == "naverda" else "Pants"
    elif "men-2026-alwayson" in cid_low: camp = "men"
    elif "holiday-winter2025-general" in cid_low: camp = "Holiday"
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson"]): camp = "alwayson"
    elif "logorun" in cid_low: camp = "Run"

    # 단계 (Funnel) - [수정] lower를 prospecting보다 먼저 체크
    if "lower" in cid_low or "retargeting" in cid_low: lvl = "lower-dm"
    elif "upper" in cid_low or "prospecting" in cid_low: lvl = "upper-dm"
    elif "middle" in cid_low: lvl = "middle-dm"
    else: lvl = "middle-dm"

    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"

    # 타겟 (Target)
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    if media in ["navermo", "naverpc", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]: target = "pro"

    # 최종 예외 조립
    if media == "kakaooptin":
        sfx = "transactional" if "transactional" in cid_low else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{sfx}"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행 UI ---
if st.button("🚀 오류 수정 버전 전수 검사"):
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
