import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="6만행 전수 검사 (완결판)", layout="wide")

# 1. 시트 설정
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506 

def has_token(text, token):
    # 단어가 앞뒤로 시작/끝/_/-로 구분될 때만 True (정규식 강화)
    return re.search(rf'(^|[_-]){re.escape(token)}([_-]|$)', text) is not None

def build_perfect_key(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # 0. 필터링
    if cid_raw == "" or "_adef-" in cid_low: return "Unknown"
    if cid_low == "sms_senders": return "SMS_Senders"
    if "navershopping" in cid_low: return "Naver shopping"
    
    # 1. 매체(Media) 판별
    media = "google"
    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver"]):
        media = "naverbsmo" if "mo-" in cid_low else "naverbspc"
    elif "kakaobsp" in cid_low:
        media = "kakaobsmo" if "mo-" in cid_low else "kakaobspc"
    elif "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low:
        if "catalog" in cid_low: media = "kakaodaC"
        elif any(x in cid_low for x in ["native", "kakaodad", "video", "dual"]): media = "kakaodaD"
        else: media = "kakaoda"
    elif "meta" in cid_low or "smp_fbig" in cid_low:
        if "catalog" in cid_low and ("advantage" in cid_low or "pixel" in cid_low): media = "metaC"
        elif "prospecting-na-na" in cid_low: media = "metam3"
        else: media = "meta"
    elif "pmax" in cid_low:
        if any(x in cid_low for x in ["w_prospecting", "demo-women", "pmaxw"]): media = "pmaxW"
        elif "pmaxm" in cid_low: media = "pmaxM"
        else: media = "pmaxC"
    elif "kakao-kw" in cid_low or "kakaotalksa" in cid_low: media = "kakaotalksa"
    elif "kakaopn" in cid_low or "transactional" in cid_low: media = "kakaooptin"
    elif "naverpc" in cid_low: media = "naverpc"
    elif "navermo" in cid_low: media = "navermo"
    elif "criteo" in cid_low: media = "criteo"

    # 2. 캠페인 Prefix (우선순위 정밀 조정)
    camp = "alwayson"

    # [Priority 1] 특별 상품 키워드
    if any(x in cid_low for x in ["steadystate", "becalm", "bigcozy"]):
        camp = "Holiday"
    
    # [Priority 2] 명시적 로고런 (winter-2026 등이 있어도 Run이 이김)
    elif "logorun" in cid_low:
        camp = "Run"

    # [Priority 3] 구체적 캠페인 태그
    elif "yet-spring2026-run" in cid_low:
        camp = "26Run"
    elif "bottoms-spring2026-otm" in cid_low:
        camp = "pants" if media == "naverda" else "Pants"
    elif "train-winter2025-train" in cid_low:
        camp = "Train"
    elif "holiday-winter2025-general" in cid_low:
        camp = "Holiday"
    elif "men-2026-alwayson" in cid_low:
        camp = "men"
    
    # [Priority 4] 시즌형 Alwayson 쉴드 (일반 run/casual 키워드보다 강함)
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson"]):
        camp = "alwayson"

    # [Priority 5] 일반 키워드 판별
    elif "_run_" in cid_low or "run" in cid_low:
        camp = "Run"
    elif "pants" in cid_low:
        camp = "pants" if media == "naverda" else "Pants"

    # [Priority 6] DA/Meta 외 매체용 (product/activity/brand)
    if media not in ["kakaoda", "kakaodaC", "kakaodaD", "meta", "metaC", "metam3", "naverda"]:
        if camp == "alwayson":
            if has_token(cid_low, "product"): camp = "product"
            elif has_token(cid_low, "activity"): camp = "activity"
            elif has_token(cid_low, "brand"): camp = "brand"

    # 3. 단계(Funnel)
    lvl = "middle-dm"
    if has_token(cid_low, "upper"): lvl = "upper-dm"
    elif has_token(cid_low, "lower"): lvl = "lower-dm"

    # [사용자 요청] naverda 매체만 lower -> middle 변환
    if media == "naverda" and lvl == "lower-dm":
        lvl = "middle-dm"

    # 브랜드검색 단계 고정
    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        lvl = "BS-dm"

    # 4. 타겟(Target)
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    if media in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]:
        target = "pro"

    # 5. 특수 매체 최종 조립 (카카오 옵트인)
    if media == "kakaooptin":
        suffix = "transactional" if "transactional" in cid_low else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행 UI ---
if st.button("🚀 최종 로직으로 전수 검사 시작"):
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
                    st.success("🎉 모든 데이터가 완벽하게 일치합니다!")
    except Exception as e:
        st.error(f"오류: {e}")
