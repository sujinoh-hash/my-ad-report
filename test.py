import streamlit as st
import pandas as pd

st.set_page_config(page_title="6만행 전수 검사기", layout="wide")

# --- 매핑 로직 (사용자님 피드백 반영 v10) ---
def build_final_key_v10(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid = str(cid).lower().strip()
    
    # [특수] 네이버 쇼핑 / SMS
    if "navershopping" in cid: return "Naver shopping"
    if "sms" in cid: return "SMS_Senders"
    
    # [1] 브랜드존 / 브랜드검색
    if any(x in cid for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        m = "naverbsmo" if "mo-" in cid else "naverbspc"
        if "kakaobsp" in cid: m = "kakaobsmo" if "mo-" in cid else "kakaobspc"
        return f"alwayson-BS-dm-pro-{m}"

    # [2] 매체명 (Media)
    media = "google"
    if "dsp_naver" in cid: media = "naverda"
    elif "dsp_kakao" in cid:
        media = "kakaodaD" if "native" in cid or "kakaodad" in cid else "kakaoda"
    elif "meta" in cid or "fbig" in cid:
        if "catalog" in cid and ("advantage" in cid or "pixel" in cid): media = "metaC"
        elif "prospecting-na-na" in cid: media = "metam3"
        else: media = "meta"
    elif "pmax" in cid:
        if any(x in cid for x in ["w_prospecting", "demo-women", "pmaxw"]): media = "pmaxW"
        elif "pmaxm" in cid: media = "pmaxM"
        else: media = "pmaxC"
    elif "kakao-kw" in cid or "kakaotalksa" in cid: media = "kakaotalksa"
    elif "naverpc" in cid: media = "naverpc"
    elif "navermo" in cid: media = "navermo"

    # [3] 캠페인키
    camp = "alwayson"
    target_media = ["dsp_kakao", "meta", "fbig", "dsp_naver"]
    if any(m in cid for m in target_media):
        if "yet-spring2026-run" in cid: camp = "26Run"
        elif "run-upper" in cid: camp = "Run"
        elif "train-winter" in cid: camp = "Train"
        elif "bottoms-spring" in cid or "pants" in cid: camp = "Pants"
        elif "holiday" in cid: camp = "Holiday"
    
    # [4] 퍼널 & 타겟팅
    lvl = "upper-dm" if "upper" in cid else ("lower-dm" if "lower" in cid else "middle-dm")
    tgt = "retargeting" if "retargeting" in cid else "prospecting"
    if any(x in cid for x in ["navermo", "naverpc", "kakaotalksa", "kakao-kw"]):
        tgt = "pro"

    return f"{camp}-{lvl}-{tgt}-{media}"

# --- 메인 화면 ---
st.title("🔎 어도비 6만 행 전수 검사")

SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
ADOBE_GID = "1818457274"

if st.button("🚀 데이터 6만 행 불러오기"):
    try:
        # 헤더가 [CID, 캠페인명, 매체] 임을 명시
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={ADOBE_GID}"
        
        # 6만 행을 안전하게 읽어오기 위해 데이터프레임 로드
        df = pd.read_csv(url)
        
        # 알려주신 헤더 'CID' 열을 타겟으로 잡음
        if 'CID' in df.columns:
            df['AI_조립결과'] = df['CID'].apply(build_final_key_v10)
            
            st.success(f"✅ 총 {len(df):,}행 로드 및 매핑 완료!")
            
            # 비교를 위해 상위 데이터 출력
            st.subheader("📋 매핑 결과 모니터링 (원본 캠페인명 vs AI 조립명)")
            # 기존 시트의 '캠페인명'과 제가 만든 'AI_조립결과'를 나란히 보여줌
            display_cols = ['CID', '캠페인명', 'AI_조립결과'] 
            st.dataframe(df[display_cols].head(500))
            
            # 요약 통계
            st.subheader("📊 조립된 캠페인명 종류별 개수")
            st.bar_chart(df['AI_조립결과'].value_counts())
            
        else:
            st.error(f"시트에서 'CID' 헤더를 찾을 수 없습니다. 현재 헤더: {df.columns.tolist()}")

    except Exception as e:
        st.error(f"오류 발생: {e}")
