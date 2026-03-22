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

    if cid_raw == "" or "_adef-" in cid_low: return "Unknown"

    # 1. 매체 판별 (생략 - 기존 로직 유지)
    # ... (생략) ...
    media = "meta" # 예시를 위해 meta로 가정

    # 2. 캠페인 Prefix (사용자님 요청 순서로 재배치)
    camp = "alwayson"

    # [규칙 1] Holiday 강제 키워드
    if any(x in cid_low for x in ["becalm", "steadystate", "bigcozy"]):
        camp = "Holiday"
    
    # [규칙 2] 사용자 지정 캠페인 키 (태그 우선 감지)
    elif "train-winter2025-train" in cid_low:
        camp = "Train"
    elif "yet-spring2026-run" in cid_low:
        camp = "26Run"
    elif "holiday-winter2025-general" in cid_low:
        camp = "Holiday"
    elif "bottoms-spring2026-otm" in cid_low:
        camp = "pants" if "dsp_naver" in cid_low else "Pants"
    
    # [규칙 3] 시즌형 Alwayson 보호 (이게 있어야 소재명에 안 낚임)
    elif any(x in cid_low for x in ["winter-2026-alwayson", "spring-2026-alwayson", "men-2026-alwayson"]):
        camp = "alwayson"
    
    # [규칙 4] 그 외 일반 매체용 product/activity/brand
    # (생략)

    # 3. 단계 및 타겟 조립 (기존 로직 유지)
    # ...
    
    # 예시 결과물 조립
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
