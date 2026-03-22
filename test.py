import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="6만행 매핑 최종 검증", layout="wide")

# 1. 시트 설정
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" 

def has_token(text, token):
    return re.search(rf'(^|[_-]){re.escape(token)}([_-]|$)', text) is not None

def build_perfect_key(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # [0] 필터링 및 특수 케이스 (Unknown / Naver Shopping / SMS)
    if cid_raw == "" or "_adef-" in cid_low: return "Unknown"
    if "navershopping" in cid_low: return "Naver shopping"
    if "sms" in cid_low: return "SMS_Senders"

    # [1] 매체(Media) 판별 (브랜드존 우선)
    media = "google"
    # 네이버 브랜드존
    if "naver-brandzone" in cid_low:
        media = "naverbsmo" if "_mo-" in cid_low else "naverbspc"
    # 다음 브랜드존
    elif "daum-brandzone" in cid_low:
        media = "kakaobsmo" if "_mo-" in cid_low else "kakaobspc"
    # 일반 매체
    elif "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low:
        media = "kakaodaD" if "_pcmo" in cid_low else "kakaoda"
        if "catalog" in cid_low: media = "kakaodaC"
    elif any(x in cid_low for x in ["smp_fbig", "smp_ig", "meta"]):
        media = "metaC" if any(x in cid_low for x in ["catalog", "alwayson-na-na"]) else "meta"
        if "prospecting-na-na" in cid_low: media = "metam3"
    elif "pmax" in cid_low:
        for p in ["pmaxa", "pmaxw", "pmaxm", "pmaxc"]:
            if p in cid_low: media = p.replace("pmax", "pmax").upper(); break
    elif "kakaopn" in cid_low or "welcomemessage" in cid_low: media = "kakaooptin"
    elif "kakaochannelkeyword" in cid_low or "kakaotalksa" in cid_low: media = "kakaotalksa"
    elif "naverpc" in cid_low: media = "naverpc"
    elif "navermo" in cid_low: media = "navermo"
    elif "criteo" in cid_low: media = "criteo"

    # [2] 캠페인 키(Prefix) 판별 (우선순위 중요)
    camp = "alwayson"
    
    # 1. 브랜드존 고정
    if any(x in media for x in ["naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        camp = "brand"
    # 2. Holiday 강제 키워드
    elif any(x in cid_low for x in ["becalm", "steadystate", "bigcozy"]):
        camp = "Holiday"
    # 3. 26Run
    elif "yet-spring2026-run" in cid_low:
        camp = "26Run"
    # 4. Pants (naverda만 소문자)
    elif any(x in cid_low for x in ["bottoms-spring2026-otm", "otm_mo", "otm_pcmo", "pants"]):
        camp = "pants" if media == "naverda" else "Pants"
    # 5. Run (logorun 키워드 포함 시)
    elif "logorun" in cid_low or "_run_" in cid_low:
        camp = "Run"
    # 6. 기타 시즌/타겟
    elif "train-winter2025-train" in cid_low or "train_mo" in cid_low: camp = "Train"
    elif "holiday-winter2025-general" in cid_low or "general_mo" in cid_low: camp = "Holiday"
    elif "men-2026-alwayson" in cid_low: camp = "men"
    # 7. DA 매체 외 (Google 등) product/activity/brand
    elif media not in ["naverda", "kakaoda", "kakaodaD", "meta", "metaC"]:
        if has_token(cid_low, "product"): camp = "product"
        elif has_token(cid_low, "activity"): camp = "activity"
        elif has_token(cid_low, "brand"): camp = "brand"

    # [3] 단계(Funnel) 결정
    lvl = "middle-dm"
    if has_token(cid_low, "upper") or "prospecting" in cid_low: lvl = "upper-dm"
    elif has_token(cid_low, "lower") or "retargeting" in cid_low: lvl = "lower-dm"
    
    # [규칙] 브랜드존은 BS-dm
    if any(x in media for x in ["naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        lvl = "BS-dm"
    # [규칙] naverda 매체는 lower를 middle로 고정
    if media == "naverda" and lvl == "lower-dm":
        lvl = "middle-dm"

    # [4] 타겟(Target) 결정
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    # 검색형 매체 'pro' 고정
    if media in ["navermo", "naverpc", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]:
        target = "pro"

    # [5] 최종 조립 및 예외 리턴 (카카오 옵트인 등)
    if media == "kakaooptin":
        suffix = "transactional" if "transactional" in cid_low else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행부 ---
if st.button("🚀 최종 로직 전수 검사 시작"):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            if camp_col:
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip() == str(x['AI_조립결과']).strip() else "❌ 불일치", axis=1)
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                st.success(f"분석 완료! 일치: {len(df)-len(mismatches):,} / 불일치: {len(mismatches):,}")
                if not mismatches.empty:
                    st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
                else:
                    st.balloons()
    except Exception as e:
        st.error(f"오류: {e}")
