import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="룰루레몬 자동화 도구 [v21]", layout="wide")

# ────────────────────────────────────────────────────────────
# 캠페인키 매핑
# ────────────────────────────────────────────────────────────
CAMPAIGN_KEY_MAP = {
    "alwayson-na-na":           "alwayson-na-na",
    "play-spring2026-golf":     "play-spring2026-golf",
    "yet-spring2026-run":       "yet-spring2026-run",
    "sn-spring2026-casualdbe":  "sn-spring2026-casual",
    "sn-spring2026-casualigc":  "sn-spring2026-casual",
    "bottoms-spring2026-otm":   "bottoms-spring2026-otm",
    "men-2026-alwayson":        "men-2026-alwayson",
}

def normalize_campaign_key(key: str) -> str:
    """
    {season}-{year}-alwayson → na-{year}-alwayson
    나머지는 CAMPAIGN_KEY_MAP 참조, 없으면 그대로
    """
    if not key:
        return key
    m = re.match(r"^(spring|winter|summer|fall)-(\d{4})-alwayson$", key)
    if m:
        return f"na-{m.group(2)}-alwayson"
    return CAMPAIGN_KEY_MAP.get(key, key)


def get_funnel(seg7: str, naver: bool = False) -> str:
    """
    [7]번 세그먼트에서 prospecting/retargeting 판별
    네이버는 글자수 제한으로 pro/re 사용
    """
    is_ret = seg7.startswith("retargeting")
    if naver:
        return "re" if is_ret else "pro"
    return "retargeting" if is_ret else "prospecting"


# ────────────────────────────────────────────────────────────
# 메인 파싱 함수
# ────────────────────────────────────────────────────────────
def build_campaign_key_v21(cid: str) -> str:
    if pd.isna(cid) or str(cid).strip() == "":
        return "Unknown"

    raw = str(cid).strip()
    low = raw.lower()
    parts = raw.split("_")
    prefix = parts[0].lower()

    # ── Unknown 필터 ──────────────────────────────────────────
    if "_adef-" in low:                                  return "Unknown"  # 구버전 코드
    if "_br_" in low:                                    return "Unknown"  # 브랜딩 캠페인
    if re.search(r"\.(com|instagram|youtube|facebook)", low): return "Unknown"  # 도메인

    # ── sms_ : SMS 옵트인 ─────────────────────────────────────
    if prefix == "sms":
        return "dm-smsoptin-smspn-alwayson-na-na"

    # ── pu_ : 카카오 트랜잭셔널 ──────────────────────────────
    if prefix == "pu":
        return "dm-kakaooptin-kakaotransactional-alwayson-na-na"

    # ── smp_ ──────────────────────────────────────────────────
    if prefix == "smp":
        medium = parts[1].lower() if len(parts) > 1 else ""

        if medium == "ig":
            return "Unknown"  # 구버전

        if "wc10" in low:
            return "dm-kakaooptin-kakaotransactional-alwayson-na-na"

        if medium == "kakao":
            seg6 = parts[6].lower() if len(parts) > 6 else ""
            if seg6 in ["tx", "all"] and "transactional" in low:
                return "dm-kakaooptin-kakaotransactional-alwayson-na-na"
            seg7 = parts[7].lower() if len(parts) > 7 else ""
            if "kakao-opt-in" in seg7 or "welcomemessage" in low:
                c_key = normalize_campaign_key(parts[8]) if len(parts) > 8 else "alwayson-na-na"
                return f"dm-kakaooptin-kakaopn-{c_key}"
            return "Unknown"

        if medium in ["fbig", "meta"]:
            seg7 = parts[7].lower() if len(parts) > 7 else ""
            funnel = get_funnel(seg7)
            c_key = normalize_campaign_key(parts[8]) if len(parts) > 8 else "alwayson-na-na"
            fmt = "catalog" if "catalog" in low else "fbig"
            return f"dm-{funnel}-{fmt}-{c_key}"

        return "Unknown"

    # ── ps_ ───────────────────────────────────────────────────
    if prefix == "ps":
        medium = parts[1].lower() if len(parts) > 1 else ""

        # 네이버쇼핑
        if "navershopping" in medium:
            return "dm-pro-shopping-alwayson-n-n"

        # 네이버/카카오(다음) 브랜드검색 → 캠페인키 alwayson-n-n 고정
        if "naver-brandzone" in medium or "daum-brandzone" in medium:
            seg7 = parts[7].lower() if len(parts) > 7 else ""
            if not (seg7.startswith("prospecting") or seg7.startswith("retargeting")):
                return "Unknown"
            device_seg = parts[9].lower() if len(parts) > 9 else ""
            if "daum" in medium:
                device = "kakaobsmo" if device_seg.startswith("mo") else "kakaobspc"
            else:
                device = "naverbsmo" if device_seg.startswith("mo") else "naverbspc"
            return f"dm-pro-{device}-alwayson-n-n"

        # 네이버 SA / 다음 SA
        if medium in ["naver", "daum"] or (
            medium.startswith("naver") and "shopping" not in medium and "brandzone" not in medium
        ):
            seg7 = parts[7].lower() if len(parts) > 7 else ""
            if not (seg7.startswith("prospecting") or seg7.startswith("retargeting")):
                return "Unknown"
            # 다음(카카오) SA는 prospecting/retargeting 그대로, 네이버만 pro/re 축약
            if medium == "daum":
                funnel = get_funnel(seg7)
                device_seg = parts[9].lower() if len(parts) > 9 else ""
                device = "kakaomo" if device_seg.startswith("mo") else "kakaopc"
            else:
                funnel = get_funnel(seg7, naver=True)
                device_seg = parts[9].lower() if len(parts) > 9 else ""
                device = "navermo" if device_seg.startswith("mo") else "naverpc"
            if   "keyword-generic"  in seg7: cat = "generic"
            elif "keyword-activity" in seg7: cat = "Activity"
            elif "keyword-brand"    in seg7: cat = "brand"
            elif "keyword-product"  in seg7: cat = "product"
            else:                            cat = "brand"
            return f"dm-{funnel}-{device}-{cat}-na-na"

        # 구글 SA
        if medium == "google":
            seg7 = parts[7].lower() if len(parts) > 7 else ""
            if not (seg7.startswith("prospecting") or seg7.startswith("retargeting")):
                return "Unknown"
            funnel = get_funnel(seg7)
            if   "keyword-generic"  in seg7: cat = "generic"
            elif "keyword-activity" in seg7: cat = "Activity"
            elif "keyword-brand"    in seg7: cat = "brand"
            elif "keyword-product"  in seg7: cat = "product"
            else:                            cat = "brand"
            return f"dm-{funnel}-googlepcmo-{cat}-na-na"

        return "Unknown"

    # ── dsp_ ──────────────────────────────────────────────────
    if prefix == "dsp":
        medium  = parts[1].lower() if len(parts) > 1 else ""
        seg7    = parts[7].lower() if len(parts) > 7 else ""
        raw_key = parts[8] if len(parts) > 8 else ""
        c_key   = normalize_campaign_key(raw_key)
        dev_seg = parts[9].lower() if len(parts) > 9 else ""

        # DA 캠페인키 유효성 검사 (카탈로그 제외한 DA 매체는 캠페인키가 반드시 3파트)
        def is_valid_da_key(key: str) -> bool:
            return len(key.split("-")) >= 3

        # 구글 PMAX
        if medium == "google":
            if not seg7.startswith("prospecting"): return "Unknown"
            if   "demo-women" in seg7: pmax = "PmaxW"
            elif "demo-men"   in seg7: pmax = "PmaxM"
            else:                      pmax = "PmaxC"
            return f"dm-prospecting-{pmax}-alwayson-na-na"

        # 유튜브
        if medium == "yt":
            return f"dm-{get_funnel(seg7)}-Youtube-alwayson-na-na"

        # 크리테오
        if medium == "criteo":
            return f"dm-{get_funnel(seg7)}-criteo-alwayson-na-na"

        # 카카오 키워드 광고 (kakao-kw) → 캠페인키 alwayson-na-na 고정
        if medium == "kakao-kw":
            return f"dm-{get_funnel(seg7)}-kakaokw-brand-alwayson-na-na"

        # 네이버 GFA / gfacatalog
        if medium == "naver":
            funnel = get_funnel(seg7)  # 1번: GFA는 prospecting/retargeting 그대로
            if "catalog" in low:
                return f"dm-{funnel}-gfacatalog-alwayson-na-na"
            if not is_valid_da_key(c_key): return "Unknown"
            return f"dm-{funnel}-GFA-{c_key}"

        # 카카오 DA
        if medium == "kakao":
            funnel = get_funnel(seg7)
            if "catalog" in low:
                return f"dm-{funnel}-kakaocatalog-alwayson-na-na"
            if not is_valid_da_key(c_key): return "Unknown"
            if dev_seg.startswith("mo-"): fmt = "bizboard"
            else:                         fmt = "display"
            return f"dm-{funnel}-{fmt}-{c_key}"

        # 메타 DA
        if medium in ["fbig", "meta"]:
            funnel = get_funnel(seg7)
            if "catalog" in low:
                return f"dm-{funnel}-fbigcatalog-alwayson-na-na"
            if not is_valid_da_key(c_key): return "Unknown"
            return f"dm-{funnel}-fbig-{c_key}"

        # 크림 DA
        if medium == "kream":
            funnel = get_funnel(seg7)
            if not is_valid_da_key(c_key): return "Unknown"
            return f"dm-{funnel}-Kream-{c_key}"

        # 페이코
        if medium == "payco":
            return "dm-prospecting-payco-alwayson-na-na"

        return "Unknown"

    return "Unknown"


# ────────────────────────────────────────────────────────────
# 날짜 추출
# ────────────────────────────────────────────────────────────
def get_date_final(content, filename):
    for line in content:
        if "# 날짜:" in line:
            nums = re.findall(r"\d+", line)
            if len(nums) >= 3:
                return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
    file_nums = re.findall(r"\d{6}", filename)
    if file_nums:
        d = file_nums[0]
        return f"20{d[0:2]}-{d[2:4]}-{d[4:6]}"
    return datetime.now().strftime("%Y-%m-%d")


# ────────────────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 1단계: 어도비 검수", "📊 2단계: 매체 Raw 정제", "📈 3단계: GA4 검수"])

with tab1:
    st.header("어도비 통합 검수 [v21]")
    files = st.file_uploader(
        "어도비 CSV 파일들을 드래그하세요.",
        type="csv", accept_multiple_files=True, key="t1"
    )
    if files:
        all_dfs = []
        for f in files:
            content = f.getvalue().decode("utf-8-sig").splitlines()
            file_date = get_date_final(content, f.name)
            idx = 0
            for i, line in enumerate(content):
                if "방문 횟수" in line:
                    idx = i
                    break
            df = pd.read_csv(io.StringIO("\n".join(content[idx:])))
            df.rename(columns={df.columns[0]: "코드"}, inplace=True)
            df = df.iloc[1:].reset_index(drop=True)
            df.insert(0, "날짜", file_date)
            all_dfs.append(df)

        full_adobe = pd.concat(all_dfs, ignore_index=True)
        full_adobe["AI_제안명"] = full_adobe["코드"].apply(build_campaign_key_v21)

        total = len(full_adobe)
        unk = (full_adobe["AI_제안명"] == "Unknown").sum()
        st.info(f"✅ 총 {total}행 | ⚠️ Unknown: {unk}행 ({unk/total*100:.1f}%)")

        cols = ["날짜", "코드", "방문 횟수", "Cart Adds", "Orders", "Revenue", "AI_제안명"]
        st.subheader("전체 결과")
        st.dataframe(full_adobe[[c for c in cols if c in full_adobe.columns]].head(1000))

        unknown_df = full_adobe[full_adobe["AI_제안명"] == "Unknown"]
        if len(unknown_df) > 0:
            st.subheader("⚠️ Unknown 목록")
            st.dataframe(unknown_df[["코드", "AI_제안명"]].head(200))

        st.download_button(
            "📥 검수 완료 다운로드",
            full_adobe.to_csv(index=False).encode("utf-8-sig"),
            "adobe_checked_v21.csv",
        )

with tab2:
    st.header("📊 매체 Raw 데이터 정제")
    media_ins = st.file_uploader(
        "매체 Raw 파일들을 드래그하세요.",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        key="t2m",
    )

    if media_ins:
        all_m = []
        for mf in media_ins:
            fname = mf.name
            fname_low = fname.lower()
            df_m = None

            # ── 파일 읽기 ──────────────────────────────────────
            if fname.endswith("xlsx"):
                df_m = pd.read_excel(mf)

            # 카카오DA 보고서 (utf-16 탭구분)
            elif "보고서" in fname and "메시지" not in fname:
                try:
                    raw = mf.read()
                    df_m = pd.read_csv(io.StringIO(raw.decode("utf-16")), sep="\t")
                except Exception:
                    st.error(f"❌ {fname} 파일을 읽을 수 없어요.")
                    continue

            # 쇼핑파트너 거래내역 (euc-kr)
            elif "거래내역" in fname:
                try:
                    raw = mf.read()
                    df_m = pd.read_csv(io.StringIO(raw.decode("euc-kr")))
                except Exception:
                    st.error(f"❌ {fname} 파일을 읽을 수 없어요.")
                    continue

            # 일반 CSV (인코딩 자동 감지)
            else:
                raw = mf.read()
                for enc in ["utf-8-sig", "utf-16", "euc-kr", "cp949", "utf-8"]:
                    try:
                        df_m = pd.read_csv(io.StringIO(raw.decode(enc)))
                        break
                    except Exception:
                        continue
                else:
                    st.error(f"❌ {fname} 파일 인코딩을 읽을 수 없어요.")
                    continue

            # ── 파일명 기반 특수 처리 (rename 전) ───────────────

            # 카카오 브랜드검색 (total_report_mo / total_report_pc)
            if "total_report" in fname_low:
                device = "kakaobsmo" if "_mo" in fname_low else "kakaobspc"
                df_m.rename(columns={"기간": "일", "노출수": "노출", "클릭수": "클릭"}, inplace=True)
                df_m["캠페인명"] = f"dm-pro-{device}-alwayson-n-n"
                df_m["광고비"] = 0

            # 카카오SA 애틀란티카 (시작일 → 일, 캠페인 → 캠페인명)
            elif "애틀라티카" in fname or "맞춤보고서" in fname_low:
                raw2 = open(base + fname, 'rb').read() if False else raw  # 이미 읽음
                df_m = pd.read_csv(io.StringIO(raw.decode("utf-8-sig")))
                df_m.rename(columns={
                    "시작일": "일", "캠페인": "캠페인명",
                    "노출수": "노출", "클릭수": "클릭", "비용": "광고비",
                    "친구 추가수(7일)": "채널친구수"
                }, inplace=True)

            # 네이버SA (일별, 캠페인, 총비용 컬럼)
            elif "daily_report_adef" in fname_low and "보고서" not in fname:
                df_m = pd.read_csv(io.StringIO(raw.decode("utf-8-sig")), header=1)
                df_m.rename(columns={
                    "일별": "일", "캠페인": "캠페인명",
                    "노출수": "노출", "클릭수": "클릭", "총비용": "광고비"
                }, inplace=True)

            # 카카오DA 보고서
            elif "보고서" in fname and "메시지" not in fname:
                df_m.rename(columns={"캠페인 이름": "캠페인명", "노출수": "노출", "클릭수": "클릭", "비용": "광고비"}, inplace=True)
                df_m["캠페인명"] = "Unknown"  # _br_ 포함된 캠페인명이므로 Unknown

            # 쇼핑파트너 거래내역
            elif "거래내역" in fname:
                df_m.rename(columns={"결제금액(유상+무상)": "광고비"}, inplace=True)
                df_m["캠페인명"] = "쇼핑파트너센터"
                df_m["광고비"] = df_m["광고비"].apply(
                    lambda x: abs(float(str(x).replace(",", "").replace("-", "0"))) if pd.notna(x) else 0
                )
                df_m["노출"], df_m["클릭"] = 0, 0

            # 메시지보고서 (카카오 트랜잭셔널)
            elif "메시지" in fname:
                df_m.rename(columns={"비용": "광고비", "열람수": "노출", "클릭수": "클릭"}, inplace=True)
                df_m["캠페인명"] = "dm-kakaooptin-kakaotransactional-alwayson-na-na"

            # 일반 rename
            else:
                ren = {
                    "일": "일", "Day": "일", "일자": "일", "일별": "일", "날짜": "일",
                    "캠페인 이름": "캠페인명", "Campaign": "캠페인명", "메시지명": "캠페인명",
                    "광고상품": "캠페인명", "최종광고비": "광고비", "결제 금액": "광고비",
                    "노출수": "노출", "노출": "노출", "Displays": "노출",
                    "클릭수": "클릭", "Clicks": "클릭", "클릭(전체)": "클릭",
                    "지출 금액 (KRW)": "광고비", "Cost": "광고비", "집행금액": "광고비",
                    "친구 추가수(7일)": "채널친구수", "전환수": "채널친구수",
                    "집행 전환수": "채널친구수", "친구 추가 수 (7일) ": "채널친구수",
                    "잠재 고객": "채널친구수", "캠페인": "캠페인명",
                    "디스플레이 수": "노출", "클릭 수": "클릭", "비용": "광고비",
                }
                df_m.rename(columns=ren, inplace=True)

                # cpk
                if "cpk" in fname_low:
                    df_m["캠페인명"] = "Kakao Offerwall"

            # ── kakaopn 열람수 → 노출수 ──────────────────────────
            if "열람수" in df_m.columns and "캠페인명" in df_m.columns:
                df_m.loc[df_m["캠페인명"].str.contains("kakaopn", na=False), "노출"] = df_m["열람수"]

            # ── 수치 콤마 제거 및 숫자 변환 ──────────────────────
            for col in ["노출", "클릭", "광고비", "채널친구수"]:
                if col in df_m.columns:
                    df_m[col] = pd.to_numeric(
                        df_m[col].astype(str).str.replace(",", "").str.strip(), errors="coerce"
                    ).fillna(0)

            # ── 날짜 컬럼 통일 (YYYY-MM-DD) ──────────────────────
            date_col = "일" if "일" in df_m.columns else None
            if date_col:
                df_m[date_col] = pd.to_datetime(
                    df_m[date_col].astype(str).str.strip()
                    .str.replace(r"\.\s*", "-", regex=True)  # 2026. 04. 14. → 2026-04-14
                    .str.rstrip("-"),
                    errors="coerce"
                ).dt.strftime("%Y-%m-%d")
                df_m.rename(columns={date_col: "일"}, inplace=True)

            # ── Total 행 제거 ─────────────────────────────────────
            if "일" in df_m.columns:
                df_m = df_m[df_m["일"] != "Total"]
                df_m = df_m[df_m["일"].notna()]

            # ── 필요한 컬럼만 남기기 ──────────────────────────────
            keep_cols = ["일", "캠페인명", "노출", "클릭", "광고비", "채널친구수"]
            df_m = df_m[[c for c in keep_cols if c in df_m.columns]]

            if len(df_m) > 0:
                all_m.append(df_m)

        if all_m:
            result = pd.concat(all_m).groupby(["일", "캠페인명"]).sum(numeric_only=True).reset_index()
            st.info(f"✅ 총 {len(result)}행 정제 완료")
            st.dataframe(result.head(1000))
            st.download_button(
                "📥 매체 정제 데이터 다운로드",
                result.to_csv(index=False).encode("utf-8-sig"),
                "media_cleaned.csv",
            )


# ────────────────────────────────────────────────────────────
# GA4 파싱 함수
# ────────────────────────────────────────────────────────────
def build_campaign_key_ga4(cid: str, search_term: str = "") -> str:
    """
    GA4 트래킹코드 → 캠페인명 변환
    어도비와 구조 동일하나:
    - parts[7] = 세그먼트명 (새로 추가)
    - parts[8] = 캠페인키
    - 기기 구분은 세션검색어(search_term)로 판별
    - 이미 dm-으로 시작하는 캠페인명은 그대로 통과
    """
    if pd.isna(cid) or str(cid).strip() == "":
        return "Unknown"

    raw = str(cid).strip()
    low = raw.lower()
    parts = raw.split("_")
    prefix = parts[0].lower()
    st_low = str(search_term).lower() if search_term else ""

    # 이미 변환된 캠페인명 → 그대로 통과
    if raw.startswith("dm-"):
        return raw

    # Unknown 필터
    if "_adef-" in low:  return "Unknown"
    if "_br_"  in low:  return "Unknown"
    if re.search(r"\.(com|instagram|youtube|facebook)", low): return "Unknown"
    if raw in ["(not set)", "(organic)", "(referral)", "(direct)"]: return "Unknown"

    # sms_
    if prefix == "sms":
        return "dm-smsoptin-smspn-alwayson-na-na"

    # pu_
    if prefix == "pu":
        return "dm-kakaooptin-kakaotransactional-alwayson-na-na"

    # smp_
    if prefix == "smp":
        medium = parts[1].lower() if len(parts) > 1 else ""
        if medium == "ig": return "Unknown"
        if "wc10" in low: return "dm-kakaooptin-kakaotransactional-alwayson-na-na"
        seg6 = parts[6].lower() if len(parts) > 6 else ""
        if medium == "kakao":
            # GA4: [6]이 kakao-opt-in
            if "kakao-opt-in" in seg6 or "welcomemessage" in low:
                c_key = normalize_campaign_key(parts[8]) if len(parts) > 8 else "alwayson-na-na"
                return f"dm-kakaooptin-kakaopn-{c_key}"
            return "Unknown"
        if medium in ["fbig", "meta"]:
            funnel = get_funnel(seg6)
            raw_key = parts[8] if len(parts) > 8 else ""
            c_key = normalize_campaign_key(raw_key)
            if "fbigcatalog" in st_low or "catalog" in st_low:
                return f"dm-{funnel}-fbigcatalog-alwayson-na-na"
            if len(c_key.split("-")) < 3: return "Unknown"
            return f"dm-{funnel}-fbig-{c_key}"
        return "Unknown"

    # ps_
    if prefix == "ps":
        medium = parts[1].lower() if len(parts) > 1 else ""
        if len(parts) < 9: return "Unknown"
        seg6 = parts[6].lower() if len(parts) > 6 else ""

        if "navershopping" in medium:
            return "dm-pro-shopping-alwayson-n-n"

        if "naver-brandzone" in medium or "daum-brandzone" in medium:
            if not (seg6.startswith("prospecting") or seg6.startswith("retargeting")):
                return "Unknown"
            if "daum" in medium:
                device = "kakaobsmo" if "mo" in st_low else "kakaobspc"
            else:
                device = "naverbsmo" if "mo" in st_low else "naverbspc"
            return f"dm-pro-{device}-alwayson-n-n"

        if medium in ["naver", "daum"] or (
            medium.startswith("naver") and "shopping" not in medium and "brandzone" not in medium
        ):
            if not (seg6.startswith("prospecting") or seg6.startswith("retargeting")):
                return "Unknown"
            if medium == "daum":
                funnel = get_funnel(seg6)
                device = "kakaomo" if "mo" in st_low else "kakaopc"
            else:
                funnel = get_funnel(seg6, naver=True)
                device = "navermo" if "mo" in st_low else "naverpc"
            if   "keyword-generic"  in seg6: cat = "generic"
            elif "keyword-activity" in seg6: cat = "Activity"
            elif "keyword-brand"    in seg6: cat = "brand"
            elif "keyword-product"  in seg6: cat = "product"
            else:                            cat = "brand"
            return f"dm-{funnel}-{device}-{cat}-na-na"

        if medium == "google":
            funnel = get_funnel(seg6)
            if   "keyword-generic"  in seg6: cat = "generic"
            elif "keyword-activity" in seg6: cat = "Activity"
            elif "keyword-brand"    in seg6: cat = "brand"
            elif "keyword-product"  in seg6: cat = "product"
            else:                            cat = "brand"
            return f"dm-{funnel}-googlepcmo-{cat}-na-na"

        return "Unknown"

    # dsp_
    if prefix == "dsp":
        medium  = parts[1].lower() if len(parts) > 1 else ""
        seg6    = parts[6].lower() if len(parts) > 6 else ""
        raw_key = parts[8] if len(parts) > 8 else ""
        c_key   = normalize_campaign_key(raw_key)

        def is_valid_da_key(key): return len(key.split("-")) >= 3

        if medium == "google":
            if   "pmaxw" in st_low: pmax = "PmaxW"
            elif "pmaxm" in st_low: pmax = "PmaxM"
            else:                   pmax = "PmaxC"
            return f"dm-prospecting-{pmax}-alwayson-na-na"

        if medium == "yt":
            return f"dm-{get_funnel(seg6)}-Youtube-alwayson-na-na"

        if medium == "criteo":
            return f"dm-{get_funnel(seg6)}-criteo-alwayson-na-na"

        if medium == "kakao-kw":
            return f"dm-{get_funnel(seg6)}-kakaokw-brand-alwayson-na-na"

        if medium == "naver":
            funnel = get_funnel(seg6)
            if "catalog" in low: return f"dm-{funnel}-gfacatalog-alwayson-na-na"
            if not is_valid_da_key(c_key): return "Unknown"
            return f"dm-{funnel}-GFA-{c_key}"

        if medium == "kakao":
            funnel = get_funnel(seg6)
            if "kakaocatalog" in st_low or "catalog" in st_low:
                return f"dm-{funnel}-kakaocatalog-alwayson-na-na"
            if not is_valid_da_key(c_key): return "Unknown"
            fmt = "bizboard" if "kakaobiz" in st_low else "display"
            return f"dm-{funnel}-{fmt}-{c_key}"

        if medium in ["fbig", "meta"]:
            funnel = get_funnel(seg6)
            if "catalog" in low: return f"dm-{funnel}-fbigcatalog-alwayson-na-na"
            if not is_valid_da_key(c_key): return "Unknown"
            return f"dm-{funnel}-fbig-{c_key}"

        if medium == "kream":
            funnel = get_funnel(seg6)
            if not is_valid_da_key(c_key): return "Unknown"
            return f"dm-{funnel}-Kream-{c_key}"

        if medium == "payco":
            return "dm-prospecting-payco-alwayson-na-na"

        return "Unknown"

    return "Unknown"


# ────────────────────────────────────────────────────────────
# GA4 날짜 추출
# ────────────────────────────────────────────────────────────
def get_date_ga4(content_lines):
    for line in content_lines:
        m = re.search(r"#\s*(\d{8})-(\d{8})", str(line))
        if m:
            d = m.group(1)
            return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return None


# ────────────────────────────────────────────────────────────
# GA4 탭
# ────────────────────────────────────────────────────────────
with tab3:
    st.header("📈 GA4 검수")
    ga4_files = st.file_uploader(
        "GA4 Excel 파일들을 드래그하세요.",
        type=["xlsx"], accept_multiple_files=True, key="t3"
    )

    if ga4_files:
        all_ga4 = []
        for f in ga4_files:
            raw_bytes = f.read()
            # 헤더 행 찾기 (날짜 컬럼 있는 행)
            xl = pd.read_excel(io.BytesIO(raw_bytes), header=None)
            header_row = 6  # 기본값
            for i, row in xl.iterrows():
                if "날짜" in str(row.values):
                    header_row = i + 1  # 다음 행이 실제 데이터
                    break

            df = pd.read_excel(io.BytesIO(raw_bytes), header=header_row - 1, skiprows=[header_row])
            # 컬럼 정리
            col_map = {
                df.columns[0]: "날짜",
                df.columns[1]: "세션소스",
                df.columns[2]: "세션캠페인",
                df.columns[3]: "세션광고콘텐츠",
                df.columns[4]: "세션검색어",
                df.columns[5]: "방문수",
                df.columns[6]: "참여세션수",
                df.columns[7]: "세션수",
                df.columns[8]: "장바구니",
                df.columns[9]: "구매",
                df.columns[10]: "총수익",
            }
            df.rename(columns=col_map, inplace=True)

            # 날짜 정리
            df["날짜"] = pd.to_datetime(
                df["날짜"].astype(str).str.strip(), errors="coerce"
            ).dt.strftime("%Y-%m-%d")
            df = df[df["날짜"].notna()]

            # 캠페인명 맵핑
            df["AI_제안명"] = df.apply(
                lambda r: build_campaign_key_ga4(r["세션캠페인"], r["세션검색어"]), axis=1
            )

            # 지표 숫자 변환
            for col in ["방문수", "참여세션수", "세션수", "장바구니", "구매", "총수익"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(",", ""), errors="coerce"
                    ).fillna(0)

            all_ga4.append(df)

        full_ga4 = pd.concat(all_ga4, ignore_index=True)
        total = len(full_ga4)
        unk = (full_ga4["AI_제안명"] == "Unknown").sum()
        st.info(f"✅ 총 {total}행 | ⚠️ Unknown: {unk}행 ({unk/total*100:.1f}%)")

        cols = ["날짜", "세션캠페인", "참여세션수", "세션수", "장바구니", "구매", "총수익", "AI_제안명"]
        st.subheader("전체 결과")
        st.dataframe(full_ga4[[c for c in cols if c in full_ga4.columns]].head(1000))

        unknown_df = full_ga4[full_ga4["AI_제안명"] == "Unknown"]
        if len(unknown_df) > 0:
            st.subheader("⚠️ Unknown 목록")
            st.dataframe(unknown_df[["세션캠페인", "세션검색어", "AI_제안명"]].drop_duplicates().head(200))

        st.download_button(
            "📥 GA4 검수 완료 다운로드",
            full_ga4.to_csv(index=False).encode("utf-8-sig"),
            "ga4_checked.csv",
        )
