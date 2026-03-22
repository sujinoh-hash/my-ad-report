import streamlit as st
import pandas as pd

st.set_page_config(page_title="6만행 매핑 최종 검증기", layout="wide")

# 1. 시트 설정
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" 

def build_perfect_key(cid):
    # [0] Unknown 필터링 (최우선)
    if pd.isna(cid) or str(cid).strip() == "" or "_adef-" in cid:
        return "Unknown"
    
    cid_low = str(cid).lower().strip()
    
    # 특정 브랜드존/일반 브랜드 코드는 Unknown 처리
    if "ps_naver" in cid_low and ("brandzone" in cid_low or "daily" in cid_low): return "Unknown"
    if "ps_google" in cid_low and "brand" in cid_low: return "Unknown"

    # [1] 매체명(Media) 판별
    media = "google"
    if "navershopping" in cid_low: return "Naver shopping"
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

    # [2] 캠페인키(Prefix) 판별
    camp = "alwayson"
    
    # 1. 특정 키워드(Holiday)
    if any(x in cid_low for x in ["becalm", "bigcozy", "steadystate"]):
        camp = "Holiday"
    # 2. 26Run
    elif "yet-spring2026-run" in cid_low:
        camp = "26Run"
    # 3. Pants (naverda는 소문자 pants, 그 외엔 대문자 Pants)
    elif "bottoms-spring2026-otm" in cid_low or "pants" in cid_low:
        camp = "pants" if media == "naverda" else "Pants"
    # 4. Run (logorun 키워드 포함 시)
    elif "logorun" in cid_low or "_run_" in cid_low:
        camp = "Run"
    # 5. Train / Holiday 시즌 태그
    elif "train-winter" in cid_low or "train2025" in cid_low:
        camp = "Train"
    elif "holiday-winter2025" in cid_low:
        camp = "Holiday"
    # 6. 기타 카테고리
    elif "men-2026" in cid_low: camp = "men"
    elif "product" in cid_low: camp = "product"
    elif "activity" in cid_low: camp = "activity"
    elif "brand" in cid_low: camp = "brand"

    # [3] 단계(Funnel) 조립
    lvl = "middle-dm"
    if "upper" in cid_low: lvl = "upper-dm"
    elif "lower" in cid_low: lvl = "lower-dm"
    
    # [사용자 요청 핵심] naverda 매체만 lower -> middle 변환
    if media == "naverda" and lvl == "lower-dm":
        lvl = "middle-dm"
    
    # 브랜드검색 단계 고정
    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        lvl = "BS-dm"

    # [4] 타겟팅(Target) 조립
    target = "prospecting"
    if "retargeting" in cid_low: target = "retargeting"
    
    # 검색형 매체만 'pro' 사용
    if any(x in media for x in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        target = "pro"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 메인 실행부 ---
if st.button("🚀 데이터 전수 검사 (정밀 수정본)"):
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
                st.success(f"검사 완료! 일치: {len(df)-len(mismatches):,} / 불일치: {len(mismatches):,}")
                if not mismatches.empty:
                    st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
                else:
                    st.balloons()
                    st.success("🎉 모든 데이터가 일치합니다!")
            else:
                st.dataframe(df[[cid_col, 'AI_조립결과']].head(1000))
    except Exception as e:
        st.error(f"오류: {e}")
