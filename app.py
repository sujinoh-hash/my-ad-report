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

        # 네이버/카카오(다음) 브랜드검색
        if "naver-brandzone" in medium or "daum-brandzone" in medium:
            seg7 = parts[7].lower() if len(parts) > 7 else ""
            if not (seg7.startswith("prospecting") or seg7.startswith("retargeting")):
                return "Unknown"
            c_key = normalize_campaign_key(parts[8]) if len(parts) > 8 else "alwayson-na-na"
            device_seg = parts[9].lower() if len(parts) > 9 else ""
            if "daum" in medium:
                device = "kakaobsmo" if device_seg.startswith("mo") else "kakaobspc"
            else:
                device = "naverbsmo" if device_seg.startswith("mo") else "naverbspc"
            return f"dm-pro-{device}-{c_key}"

        # 네이버 SA / 다음 SA
        if medium in ["naver", "daum"] or (
            medium.startswith("naver") and "shopping" not in medium and "brandzone" not in medium
        ):
            seg7 = parts[7].lower() if len(parts) > 7 else ""
            if not (seg7.startswith("prospecting") or seg7.startswith("retargeting")):
                return "Unknown"
            funnel = get_funnel(seg7, naver=True)
            device_seg = parts[9].lower() if len(parts) > 9 else ""
            if medium == "daum":
                device = "kakaomo" if device_seg.startswith("mo") else "kakaopc"
            else:
                device = "navermo" if device_seg.startswith("mo") else "naverpc"
            if   "keyword-generic"  in seg7: cat = "generic"
            elif "keyword-activity" in seg7: cat = "Activity"
            elif "keyword-brand"    in seg7: cat = "brand"
            elif "keyword-product"  in seg7: cat = "product"
            else:                            cat = "brand"
            c_key = normalize_campaign_key(parts[8]) if len(parts) > 8 else "alwayson-na-na"
            return f"dm-{funnel}-{device}-{cat}-{c_key}"

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
            c_key = normalize_campaign_key(parts[8]) if len(parts) > 8 else "alwayson-na-na"
            return f"dm-{funnel}-googlepcmo-{cat}-{c_key}"

        return "Unknown"

    # ── dsp_ ──────────────────────────────────────────────────
    if prefix == "dsp":
        medium  = parts[1].lower() if len(parts) > 1 else ""
        seg7    = parts[7].lower() if len(parts) > 7 else ""
        c_key   = normalize_campaign_key(parts[8]) if len(parts) > 8 else "alwayson-na-na"
        dev_seg = parts[9].lower() if len(parts) > 9 else ""

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

        # 카카오 SA (kakao-kw)
        if medium == "kakao-kw":
            return f"dm-{get_funnel(seg7)}-kakaokw-brand-{c_key}"

        # 네이버 GFA / catalog
        if medium == "naver":
            funnel = get_funnel(seg7, naver=True)
            fmt = "catalog" if "catalog" in low else "GFA"
            return f"dm-{funnel}-{fmt}-{c_key}"

        # 카카오 DA
        if medium == "kakao":
            funnel = get_funnel(seg7)
            if   "catalog"          in low:            fmt = "catalog"
            elif dev_seg.startswith("mo-"):            fmt = "bizboard"
            else:                                      fmt = "display"
            return f"dm-{funnel}-{fmt}-{c_key}"

        # 메타 DA
        if medium in ["fbig", "meta"]:
            funnel = get_funnel(seg7)
            fmt = "catalog" if "catalog" in low else "fbig"
            return f"dm-{funnel}-{fmt}-{c_key}"

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
tab1, tab2 = st.tabs(["🎯 1단계: 어도비 검수", "📊 2단계: 데이터 통합"])

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
    st.header("📊 데이터 최종 통합 리포트")
    c1, c2 = st.columns(2)
    with c1:
        adobe_in = st.file_uploader("1. 검수된 어도비 파일", type="csv", key="t2a")
    with c2:
        media_ins = st.file_uploader(
            "2. 매체 Raw 파일들", type=["csv", "xlsx"],
            accept_multiple_files=True, key="t2m",
        )

    if adobe_in and media_ins:
        df_a = pd.read_csv(adobe_in)
        all_m = []
        for mf in media_ins:
            if mf.name.endswith("xlsx"):
                df_m = pd.read_excel(mf)
            else:
                raw = mf.read()
                for enc in ["utf-8-sig", "euc-kr", "cp949", "utf-8"]:
                    try:
                        df_m = pd.read_csv(io.StringIO(raw.decode(enc)))
                        break
                    except Exception:
                        continue
                else:
                    st.error(f"❌ {mf.name} 파일 인코딩을 읽을 수 없어요.")
                    continue
            ren = {
                "일": "일", "Day": "일", "일자": "일", "일별": "일", "날짜": "일",
                "캠페인 이름": "캠페인명", "Campaign": "캠페인명", "메시지명": "캠페인명",
                "광고상품": "캠페인명", "최종광고비": "광고비", "결제 금액": "광고비",
                "노출수": "노출", "노출": "노출", "Displays": "노출",
                "클릭수": "클릭", "Clicks": "클릭",
                "지출 금액 (KRW)": "광고비", "Cost": "광고비", "집행금액": "광고비",
                "친구 추가수(7일)": "채널친구수", "전환수": "채널친구수",
                "집행 전환수": "채널친구수", "친구 추가 수 (7일) ": "채널친구수",
            }
            df_m.rename(columns=ren, inplace=True)

            fname = mf.name
            if "메시지" in fname:
                df_m["캠페인명"] = "dm-kakaooptin-kakaotransactional-alwayson-na-na"
            elif "cpk" in fname.lower():
                df_m["캠페인명"] = "Kakao Offerwall"
            elif "쇼핑파트너" in fname or "결제 금액" in df_m.columns:
                df_m["캠페인명"] = "쇼핑파트너센터"
                df_m["광고비"] = df_m["광고비"].apply(
                    lambda x: abs(float(str(x).replace(",", ""))) if pd.notna(x) else 0
                )
                df_m["노출"], df_m["클릭"] = 0, 0

            if "열람수" in df_m.columns:
                df_m.loc[df_m["캠페인명"].str.contains("kakaopn", na=False), "노출"] = df_m["열람수"]

            for col in ["노출", "클릭", "광고비", "채널친구수"]:
                if col in df_m.columns:
                    df_m[col] = pd.to_numeric(
                        df_m[col].astype(str).str.replace(",", ""), errors="coerce"
                    ).fillna(0)

            # 날짜 형식 통일 (YYYY-MM-DD)
            if "일" in df_m.columns:
                df_m["일"] = pd.to_datetime(
                    df_m["일"].astype(str).str.strip(), errors="coerce"
                ).dt.strftime("%Y-%m-%d")

            # 필요한 컬럼만 남기기
            keep_cols = ["일", "캠페인명", "노출", "클릭", "광고비", "채널친구수"]
            df_m = df_m[[c for c in keep_cols if c in df_m.columns]]
            all_m.append(df_m)

        df_m_total = pd.concat(all_m).groupby(["일", "캠페인명"]).sum(numeric_only=True).reset_index()

        if st.button("🚀 최종 통합 실행"):
            df_a_sum = df_a.groupby(["날짜", "AI_제안명"]).agg(
                {"방문 횟수": "sum", "Cart Adds": "sum", "Orders": "sum", "Revenue": "sum"}
            ).reset_index()

            final = pd.merge(
                df_m_total, df_a_sum,
                left_on=["일", "캠페인명"], right_on=["날짜", "AI_제안명"],
                how="outer",
            )
            final["일"] = final["일"].fillna(final["날짜"])
            final["캠페인명"] = final["캠페인명"].fillna(final["AI_제안명"])

            result = final.drop(columns=["날짜", "AI_제안명"]).sort_values(["일", "캠페인명"])
            st.dataframe(result.head(1000))
            st.download_button(
                "📥 통합 리포트 다운로드",
                result.to_csv(index=False).encode("utf-8-sig"),
                "lululemon_final_report_v21.csv",
            )
