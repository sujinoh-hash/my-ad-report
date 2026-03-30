import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="룰루레몬 자동화 도구 [v14]", layout="wide")

# --- [로직] 1단계: 모든 히스토리 규칙이 반영된 매핑 함수 ---
def build_perfect_key_final(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    # 1. 고정값 및 네이버 쇼핑 (통합)
    if "navershopping" in cid_low: return "Naver shopping"
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"
    if "payco" in cid_low: return "alwayson-lower-dm-prospecting-payco"
    
    # 2. 카카오 옵트인 (kakaopn / transactional 구분)
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        suffix = "transactional" if any(x in cid_low for x in ["pu_", "transactional"]) else "kakaopn"
        return f"alwayson-lower-dm-kakaooptin-{suffix}"

    # 3. 브랜드검색 (Strict: brandzone-na 필수)
    if "brandzone" in cid_low:
        if "brandzone-na" not in cid_low: return "Unknown"
        sub = ("naverbsmo" if "naver" in cid_low else "kakaobsmo") if any(x in cid_low for x in ["_mo", "-mo"]) else ("naverbspc" if "naver" in cid_low else "kakaobspc")
        return f"alwayson-BS-dm-pro-{sub}"

    # 4. PMAX 상세 구분 (W, M, C) - [복구!]
    if "pmax" in cid_low:
        if "w_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxW"
        if "m_prospecting-demo" in cid_low: return "alwayson-middle-dm-prospecting-pmaxM"
        return "alwayson-middle-dm-prospecting-pmaxC"

    # 5. 검색광고 (Strict: ps_ + keyword- 필수)
    if cid_low.startswith("ps_"):
        if "keyword-" not in cid_low: return "Unknown"
        m = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
        if "google" in cid_low: m = "google"
        elif "daum" in cid_low: m = "kakaomo" if "mo" in m else "kakaopc"
        f = "lower-dm" if "lower" in cid_low else "middle-dm"
        t = "retargeting" if "retargeting" in cid_low else "pro"
        c = "brand"
        if any(x in cid_low for x in ["product", "dailywear", "waterbottle"]): c = "product"
        elif "activity" in cid_low: c = "activity"
        return f"{c}-{f}-{t}-{m}"

    # 6. 크리테오 상세 (Prospecting vs Retargeting)
    if "criteo" in cid_low:
        if "dsp_criteo" in cid_low and ("w_prospecting-demo-women" in cid_low or "m_prospecting-demo-men" in cid_low):
            return "alwayson-upper-dm-prospecting-criteo"
        if "lower" not in cid_low: return "Unknown"
        return "alwayson-lower-dm-retargeting-criteo"

    # 7. 매체 판별 (YouTube 복구)
    media = "google"
    if "dsp_yt" in cid_low: media = "YouTube"
    elif "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low:
        media = "kakaodaD" if "_pcmo" in cid_low else "kakaoda"
        if "catalog" in cid_low: media = "kakaodaC"
    elif any(x in cid_low for x in ["meta", "smp_fbig", "smp_ig"]):
        media = "metaC" if "catalog" in cid_low else "meta"
        if "prospecting-na-na" in cid_low: media = "metam3"

    # 8. 캠페인 카테고리 판별 (Run, Train, Pants, Springstory 등)
    if any(x in cid_low for x in ["sn-spring2026-casualigc", "sn-spring2026-casualdbe"]): camp = "Springstory"
    elif any(x in cid_low for x in ["holiday", "becalm", "steadystate", "bigcozy"]): camp = "Holiday"
    elif any(x in cid_low for x in ["runnigstorekw", "logorun", "yet-spring2026-run"]): camp = "Run"
    elif "train-winter2025" in cid_low: camp = "Train"
    elif "bottoms-spring2026-otm" in cid_low: camp = "Pants"
    else: camp = "alwayson"

    # 9. 퍼널 조립
    lvl = "lower-dm" if ("lower" in cid_low or "retargeting" in cid_low) else ("upper-dm" if "prospecting" in cid_low else "middle-dm")
    target = "retargeting" if "retargeting" in cid_low else "prospecting"
    
    return f"{camp}-{lvl}-{target}-{media}"

# --- 데이터 처리 및 UI (1/2단계 통합) ---
def get_date_final(content, filename):
    for line in content:
        if "# 날짜:" in line:
            nums = re.findall(r'\d+', line)
            if len(nums) >= 3: return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
    file_nums = re.findall(r'\d{6}', filename)
    if file_nums:
        d = file_nums[0]
        return f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
    return datetime.now().strftime("%Y-%m-%d")

tab1, tab2 = st.tabs(["🎯 1단계: 어도비 검수", "📊 2단계: 데이터 통합"])

with tab1:
    st.header("어도비 통합 검수 (모든 지표 포함)")
    files = st.file_uploader("어도비 CSV 파일들을 드래그하세요.", type="csv", accept_multiple_files=True, key="t1")
    if files:
        all_dfs = []
        for f in files:
            content = f.getvalue().decode('utf-8-sig').splitlines()
            file_date = get_date_final(content, f.name)
            idx = 0
            for i, line in enumerate(content):
                if "방문 횟수" in line: idx = i; break
            df = pd.read_csv(io.StringIO("\n".join(content[idx:])))
            df.rename(columns={df.columns[0]: '코드'}, inplace=True)
            df = df.iloc[1:].reset_index(drop=True)
            df.insert(0, '날짜', file_date)
            all_dfs.append(df)
        full_adobe = pd.concat(all_dfs, ignore_index=True)
        full_adobe['AI_제안명'] = full_adobe['코드'].apply(build_perfect_key_final)
        cols = ['날짜', '코드', '방문 횟수', 'Cart Adds', 'Orders', 'Revenue', 'AI_제안명']
        st.dataframe(full_adobe[[c for c in cols if c in full_adobe.columns]].head(1000))
        st.download_button("📥 검수 완료 파일 다운로드", full_adobe.to_csv(index=False).encode('utf-8-sig'), "adobe_checked.csv")

with tab2:
    st.header("📊 데이터 최종 통합 리포트")
    c1, c2 = st.columns(2)
    with c1: adobe_in = st.file_uploader("1. 검수된 어도비 파일", type="csv", key="t2a")
    with c2: media_ins = st.file_uploader("2. 매체 Raw 파일들", type=["csv", "xlsx"], accept_multiple_files=True, key="t2m")
    if adobe_in and media_ins:
        df_a = pd.read_csv(adobe_in)
        all_m = []
        for mf in media_ins:
            df_m = pd.read_excel(mf) if mf.name.endswith('xlsx') else pd.read_csv(mf)
            # 지표 표준화 (노출, 클릭, 광고비, 채널친구수)
            ren = {'일':'일','Day':'일','일자':'일','일별':'일','날짜':'일','캠페인 이름':'캠페인명','Campaign':'캠페인명','메시지명':'캠페인명','광고상품':'캠페인명','AD Type':'캠페인명','최종광고비':'광고비','결제 금액':'광고비','노출수':'노출','노출':'노출','Displays':'노출','클릭수':'클릭','Clicks':'클릭','지출 금액 (KRW)':'광고비','Cost':'광고비','집행금액':'광고비','친구 추가수(7일)':'채널친구수','전환수':'채널친구수','집행 전환수':'채널친구수','친구 추가 수 (7일) ':'채널친구수'}
            df_m.rename(columns=ren, inplace=True)
            
            # 고정값 처리
            if "메시지" in mf.name: df_m['캠페인명'] = "alwayson-lower-dm-kakaooptin-kakaopn"
            if "cpk" in mf.name.lower(): df_m['캠페인명'] = "Kakao Offerwall"
            if "쇼핑파트너" in mf.name or "결제 금액" in df_m.columns:
                df_m['캠페인명'] = "쇼핑파트너센터"
                df_m['광고비'] = df_m['광고비'].apply(lambda x: abs(float(str(x).replace(',',''))) if pd.notna(x) else 0)
                df_m['노출'], df_m['클릭'] = 0, 0
            
            # kakaopn 지표 보정 (노출=열람수)
            if '열람수' in df_m.columns:
                df_m.loc[df_m['캠페인명'].str.contains('kakaopn', na=False), '노출'] = df_m['열람수']
            
            # 네이버 쇼핑 통합
            df_m['캠페인명'] = df_m['캠페인명'].replace(['navershopping_w', 'navershopping_m'], 'Naver shopping')
            
            # 숫자 데이터로 변환 (컴마 제거 등)
            for c in ['노출', '클릭', '광고비', '채널친구수']:
                if c in df_m.columns:
                    df_m[c] = pd.to_numeric(df_m[c].astype(str).str.replace(',',''), errors='coerce').fillna(0)
            
            all_m.append(df_m)
        
        df_m_total = pd.concat(all_m).groupby(['일', '캠페인명']).sum(numeric_only=True).reset_index()
        
        if st.button("🚀 최종 통합 실행"):
            # 어도비 요약 (방문, 카트, 주문, 매출)
            df_a_sum = df_a.groupby(['날짜', 'AI_제안명']).agg({'방문 횟수':'sum','Cart Adds':'sum','Orders':'sum','Revenue':'sum'}).reset_index()
            # 최종 병합
            final = pd.merge(df_m_total, df_a_sum, left_on=['일', '캠페인명'], right_on=['날짜', 'AI_제안명'], how='outer')
            # 날짜 정렬
            final['일'] = final['일'].fillna(final['날짜'])
            final['캠페인명'] = final['캠페인명'].fillna(final['AI_제안명'])
            final = final.drop(columns=['날짜', 'AI_제안명']).sort_values(['일', '캠페인명'])
            
            st.success("데이터 통합 완료!")
            st.dataframe(final.head(1000))
            st.download_button("📥 최종 리포트 다운로드", final.to_csv(index=False).encode('utf-8-sig'), "lululemon_final_report.csv")
