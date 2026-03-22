import streamlit as st
import pandas as pd

st.set_page_config(page_title="6만행 매핑 최종 검증기", layout="wide")

def build_perfect_key(cid):
    # [0] 기본 필터링: 비어있거나 옛날 코드(_adef-)는 무조건 Unknown
    if pd.isna(cid) or str(cid).strip() == "" or "_adef-" in cid:
        return "Unknown"
    
    cid_low = str(cid).lower().strip()
    
    # [1] 매체명(Media) 판별
    media = "google"
    if "navershopping" in cid_low: return "Naver shopping"
    
    # 브랜드검색류
    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver"]):
        media = "naverbsmo" if "mo-" in cid_low else "naverbspc"
    elif "kakaobsp" in cid_low:
        media = "kakaobsmo" if "mo-" in cid_low else "kakaobspc"
    # 일반 매체
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

    # [2] 캠페인키(Prefix) 판별 - 우선순위 조정
    camp = "alwayson"
    
    # (1) Holiday 예외 키워드 (가장 높은 우선순위)
    if any(x in cid_low for x in ["becalm", "bigcozy", "steadystate"]):
        camp = "Holiday"
    # (2) 명확한 시즌 태그
    elif "yet-spring2026-run" in cid_low: 
        camp = "26Run"
    elif "bottoms-spring2026-otm" in cid_low: 
        # naverda일 때만 소문자 pants로 매칭 (사용자 리스트 기준)
        camp = "pants" if media == "naverda" else "Pants"
    elif "train-winter" in cid_low: 
        camp = "Train"
    elif "holiday-winter2025" in cid_low: 
        camp = "Holiday"
    # (3) winter-2026-alwayson 세부 판별
    elif "winter-2026-alwayson" in cid_low:
        if "_run_" in cid_low or "logorun" in cid_low: camp = "Run"
        elif "_casual_" in cid_low: camp = "Holiday"
        else: camp = "alwayson"
    # (4) 기타 카테고리 (태그가 없을 때만 적용)
    elif "men-2026" in cid_low: camp = "men"
    elif "product" in cid_low: camp = "product"
    elif "activity" in cid_low: camp = "activity"
    elif "brand" in cid_low: camp = "brand"

    # [3] 단계(Funnel) 조립
    lvl = "middle-dm"
    if "upper" in cid_low: lvl = "upper-dm"
    elif "lower" in cid_low: lvl = "lower-dm"
    
    # [사용자 요청] naverda의 lower만 middle로 변환
    if media == "naverda" and lvl == "lower-dm":
        lvl = "middle-dm"
    
    # 브랜드검색 단계 고정
    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        lvl = "BS-dm"

    # [4] 타겟팅(Target) 조립
    target = "prospecting"
    if "retargeting" in cid_low: target = "retargeting"
    
    # 검색광고형 타겟팅 명칭 보정 (pro)
    if any(x in media for x in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        target = "pro"
        
    # [특수] 카카오 옵트인 매체 처리
    if "transactional" in cid_low: return "alwayson-lower-dm-kakaooptin-transactional"
    if "kakaopn" in cid_low: return "alwayson-lower-dm-kakaooptin-kakaopn"

    # [5] 최종 조립 및 Unknown 필터링 (정의되지 않은 패턴은 Unknown 처리)
    result = f"{camp}-{lvl}-{target}-{media}"
    
    # ps_naver로 시작하는데 날짜 태그 등이 없는 경우(daily/campaign brandzone 등) Unknown 처리
    if cid_low.startswith("ps_") and "26" not in cid_low and "25" not in cid_low:
        return "Unknown"

    return result

# --- 메인 실행부 ---
st.title("📊 6만행 전수 매핑 검증 (수정본 v14)")

SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" 

if st.button("🚀 데이터 분석 시작"):
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
                st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(500))
            else:
                st.dataframe(df[[cid_col, 'AI_조립결과']].head(1000))
    except Exception as e:
        st.error(f"오류: {e}")
