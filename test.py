import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="6만행 전수 검사 (최종)", layout="wide")

# 1. 시트 설정
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506"  # 맵핑 탭의 GID

def has_token(text, token):
    # 단어가 앞뒤로 [시작, 끝, _, -]로 확실히 구분될 때만 True
    return re.search(rf'(^|[_-]){re.escape(token)}([_-]|$)', text) is not None

def build_perfect_key(cid):
    if pd.isna(cid): return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    if cid_raw == "" or "_adef-" in cid_low: return "Unknown"
    if cid_low == "sms_senders": return "SMS_Senders"
    if "navershopping" in cid_low: return "Naver shopping"
    
    # [특수] 브랜드존 일회성 코드 Unknown 처리
    if "ps_naver" in cid_low and "daily" in cid_low: return "Unknown"

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
    elif "naverpc" in cid_low: media = "naverpc"
    elif "navermo" in cid_low: media = "navermo"
    elif "criteo" in cid_low: media = "criteo"

    # 2. 캠페인 Prefix (사용자 가이드 반영)
    camp = "alwayson"
    
    # [A] 특정 매체 그룹 (dsp_naver, dsp_kakao, smp_fbig) 전용 로직
    if media in ["kakaoda", "kakaodaC", "kakaodaD", "meta", "metaC", "metam3", "naverda"]:
        if any(x in cid_low for x in ["steadystate", "becalm", "bigcozy"]):
            camp = "Holiday"
        elif "logorun" in cid_low or "_run_" in cid_low:
            camp = "Run"
        elif "train-winter2025-train" in cid_low or "train2025" in cid_low:
            camp = "Train"
        elif "bottoms-spring2026-otm" in cid_low or "pants" in cid_low:
            # [규칙] naverda만 소문자 pants
            camp = "pants" if media == "naverda" else "Pants"
        elif "yet-spring2026-run" in cid_low:
            camp = "26Run"
        elif "holiday-winter2025-general" in cid_low:
            camp = "Holiday"
        # 그 외에는 모두 alwayson (brand, activity 판별 안 함)
    else:
        # [B] 그 외 매체 (google, YouTube 등)
        if has_token(cid_low, "product"): camp = "product"
        elif has_token(cid_low, "activity"): camp = "activity"
        elif has_token(cid_low, "brand"): camp = "brand"

    # 3. 단계(Funnel)
    lvl = "middle-dm"
    if has_token(cid_low, "upper"): lvl = "upper-dm"
    elif has_token(cid_low, "lower"): lvl = "lower-dm"

    # [규칙] naverda 매체는 lower를 middle로 고정
    if media == "naverda" and lvl == "lower-dm":
        lvl = "middle-dm"

    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        lvl = "BS-dm"

    # 4. 타겟(Target)
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    if media in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]:
        target = "pro"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 실행부 ---
if st.button("🚀 시트 연결 및 전수 검사 시작"):
    try:
        # gid 파라미터를 포함하여 정확한 탭 연결
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(csv_url)
        
        df.columns = [c.strip() for c in df.columns]
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            if camp_col:
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip() == str(x['AI_조립결과']).strip() else "❌ 불일치", axis=1)
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                
                st.success(f"연결 완료! 일치: {len(df)-len(mismatches):,} / 불일치: {len(mismatches):,}")
                if not mismatches.empty:
                    st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
                else:
                    st.balloons()
            else:
                st.dataframe(df[[cid_col, 'AI_조립결과']].head(1000))
        else:
            st.error("CID 열을 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"시트 연결 오류: {e}")
