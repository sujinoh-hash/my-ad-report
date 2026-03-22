import streamlit as st
import pandas as pd

st.set_page_config(page_title="맵핑 전수 검사기", layout="wide")

# --- 매핑 로직 (최신 업데이트 유지) ---
def build_perfect_key(cid):
    if pd.isna(cid) or str(cid).strip() == "" or "_adef-" in cid:
        return "Unknown"
    
    cid = str(cid).lower().strip()
    
    # 1. 매체명(Media) 판별
    media = "google"
    if "navershopping" in cid: return "Naver shopping"
    if any(x in cid for x in ["brandzone", "naverbsp", "ps_naver"]):
        media = "naverbsmo" if "mo-" in cid else "naverbspc"
    elif "kakaobsp" in cid:
        media = "kakaobsmo" if "mo-" in cid else "kakaobspc"
    elif "dsp_yt" in cid: media = "YouTube"
    elif "dsp_naver" in cid: media = "naverda"
    elif "dsp_kakao" in cid:
        media = "kakaodaD" if "native" in cid else "kakaoda"
    elif "meta" in cid or "fbig" in cid:
        media = "metaC" if "catalog" in cid and ("advantage" in cid or "pixel" in cid) else "meta"
        if "prospecting-na-na" in cid: media = "metam3"
    elif "pmax" in cid:
        if any(x in cid for x in ["w_prospecting", "demo-women", "pmaxw"]): media = "pmaxW"
        elif "pmaxm" in cid: media = "pmaxM"
        else: media = "pmaxC"
    elif "kakao-kw" in cid or "kakaotalksa" in cid: media = "kakaotalksa"
    elif "naverpc" in cid: media = "naverpc"
    elif "navermo" in cid: media = "navermo"

    # 2. 캠페인키(Prefix) 판별
    camp = "alwayson"
    if "brand" in cid: camp = "brand"
    elif "product" in cid: camp = "product"
    elif "activity" in cid: camp = "activity"
    elif "yet-spring2026-run" in cid: camp = "26Run"
    elif "men-2026" in cid: camp = "men"
    elif "bottoms-spring2026-otm" in cid: camp = "pants"
    elif "winter-2026-alwayson" in cid:
        camp = "Run" if "run" in cid else "Holiday"
    elif "train-winter" in cid: camp = "Train"

    # 3. 단계(Funnel) 및 타겟팅(Target) 조립
    lvl = "middle-dm"
    if "upper" in cid: lvl = "upper-dm"
    elif "lower" in cid: lvl = "lower-dm"
    
    if camp in ["product", "activity"] and lvl == "upper-dm": lvl = "middle-dm"
    if camp in ["pants", "Holiday"] and lvl == "lower-dm": lvl = "middle-dm"
    if "brandzone" in cid or "naverbsp" in cid or "ps_naver" in cid or "kakaobsp" in cid: lvl = "BS-dm"

    target = "retargeting" if "retargeting" in cid else "prospecting"
    if any(x in media for x in ["naverpc", "navermo", "kakaotalksa", "naverbsmo", "naverbspc", "kakaobsmo", "kakaobspc"]):
        target = "pro"

    return f"{camp}-{lvl}-{target}-{media}"

# --- 메인 실행부 ---
st.title("🚀 맵핑 데이터 전수 검사 (KeyError 방지)")

# 시트 설정 (ID와 GID가 맵핑 탭이 맞는지 꼭 확인하세요!)
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIXYrj0LSrcaYdgY"
# 맵핑 탭의 GID를 여기에 넣으세요 (어도비 탭 GID와 다를 수 있습니다)
MAPPING_GID = "1901484506" 

if st.button("📊 데이터 검사 시작"):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(url)
        
        # [해결책] 모든 컬럼명의 공백을 제거하고 대문자로 통일해서 비교
        df.columns = [c.strip() for c in df.columns]
        
        # 'CID'라는 이름이 들어간 컬럼 찾기
        cid_col = next((c for c in df.columns if 'CID' in c.upper()), None)
        camp_col = next((c for c in df.columns if '캠페인명' in c), None)

        if cid_col:
            st.info(f"'{cid_col}' 열을 사용하여 분석을 진행합니다.")
            df['AI_조립결과'] = df[cid_col].apply(build_perfect_key)
            
            if camp_col:
                df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x[camp_col]).strip() == str(x['AI_조립결과']).strip() else "❌ 불일치", axis=1)
                
                # 결과 출력
                st.success(f"검사 완료! 전체 {len(df):,}행")
                
                mismatches = df[df['일치여부'] == "❌ 불일치"]
                if not mismatches.empty:
                    st.warning(f"불일치 항목: {len(mismatches)}건")
                    st.dataframe(mismatches[[cid_col, camp_col, 'AI_조립결과']].head(200))
                else:
                    st.balloons()
                    st.success("모든 항목이 일치합니다!")
            else:
                st.dataframe(df[[cid_col, 'AI_조립결과']].head(200))
        else:
            st.error(f"시트에서 'CID' 열을 찾을 수 없습니다. 현재 시트의 열 이름: {df.columns.tolist()}")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
