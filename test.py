import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="6만행 전수 검사 최종", layout="wide")

# 1. 시트 설정
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" 

def has_token(text, token):
    return re.search(rf'(^|[_-]){re.escape(token)}([_-]|$)', text) is not None

def build_perfect_key(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    if cid_raw == "" or "_adef-" in cid_low: return "Unknown"
    
    # 변수 초기화
    media = "google"
    camp = "alwayson"
    lvl = "middle-dm"
    target = "prospecting"

    if "navershopping" in cid_low: return "Naver shopping"
    if "sms" in cid_low: return "SMS_Senders"

    # [1] 매체(Media) 판별
    if "naver-brandzone" in cid_low:
        media = "naverbsmo" if "_mo-" in cid_low else "naverbspc"
    elif "daum-brandzone" in cid_low:
        media = "kakaobsmo" if "_mo-" in cid_low else "kakaobspc"
    elif "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low:
        media = "kakaodaD" if "_pcmo" in cid_low else "kakaoda"
        if "catalog" in cid_low: media = "kakaodaC"
    elif any(x in cid_low for x in ["smp_fbig", "smp_ig", "meta"]):
        if any(x in cid_low for x in ["catalog", "alwayson-na-na"]): media = "metaC"
        elif "prospecting-na-na" in cid_low: media = "metam3"
        else: media = "meta"
    elif "pmax" in cid_low:
        if "pmaxa" in cid_low: media = "pmaxA"
        elif "pmaxw" in cid_low: media = "pmaxW"
        elif "pmaxm" in cid_low: media = "pmaxM"
        else: media = "pmaxC"
    elif "kakaopn" in cid_low or "welcomemessage" in cid_low: media = "kakaooptin"
    elif "kakaochannelkeyword" in cid_low or "kakaotalksa" in cid_low: media = "kakaotalksa"
    elif "naverpc" in cid_low: media = "naverpc"
    elif "navermo" in cid_low: media = "navermo"

    # [2] 캠페인 키(Prefix) 판별 - "캠페인 태그" 우선 원칙
    # 1. Holiday 강제 키워드
    if any(x in cid_low for x in ["becalm", "steadystate", "bigcozy"]):
        camp = "Holiday"
    # 2. 브랜드존
    elif any(x in media for x in ["naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        camp = "brand"
    # 3. 캠페인 태그 최우선 (이 태그들이 있으면 뒤의 소재명 pants, run 등 무시)
    elif "train-winter2025-train" in cid_low: camp = "Train"
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "holiday-winter2025-general" in cid_low: camp = "Holiday"
    elif "bottoms-spring2026-otm" in cid_low:
        camp = "pants" if media == "naverda" else "Pants"
    elif "men-2026-alwayson" in cid_low:
        camp = "men"
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson"]):
        camp = "alwayson"
    # 4. 태그가 없을 때만 소재명 판별
    elif "logorun" in cid_low: camp = "Run"
    
    # 5. 기타 매체(Google 등)
    elif media in ["google", "YouTube"]:
        if has_token(cid_low, "product"): camp = "product"
        elif has_token(cid_low, "activity"): camp = "activity"
        elif has_token(cid_low, "brand"): camp = "brand"

    # [3] 단계(Funnel) 결정
    if any(x in media for x in ["naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        lvl = "BS-dm"
    elif has_token(cid_low, "upper") or "prospecting" in cid_low:
        lvl = "upper-dm"
    elif has_token(cid_low, "lower") or "retargeting" in cid_low:
        lvl = "lower-dm"
    else:
        lvl = "middle-dm"

    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"

    # [4] 타겟(Target) 결정
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    if media in ["navermo", "naverpc", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]:
        target = "pro"

    # [5] 카카오 옵트인 특수 조립
    if media == "kakaooptin":
        suffix = "transactional" if "transactional" in cid_low else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행부 ---
if st.button("🚀 최종 검증 시작 (대소문자 무시)"):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            if camp_col:
                # 대소문자 무시하고 비교 (.lower() 적용)
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip().lower() == str(x['AI_조립결과']).strip().lower() else "❌ 불일치", axis=1)
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                st.success(f"검사 완료! 일치: {len(df)-len(mismatches):,} / 불일치: {len(mismatches):,}")
                st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
    except Exception as e:
        st.error(f"오류: {e}")
