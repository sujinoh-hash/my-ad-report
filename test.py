import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="GA4 TSV → Excel 변환", layout="wide")
st.title("🔄 GA4 TSV → Excel 변환")
st.caption("GA4에서 다운받은 TSV 파일을 업로드하면 Excel(.xlsx)로 변환해드려요.")

# ────────────────────────────────────────────────────────────
# 캠페인키 정규화
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
    if not key:
        return key
    m = re.match(r"^(spring|winter|summer|fall)-(\d{4})-alwayson$", key)
    if m:
        return f"na-{m.group(2)}-alwayson"
    return CAMPAIGN_KEY_MAP.get(key, key)

def get_funnel(seg: str, naver: bool = False) -> str:
    is_ret = seg.startswith("retargeting")
    if naver:
        return "re" if is_ret else "pro"
    return "retargeting" if is_ret else "prospecting"

def build_campaign_key_ga4(cid: str, search_term: str = "", ad_content: str = "") -> str:
    if pd.isna(cid) or str(cid).strip() == "":
        return "Unknown"

    raw = str(cid).strip()
    low = raw.lower()
    parts = raw.split("_")
    prefix = parts[0].lower()
    st_low = str(search_term).lower() if search_term and str(search_term) != "nan" else ""
    ac_low = str(ad_content).lower() if ad_content and str(ad_content) != "nan" else ""

    if raw.startswith("dm-"):                             return raw
    if "_adef-" in low:                                   return "Unknown"
    if "_br_"   in low:                                   return "Unknown"
    if re.search(r"\.(com|instagram|youtube|facebook)", low): return "Unknown"
    if raw in ["(not set)", "(organic)", "(referral)", "(direct)"]: return "Unknown"

    if prefix == "sms":
        return "dm-smsoptin-smspn-alwayson-na-na"
    if prefix == "pu":
        return "dm-kakaooptin-kakaotransactional-alwayson-na-na"

    if prefix == "smp":
        medium = parts[1].lower() if len(parts) > 1 else ""
        if medium == "ig": return "Unknown"
        if "wc10" in low:  return "dm-kakaooptin-kakaotransactional-alwayson-na-na"
        seg6 = parts[6].lower() if len(parts) > 6 else ""
        if medium == "kakao":
            if "kakao-opt-in" in seg6 or "welcomemessage" in low:
                c_key = normalize_campaign_key(parts[8]) if len(parts) > 8 else "alwayson-na-na"
                return f"dm-kakaooptin-kakaopn-{c_key}"
            return "Unknown"
        if medium in ["fbig", "meta"]:
            funnel  = get_funnel(seg6)
            raw_key = parts[8] if len(parts) > 8 else ""
            c_key   = normalize_campaign_key(raw_key)
            if "fbigcatalog" in st_low or "catalog" in st_low:
                return f"dm-{funnel}-fbigcatalog-alwayson-na-na"
            if len(c_key.split("-")) < 3: return "Unknown"
            return f"dm-{funnel}-fbig-{c_key}"
        return "Unknown"

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
                device = "kakaobsmo" if ac_low.startswith("mo-") else "kakaobspc"
            else:
                device = "naverbsmo" if ac_low.startswith("mo-") else "naverbspc"
            return f"dm-pro-{device}-alwayson-n-n"
        if medium in ["naver", "daum"] or (
            medium.startswith("naver") and "shopping" not in medium and "brandzone" not in medium
        ):
            if not (seg6.startswith("prospecting") or seg6.startswith("retargeting")):
                return "Unknown"
            if medium == "daum":
                funnel = get_funnel(seg6)
                device = "kakaomo" if ac_low.startswith("mo-") else "kakaopc"
            else:
                funnel = get_funnel(seg6, naver=True)
                device = "navermo" if ac_low.startswith("mo-") else "naverpc"
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

    if prefix == "dsp":
        medium  = parts[1].lower() if len(parts) > 1 else ""
        seg6    = parts[6].lower() if len(parts) > 6 else ""
        raw_key = parts[8] if len(parts) > 8 else ""
        c_key   = normalize_campaign_key(raw_key)

        def is_valid(k): return len(k.split("-")) >= 3

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
            if not is_valid(c_key): return "Unknown"
            return f"dm-{funnel}-GFA-{c_key}"
        if medium == "kakao":
            funnel = get_funnel(seg6)
            if "kakaocatalog" in st_low or "catalog" in st_low:
                return f"dm-{funnel}-kakaocatalog-alwayson-na-na"
            if not is_valid(c_key): return "Unknown"
            fmt = "bizboard" if "kakaobiz" in st_low else "display"
            return f"dm-{funnel}-{fmt}-{c_key}"
        if medium in ["fbig", "meta"]:
            funnel = get_funnel(seg6)
            if "catalog" in low: return f"dm-{funnel}-fbigcatalog-alwayson-na-na"
            if not is_valid(c_key): return "Unknown"
            return f"dm-{funnel}-fbig-{c_key}"
        if medium == "kream":
            funnel = get_funnel(seg6)
            if not is_valid(c_key): return "Unknown"
            return f"dm-{funnel}-Kream-{c_key}"
        if medium == "payco":
            return "dm-prospecting-payco-alwayson-na-na"
        return "Unknown"

    return "Unknown"


# ────────────────────────────────────────────────────────────
# TSV 파싱
# ────────────────────────────────────────────────────────────
COLUMN_MAP = {
    "날짜": "날짜", "date": "날짜",
    "세션 소스": "세션소스", "세션소스": "세션소스", "session source": "세션소스",
    "세션 캠페인": "세션캠페인", "세션캠페인": "세션캠페인", "session campaign": "세션캠페인", "campaign": "세션캠페인",
    "세션 광고 콘텐츠": "세션광고콘텐츠", "세션광고콘텐츠": "세션광고콘텐츠", "세션 수동 광고 콘텐츠": "세션광고콘텐츠",
    "세션 검색어": "세션검색어", "세션검색어": "세션검색어",
    "방문수": "방문수", "users": "방문수", "총 사용자": "방문수",
    "참여 세션수": "참여세션수", "참여세션수": "참여세션수", "engaged sessions": "참여세션수",
    "세션수": "세션수", "세션": "세션수", "sessions": "세션수",
    "장바구니에 추가": "장바구니", "장바구니": "장바구니", "add to carts": "장바구니",
    "구매": "구매", "purchases": "구매", "transactions": "구매",
    "총 수익": "총수익", "총수익": "총수익", "revenue": "총수익", "total revenue": "총수익", "구매 수익": "총수익",
}

def parse_tsv(raw_bytes: bytes) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-16", "utf-8", "euc-kr"]:
        try:
            text = raw_bytes.decode(enc)
            break
        except Exception:
            continue
    else:
        raise ValueError("파일 인코딩을 읽을 수 없어요.")

    lines = text.splitlines()
    header_row = None
    for i, line in enumerate(lines):
        cols = [c.strip() for c in line.split("\t")]
        if any(k in " ".join(cols) for k in ["날짜", "세션", "Date", "Session", "Campaign"]):
            header_row = i
            break
    if header_row is None:
        raise ValueError("헤더 행을 찾을 수 없어요. TSV 파일 구조를 확인하세요.")

    df = pd.read_csv(io.StringIO(text), sep="\t", header=header_row)

    # 합계 행 제거
    first_col = df.columns[0]
    df = df[~df[first_col].astype(str).str.contains(r"합계|총계|Total|Grand Total", na=False)]
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 컬럼명 정규화
    ren = {}
    for col in df.columns:
        key = col.strip().lower()
        for pattern, mapped in COLUMN_MAP.items():
            if key == pattern.lower():
                ren[col] = mapped
                break
    df.rename(columns=ren, inplace=True)

    # 숫자 변환
    for col in ["방문수", "참여세션수", "세션수", "장바구니", "구매", "총수익"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.replace("₩", "").str.strip(),
                errors="coerce"
            ).fillna(0)

    return df


# ────────────────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────────────────
tsv_files = st.file_uploader(
    "GA4 TSV 파일을 드래그하세요. 여러 개도 가능해요.",
    type=["tsv", "txt"],
    accept_multiple_files=True,
)

if tsv_files:
    for f in tsv_files:
        st.divider()
        st.markdown(f"### 📄 {f.name}")
        try:
            raw_bytes = f.read()
            df = parse_tsv(raw_bytes)

            # 캠페인명 변환
            if "세션캠페인" in df.columns:
                df.insert(
                    df.columns.get_loc("세션캠페인") + 1,
                    "AI_제안명",
                    df.apply(
                        lambda r: build_campaign_key_ga4(
                            r["세션캠페인"],
                            r.get("세션검색어", ""),
                            r.get("세션광고콘텐츠", "")
                        ), axis=1
                    )
                )
                unk = (df["AI_제안명"] == "Unknown").sum()
                st.info(f"✅ {len(df)}행 변환 완료 | ⚠️ Unknown: {unk}행")

            st.dataframe(df.head(500), use_container_width=True)

            # Excel 변환
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="GA4 데이터")

            out_name = f.name.rsplit(".", 1)[0] + ".xlsx"
            st.download_button(
                label=f"📥 {out_name} 다운로드",
                data=out.getvalue(),
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{f.name}",
            )

        except Exception as e:
            st.error(f"❌ 오류: {e}")
