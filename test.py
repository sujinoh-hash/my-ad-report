import streamlit as st
import pandas as pd

st.set_page_config(page_title="6만행 전수 검사기", layout="wide")

# --- 매핑 로직 (사용자님 피드백 100% 반영 버전) ---
def build_final_key_v9(cid):
    if pd.isna(cid): return "Unknown"
    cid = str(cid).lower().strip()
    
    # [특수] 네이버 쇼핑
    if "navershopping" in cid: return "Naver shopping"
    if "sms" in cid: return "SMS_Senders"
    
    # [1] 브랜드존 / 브랜드검색 (alwayson-BS-dm-pro-...)
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
        # 기기/타겟팅 구분 규칙 적용
        if any(x in cid for x in ["w_prospecting", "demo-women", "pmaxw"]): media = "pmaxW"
        elif "pmaxm" in cid: media = "pmaxM"
        else: media = "pmaxC"
    elif "kakao-kw" in cid or "kakaotalksa" in cid: media = "kakaotalksa"
    elif "naverpc" in cid: media = "naverpc"
    elif "navermo" in cid: media = "navermo"
    elif "youtube" in cid: media = "YouTube"
    elif "criteo" in cid: media = "criteo"

    # [3] 캠페인키 (dsp_kakao, meta, dsp_naver 이외엔 alwayson)
    camp = "alwayson"
    target_media = ["dsp_kakao", "meta", "fbig", "dsp_naver"]
    if any(m in cid for m in target_media):
        if "yet-spring2026-run" in cid: camp = "26Run"
        elif "run-upper" in cid: camp = "Run"
        elif "train-winter" in cid: camp = "Train"
        elif "bottoms-spring" in cid or "pants" in cid: camp = "Pants"
        elif "holiday" in cid: camp = "Holiday"
        elif "men-upper" in cid: camp = "men"
    
    # [4] 퍼널 & 타겟팅 조립
    lvl = "upper-dm" if "upper" in cid else ("lower-dm" if "lower" in cid else "middle-dm")
    tgt = "retargeting" if "retargeting" in cid else "prospecting"
    
    # 검색광고형 타겟팅 명칭 보정 (pro)
    if any(x in cid for x in ["navermo", "naverpc", "kakaotalksa", "kakao-kw"]):
        tgt = "pro"

    return f"{camp}-{lvl}-{tgt}-{media}"

# --- 메인 실행 UI ---
st.title("🔎 6만 행 전수 검사 결과")

# 시트 정보 (사용자님 정보 다시 확인)
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
ADOBE_GID = "1818457274"

if st.button("🚀 6만 행 매핑 시작 (구글 시트 연결)"):
    try:
        # CSV 출력 링크 생성
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={ADOBE_GID}"
        df = pd.read_csv(url)
        
        # 6만 행 처리 시작
        cid_col = df.columns[1] # 캠페인코드 열
        df['조립결과'] = df[cid_col].apply(build_final_key_v9)
        
        st.success(f"✅ 총 {len(df):,}행을 성공적으로 불러와서 매핑했습니다!")
        
        # 결과 요약
        st.subheader("📊 매핑된 캠페인명 종류 (중복 제거)")
        summary = df['조립결과'].value_counts().reset_index()
        summary.columns = ['캠페인명', '행 개수']
        st.dataframe(summary)
        
        st.subheader("⚠️ 원본 대비 매핑 결과 (상세)")
        st.dataframe(df[[cid_col, '조립결과']].head(500))
        
    except Exception as e:
        st.error(f"데이터를 불러오지 못했습니다. 구글 시트의 [공유] 설정이 '링크가 있는 모든 사용자'로 되어 있는지 확인해 주세요.")
        st.info(f"에러 상세: {e}")
