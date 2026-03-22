import streamlit as st
import pandas as pd

st.set_page_config(page_title="6만행 최종 매핑 검증기", layout="wide")

# 1. 시트 설정 (GID를 여기서 꼭 확인해서 수정해주세요!)
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506"  # <--- '맵핑' 탭의 gid 숫자로 바꿔주세요!

def build_perfect_key(cid):
    if pd.isna(cid) or str(cid).strip() == "" or "_adef-" in cid:
        return "Unknown"
    
    cid_low = str(cid).lower().strip()
    
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

    # [2] 캠페인키(Prefix) 판별
    camp = "alwayson"
    
    # [특수 규칙 1] becalm, bigcozy, steadystate가 포함되면 Holiday
    if any(x in cid_low for x in ["becalm", "bigcozy", "steadystate"]):
        camp = "Holiday"
    # [특수 규칙 2] 시즌 및 태그 우선순위
    elif "yet-spring2026-run" in cid_low: camp = "26Run"
    elif "bottoms-spring2026-otm" in cid_low: camp = "pants" if media == "naverda" else "Pants"
    elif "train-winter" in cid_low: camp = "Train"
    elif "holiday-winter2025" in cid_low: camp = "Holiday"
    elif "winter-2026-alwayson" in cid_low:
        if "_run_" in cid_low or "logorun" in cid_low: camp = "Run"
        elif "casual" in cid_low: camp = "Holiday"
        else: camp = "alwayson"
    elif "men-2026" in cid_low: camp = "men"
    elif "product" in cid_low: camp = "product"
    elif "activity" in cid_low: camp = "activity"
    elif "brand" in cid_low: camp = "brand"

    # [3] 단계(Funnel) 조립
    lvl = "middle-dm"
    if "upper" in cid_low: lvl = "upper-dm"
    elif "lower" in cid_low: lvl = "lower-dm"
    
    # [특수 규칙 3] naverda 매체만 lower -> middle 변환
    if media == "naverda" and lvl == "lower-dm":
        lvl = "middle-dm"
    
    # 브랜드검색 단계 고정
    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        lvl = "BS-dm"

    # [4] 타겟팅(Target) 조립
    target = "prospecting"
    if "retargeting" in cid_low: target = "retargeting"
    if any(x in media for x in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        target = "pro"

    # [5] Unknown 필터링
    if cid_low.startswith("ps_") and "brandzone" not in cid_low and "naverbsp" not in cid_low:
        if "26" not in cid_low and "25" not in cid_low: return "Unknown"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 메인 실행부 ---
st.title("🚀 맵핑 데이터 전수 검사 (GID 연결 버전)")

if st.button("📊 데이터 분석 시작"):
    try:
        # GID를 URL에 정확히 포함시킴
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
                    st.warning("⚠️ 불일치 데이터 패턴 확인")
                    st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
                else:
                    st.balloons()
                    st.success("🎉 모든 데이터가 일치합니다!")
            else:
                st.dataframe(df[[cid_col, 'AI_조립결과']].head(1000))
        else:
            st.error(f"CID 열을 찾을 수 없습니다. (현재 시트 컬럼: {df.columns.tolist()})")
            
    except Exception as e:
        st.error(f"오류: {e}")
