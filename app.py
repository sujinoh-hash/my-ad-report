import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="룰루레몬 자동화 도구 [v11]", layout="wide")

# --- [로직] 매핑 함수 ---
def build_perfect_key_final(cid):
    if pd.isna(cid) or str(cid).strip() == "": return "Unknown"
    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    if "navershopping" in cid_low: return "Naver shopping"
    if "dsp_kakao-kw" in cid_low: return "alwayson-upper-dm-pro-kakaotalksa"
    if any(x in cid_low for x in ["kakaopn", "kakao-opt-in", "welcomemessage", "pu_", "transactional"]):
        return "alwayson-lower-dm-kakaooptin-kakaopn"
    if "payco" in cid_low: return "alwayson-lower-dm-prospecting-payco"

    if "brandzone" in cid_low:
        if "brandzone-na" not in cid_low: return "Unknown"
        sub = "naverbsmo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverbspc"
        if "kakao" in cid_low: sub = sub.replace("naver", "kakao")
        return f"alwayson-BS-dm-pro-{sub}"

    if cid_low.startswith("ps_"):
        if "keyword-" not in cid_low: return "Unknown"
        m = "navermo" if any(x in cid_low for x in ["_mo", "-mo"]) else "naverpc"
        if "google" in cid_low: m = "google"
        elif "daum" in cid_low: m = "kakaomo" if "mo" in m else "kakaopc"
        f = "lower-dm" if "lower" in cid_low else "middle-dm"
        t = "retargeting" if "retargeting" in cid_low else "pro"
        c = "brand"
        if any(x in cid_low for x in ["product", "dailywear"]): c = "product"
        elif "activity" in cid_low: c = "activity"
        return f"{c}-{f}-{t}-{m}"

    if "criteo" in cid_low:
        if "prospecting-demo" in cid_low: return "alwayson-upper-dm-prospecting-criteo"
        if "lower" in cid_low: return "alwayson-lower-dm-retargeting-criteo"
        return "Unknown"

    media = "google"
    if "dsp_naver" in cid_low: media = "naverda"
    elif "dsp_kakao" in cid_low: media = "kakaoda"
    elif "meta" in cid_low or "smp_fbig" in cid_low: media = "meta"
    camp = "Springstory" if "spring2026" in cid_low else "alwayson"
    return f"{camp}-upper-dm-prospecting-{media}"

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

# --- UI ---
st.title("🏃 룰루레몬 하이브리드 자동화 도구 [v11]")
tab1, tab2 = st.tabs(["🎯 1단계: 어도비 검수", "📊 2단계: 데이터 통합"])

with tab1:
    st.header("어도비 데이터 통합 검수")
    files = st.file_uploader("어도비 CSV 파일들을 드래그하세요.", type="csv", accept_multiple_files=True, key="tab1_uploader")
    if files:
        all_dfs = []
        for f in files:
            content = f.getvalue().decode('utf-8-sig').splitlines()
            file_date = get_date_final(content, f.name)
            idx = 0
            for i, line in enumerate(content):
                if "방문 횟수" in line:
                    idx = i
                    break
            df = pd.read_csv(io.StringIO("\n".join(content[idx:])))
            df.rename(columns={df.columns[0]: '코드'}, inplace=True)
            df = df.iloc[1:].reset_index(drop=True)
            df.insert(0, '날짜', file_date)
            all_dfs.append(df)
        
        full_adobe = pd.concat(all_dfs, ignore_index=True)
        full_adobe['AI_제안명'] = full_adobe['코드'].apply(build_perfect_key_final)
        
        cols = ['날짜', '코드', '방문 횟수', 'Cart Adds', 'Orders', 'Revenue', 'AI_제안명']
        existing_cols = [c for c in cols if c in full_adobe.columns]
        
        st.subheader("🧐 검수용 실적 테이블 (모든 지표 포함)")
        st.dataframe(full_adobe[existing_cols].head(1000))
        st.download_button("📥 검수 완료 파일 다운로드", full_adobe.to_csv(index=False).encode('utf-8-sig'), "adobe_checked.csv")

with tab2:
    st.header("📊 데이터 최종 통합 리포트")
    c1, c2 = st.columns(2)
    with c1:
        adobe_file = st.file_uploader("1. 검수 완료된 어도비 파일 업로드", type="csv", key="tab2_adobe")
    with c2:
        media_files = st.file_uploader("2. 매체 실적 파일들 업로드", type=["csv", "xlsx"], accept_multiple_files=True, key="tab2_media")
    
    if adobe_file and media_files:
        df_a = pd.read_csv(adobe_file)
        all_media_list = []
        
        for mf in media_files:
            df_m = pd.read_excel(mf) if mf.name.endswith('xlsx') else pd.read_csv(mf)
            
            # 지표 표준화
            rename_map = {'일':'일','Day':'일','일자':'일','일별':'일','날짜':'일','캠페인 이름':'캠페인명','Campaign':'캠페인명','메시지명':'캠페인명','광고상품':'캠페인명',
                          '노출수':'노출','노출':'노출','Displays':'노출','클릭수':'클릭','Clicks':'클릭','비용':'광고비','지출 금액 (KRW)':'광고비','Cost':'광고비','집행금액':'광고비','결제 금액':'광고비',
                          '친구 추가수(7일)':'채널친구수','전환수':'채널친구수','집행 전환수':'채널친구수'}
            df_m.rename(columns=rename_map, inplace=True)
            
            # 고정값 처리 (카카오 메시지, CPK, 쇼핑파트너)
            if "메시지" in mf.name or "msg" in str(df_m.columns).lower():
                df_m['캠페인명'] = "alwayson-lower-dm-kakaooptin-kakaopn"
            if "cpk" in mf.name.lower():
                df_m['캠페인명'] = "Kakao Offerwall"
            if "쇼핑파트너" in mf.name or "결제 금액" in df_m.columns:
                df_m['캠페인명'] = "쇼핑파트너센터"
                df_m['광고비'] = df_m['광고비'].apply(lambda x: abs(float(str(x).replace(',',''))) if pd.notna(x) else 0)
            
            # kakaopn 노출 = 열람수 보정
            if '열람수' in df_m.columns:
                df_m.loc[df_m['캠페인명'].str.contains('kakaopn', na=False), '노출'] = df_m['열람수']
            
            # 필요 열만 선택해서 리스트에 추가
            target_cols = ['일', '캠페인명', '노출', '클릭', '광고비']
            if '채널친구수' in df_m.columns: target_cols.append('채널친구수')
            all_media_list.append(df_m[[c for c in target_cols if c in df_m.columns]])

        # 매체 데이터 합치기
        df_m_total = pd.concat(all_media_list).groupby(['일', '캠페인명']).sum().reset_index()
        
        if st.button("🚀 매체 + 어도비 최종 통합 실행"):
            df_a_sum = df_a.groupby(['날짜', 'AI_제안명']).agg({'방문 횟수':'sum','Cart Adds':'sum','Orders':'sum','Revenue':'sum'}).reset_index()
            final = pd.merge(df_m_total, df_a_sum, left_on=['일', '캠페인명'], right_on=['날짜', 'AI_제안명'], how='outer')
            st.success("통합이 완료되었습니다!")
            st.dataframe(final.head(1000))
            st.download_button("📥 최종 통합 리포트 다운로드", final.to_csv(index=False).encode('utf-8-sig'), "final_report.csv")
