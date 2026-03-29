import streamlit as st
import pandas as pd
import io

# 화면 설정
st.set_page_config(page_title="룰루레몬 자동화 도구", layout="wide")

# --- [로직] v5 매핑 함수 (검증 완료된 최신 버전) ---
def build_perfect_key_v5(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # 1. 고정 매칭 (카톡SA, 페이코)
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"
    if "payco" in cid_low: return "alwayson-lower-dm-prospecting-payco"

    # 2. 카카오 옵트인
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    # 3. 네이버 쇼핑 / 브랜드검색
    if "navershopping" in cid_low: return "Naver shopping"
    if "brandzone" in cid_low:
        if "brandzone-na" not in cid_low: return "Unknown"
        sub = ("naverbsmo" if "naver" in cid_low else "kakaobsmo") if any(x in cid_low for x in ["_mo", "-mo"]) else ("naverbspc" if "naver" in cid_low else "kakaobspc")
        return f"alwayson-BS-dm-pro-{sub}"

    # 4. 크리테오 (Prospecting 예외)
    if "criteo" in cid_low:
        if "dsp_criteo" in cid_low and ("w_prospecting-demo-women" in cid_low or "m_prospecting-demo-men" in cid_low):
            return "alwayson-upper-dm-prospecting-criteo"
        if "lower" not in cid_low: return "Unknown"
        return "alwayson-lower-dm-retargeting-criteo"

    # 5. 네이버 스페셜 DA (naverdas)
    if "dsp_naver" in cid_low and "prospecting-demo-all" in cid_low:
        camp_das = "alwayson"
        if any(x in cid_low for x in ["holiday", "becalm", "steadystate", "bigcozy"]): camp_das = "Holiday"
        lvl_das = "upper-dm" if "upper" in cid_low else "middle-dm"
        return f"{camp_das}-{lvl_das}-prospecting-naverdas"

    # 6. 검색광고 (ps_) - keyword 필수
    if any(x in cid_low for x in ["ps_naver", "ps_google", "ps_daum"]):
        if not any(x in cid_low for x in ["prospecting-keyword", "retargeting-keyword"]): return "Unknown"
        if "keyword-generic" in cid_low:
            sub_gen = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
            return f"generic-middle-dm-pro-{sub_gen}"
        
        m_fin = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
        if "ps_google" in cid_low: m_fin = "google"
        elif "ps_daum" in cid_low: m_fin = "kakaomo" if any(x in cid_low for x in ["-mo-", "_mo"]) else "kakaopc"
        
        t_fin = "pro" if "ps_naver" in cid_low else ("retargeting" if "retargeting" in cid_low else "prospecting")
        c_fin = "product" if any(x in cid_low for x in ["product", "dailywear", "waterbottle"]) else ("activity" if "activity" in cid_low else "brand")
        l_fin = "middle-dm" if c_fin in ["product", "activity"] else "lower-dm"
        return f"{c_fin}-{l_fin}-{t_fin}-{m_fin}"

    # 7. 일반 캠페인 (Springstory 등)
    media = "google"
    if "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low: media = "kakaoda"
    elif any(x in cid_low for x in ["meta", "smp_fbig", "smp_ig"]): media = "meta"

    if any(x in cid_low for x in ["sn-spring2026-casualigc", "sn-spring2026-casualdbe"]): camp = "Springstory"
    elif any(x in cid_low for x in ["holiday", "becalm", "steadystate", "bigcozy"]): camp = "Holiday"
    else: camp = "alwayson"

    lvl = "lower-dm" if ("lower" in cid_low or "retargeting" in cid_low) else "middle-dm"
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    
    return f"{camp}-{lvl}-{target}-{media}"

# --- 화면 UI ---
st.title("🏃 룰루레몬 하이브리드 자동화 도구")

tab1, tab2 = st.tabs(["🎯 1단계: 어도비 검수", "📊 2단계: 데이터 통합"])

with tab1:
    st.header("어도비 이름표 달기 (Raw 데이터 업로드)")
    uploaded_file = st.file_uploader("어도비에서 다운로드한 CSV 파일을 올려주세요.", type="csv")
    
    if uploaded_file:
        # 어도비 특유의 설명글(Header) 건너뛰고 읽기
        content = uploaded_file.getvalue().decode('utf-8-sig').splitlines()
        data_start_idx = 0
        for i, line in enumerate(content):
            # '마케팅 채널 세부 사항' 또는 '방문 횟수'가 포함된 행이 실제 데이터 시작 직전임
            if "방문 횟수" in line and "," in line:
                data_start_idx = i
                break
        
        # 실제 데이터 로드
        df = pd.read_csv(io.StringIO("\n".join(content[data_start_idx:])))
        
        # 첫 번째 열이 CID(코드)이므로 이름 변경
        df.rename(columns={df.columns[0]: '코드'}, inplace=True)
        
        # 합계 행(두 번째 행) 제외하고 데이터만 추출
        df = df.iloc[1:].reset_index(drop=True)
        
        # AI 매핑 실행
        df['AI_제안명'] = df['코드'].apply(build_perfect_key_v5)
        
        st.subheader("🧐 매핑 결과 더블체크")
        only_unknown = st.checkbox("Unknown만 모아보기")
        display_df = df[df['AI_제안명'] == "Unknown"] if only_unknown else df
        
        st.dataframe(display_df[['코드', '방문 횟수', 'Revenue', 'AI_제안명']].head(500))
        
        # 결과 다운로드
        st.download_button(
            label="📥 1차 매핑 결과 다운로드",
            data=df.to_csv(index=False).encode('utf-8-sig'),
            file_name="adobe_1st_mapped_result.csv",
            mime="text/csv"
        )

with tab2:
    st.header("매체 데이터 통합")
    st.info("여기는 매체별 실적 파일(비용 등)을 올려서 어도비와 합치는 공간입니다 (구현 예정).")
