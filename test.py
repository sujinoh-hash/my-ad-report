import streamlit as st
import pandas as pd

st.set_page_config(page_title="6만행 최종 매핑 검증기", layout="wide")

def build_perfect_key(cid):
    if pd.isna(cid) or str(cid).strip() == "" or "_adef-" in cid:
        return "Unknown"
    
    cid_low = str(cid).lower().strip()
    
    # 1. 매체명(Media) 판별
    media = "google"
    if "navershopping" in cid_low: return "Naver shopping"
    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver"]):
        media = "naverbsmo" if "mo-" in cid_low else "naverbspc"
    elif "kakaobsp" in cid_low:
        media = "kakaobsmo" if "mo-" in cid_low else "kakaobspc"
    elif "dsp_yt" in cid_low: 
        media = "YouTube"
    elif "dsp_naver" in cid_low: 
        media = "naverda"
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
    elif "kakao-kw" in cid_low or "kakaotalksa" in cid: media = "kakaotalksa"
    elif "naverpc" in cid_low: media = "naverpc"
    elif "navermo" in cid_low: media = "navermo"
    elif "criteo" in cid_low: media = "criteo"

    # 2. 캠페인키(Prefix) 판별
    camp = "alwayson"
    
    # [Holiday 특수 규칙] becalm, bigcozy, steadystate가 있으면 무조건 Holiday
    if any(x in cid_low for x in ["becalm", "bigcozy", "steadystate"]):
        camp = "Holiday"
    # [시즌 및 카테고리 우선순위]
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "bottoms-spring2026-otm" in cid_low: camp = "Pants"
    elif "train-winter" in cid_low: camp = "Train"
    elif "holiday-winter2025" in cid_low or "casual" in cid_low: camp = "Holiday"
    elif "men-2026" in cid_low: camp = "men"
    elif "product" in cid_low: camp = "product"
    elif "activity" in cid_low: camp = "activity"
    elif "brand" in cid_low: camp = "brand"

    # 3. 단계(Funnel) 조립
    lvl = "middle-dm"
    if "upper" in cid_low: lvl = "upper-dm"
    elif "lower" in cid_low: lvl = "lower-dm"
    
    # [단계 강제 고정 규칙]
    if media == "naverda" and lvl == "lower-dm": lvl = "middle-dm"
    if camp in ["Pants", "Holiday"] and lvl == "lower-dm": lvl = "middle-dm"
    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]): lvl = "BS-dm"

    # 4. 타겟팅(Target) 조립
    target = "prospecting"
    if "retargeting" in cid_low: target = "retargeting"
    if any(x in media for x in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        target = "pro"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 메인 실행 UI ---
st.title("📊 6만행 전수 매핑 검증 (최종 로직)")

SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" # 맵핑 탭 GID 확인 필요

if st.button("🚀 전체 데이터 분석 시작"):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(url)
        
        # 열 이름 전처리 (공백 제거 등)
        df.columns = [c.strip() for c in df.columns]
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            if camp_col:
                # 공백 제거 후 비교
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip() == str(x['AI_조립결과']).strip() else "❌ 불일치", axis=1)
                
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                st.success(f"검사 완료! 일치: {len(df)-len(mismatches):,} / 불일치: {len(mismatches):,}")
                
                if not mismatches.empty:
                    st.subheader("⚠️ 불일치 항목 (Top 500)")
                    st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
                else:
                    st.balloons()
                    st.success("🎉 축하합니다! 모든 데이터가 일치합니다.")
            else:
                st.dataframe(df[[cid_col, 'AI_조립결과']].head(1000))
        else:
            st.error(f"CID 열을 찾을 수 없습니다. 현재 컬럼: {df.columns.tolist()}")
            
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
