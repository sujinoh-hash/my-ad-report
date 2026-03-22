import streamlit as st
import pandas as pd

st.set_page_config(page_title="맵핑 기준값 검증기", layout="wide")

# --- 매핑 로직 (사용자님 피드백 반영 v11) ---
def build_final_key_v11(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid = str(cid).lower().strip()
    
    # [특수] 네이버 쇼핑 / SMS
    if "navershopping" in cid: return "Naver shopping"
    if "sms" in cid: return "SMS_Senders"
    
    # [1] 브랜드존 / 브랜드검색 (BS)
    if any(x in cid for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        m = "naverbsmo" if "mo-" in cid else "naverbspc"
        if "kakaobsp" in cid: m = "kakaobsmo" if "mo-" in cid else "kakaobspc"
        return f"alwayson-BS-dm-pro-{m}"

    # [2] 매체명 (Media)
    media = "google" # ps_google 대응
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
    
    # [4] 퍼널 & 타겟팅
    lvl = "upper-dm" if "upper" in cid else ("lower-dm" if "lower" in cid else "middle-dm")
    tgt = "retargeting" if "retargeting" in cid else "prospecting"
    if any(x in cid for x in ["navermo", "naverpc", "kakaotalksa", "kakao-kw"]):
        tgt = "pro"

    return f"{camp}-{lvl}-{tgt}-{media}"

# --- 메인 UI ---
st.title("🔎 '맵핑' 시트 기준값 검증")

# 시트 정보 (맵핑 탭의 GID로 바꿔주세요!)
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506" # 예: 0 또는 숫자

if st.button("📊 맵핑 데이터 불러와서 로직 검증"):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAPPING_GID}"
        df = pd.read_csv(url)
        
        # 헤더 확인 및 매핑 실행
        if 'CID' in df.columns:
            df['AI_조립결과'] = df['CID'].apply(build_final_key_v11)
            
            # 정답(캠페인명)과 AI 결과가 다른 것만 골라내기
            df['일치여부'] = df.apply(lambda x: "✅ 일치" if str(x['캠페인명']).strip() == str(x['AI_조립결과']).strip() else "❌ 불일치", axis=1)
            
            st.success(f"✅ 맵핑 시트 데이터 로드 완료!")
            
            # 결과 테이블
            st.subheader("📋 매핑 검증 리포트")
            st.dataframe(df[['CID', '캠페인명', 'AI_조립결과', '일치여부']])
            
            # 불일치 항목만 따로 보기
            mismatches = df[df['일치여부'] == "❌ 불일치"]
            if not mismatches.empty:
                st.warning(f"⚠️ 총 {len(mismatches)}개의 불일치 항목이 발견되었습니다. 규칙 수정이 필요합니다.")
                st.dataframe(mismatches)
            else:
                st.balloons()
                st.success("🎉 모든 맵핑 기준값이 AI 로직과 100% 일치합니다!")
        else:
            st.error(f"시트에서 'CID' 헤더를 찾을 수 없습니다. 현재 헤더: {df.columns.tolist()}")

    except Exception as e:
        st.error(f"오류 발생: {e}")
