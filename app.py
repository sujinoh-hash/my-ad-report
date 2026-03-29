import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="룰루레몬 자동화 도구", layout="wide")

# --- [로직] v5 매핑 함수 (내용은 동일) ---
def build_perfect_key_v5(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()
    
    # [1] 고정 매칭
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"
    if "payco" in cid_low: return "alwayson-lower-dm-prospecting-payco"
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"
    
    # [2] 네이버/브랜드검색/쇼핑
    if "navershopping" in cid_low: return "Naver shopping"
    if "brandzone" in cid_low:
        if "brandzone-na" not in cid_low: return "Unknown"
        sub = ("naverbsmo" if "naver" in cid_low else "kakaobsmo") if any(x in cid_low for x in ["_mo", "-mo"]) else ("naverbspc" if "naver" in cid_low else "kakaobspc")
        return f"alwayson-BS-dm-pro-{sub}"
        
    # [3] 크리테오
    if "criteo" in cid_low:
        if "dsp_criteo" in cid_low and ("w_prospecting-demo-women" in cid_low or "m_prospecting-demo-men" in cid_low):
            return "alwayson-upper-dm-prospecting-criteo"
        if "lower" not in cid_low: return "Unknown"
        return "alwayson-lower-dm-retargeting-criteo"

    # [4] 네이버 스페셜 DA
    if "dsp_naver" in cid_low and "prospecting-demo-all" in cid_low:
        camp_das = "alwayson"
        if any(x in cid_low for x in ["holiday", "becalm", "steadystate", "bigcozy"]): camp_das = "Holiday"
        lvl_das = "upper-dm" if "upper" in cid_low else "middle-dm"
        return f"{camp_das}-{lvl_das}-prospecting-naverdas"

    # [5] 검색광고
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

    # [6] 기타
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

tab1, tab2 = st.tabs(["🎯 1단계: 어도비 통합 검수", "📊 2단계: 데이터 통합"])

with tab1:
    st.header("어도비 Raw 데이터 일괄 업로드 (최대 20개 가능)")
    # accept_multiple_files=True 옵션으로 여러 파일 선택 가능하게 함
    uploaded_files = st.file_uploader("어도비 CSV 파일들을 드래그해서 놓으세요.", type="csv", accept_multiple_files=True)
    
    if uploaded_files:
        all_dfs = []
        for uploaded_file in uploaded_files:
            # 1. 파일별 날짜 정보 추출 (파일명에서 가져오거나 본문에서 추출)
            content = uploaded_file.getvalue().decode('utf-8-sig').splitlines()
            
            # 파일 상단 날짜 정보 찾기 (예: # 날짜:2026년 3월 16일)
            file_date = "날짜미상"
            data_start_idx = 0
            for i, line in enumerate(content):
                if "# 날짜:" in line:
                    file_date = line.split(":")[-1].strip()
                if "방문 횟수" in line and "," in line:
                    data_start_idx = i
                    break
            
            # 2. 데이터 로드
            temp_df = pd.read_csv(io.StringIO("\n".join(content[data_start_idx:])))
            temp_df.rename(columns={temp_df.columns[0]: '코드'}, inplace=True)
            temp_df = temp_df.iloc[1:].reset_index(drop=True) # 합계행 제외
            
            # 날짜 열이 없으면 파일에서 찾은 날짜 삽입
            if '날짜' not in temp_df.columns:
                temp_df.insert(0, '날짜', file_date)
            
            all_dfs.append(temp_df)
        
        # 3. 모든 파일 하나로 합치기
        full_df = pd.concat(all_dfs, ignore_index=True)
        
        # 4. AI 매핑 실행
        full_df['AI_제안명'] = full_df['코드'].apply(build_perfect_key_v5)
        
        # 5. 화면 표시 (사용자 요청: 날짜, 카트수, 주문수 포함)
        st.subheader(f"🧐 총 {len(full_df)}건의 데이터 통합 검수")
        
        # 표시할 컬럼 정리 (존재하는 컬럼만 선택)
        cols_to_show = ['날짜', '코드', '방문 횟수', 'Cart Adds', 'Orders', 'Revenue', 'AI_제안명']
        existing_cols = [c for c in cols_to_show if c in full_df.columns]
        
        only_unknown = st.checkbox("Unknown만 모아보기")
        display_df = full_df[full_df['AI_제안명'] == "Unknown"] if only_unknown else full_df
        
        st.dataframe(display_df[existing_cols].head(1000))
        
        # 6. 결과 다운로드
        st.download_button(
            label="📥 통합 매핑 결과 다운로드",
            data=full_df.to_csv(index=False).encode('utf-8-sig'),
            file_name="adobe_merged_check.csv",
            mime="text/csv"
        )
