import streamlit as st
import pandas as pd

st.set_page_config(page_title="6만행 최종 매핑 검증기", layout="wide")

# 1. 시트 설정 (GID를 여기서 꼭 확인해서 수정해주세요!)
SHEET_ID = "1u57_Dqo9KoqcpP5OqM9XzD9W3J-VIxYrj0LSrcaYdgY"
MAPPING_GID = "1901484506"  # <--- '맵핑' 탭의 gid 숫자로 바꿔주세요!

import re

def has_token(text, token):
    return re.search(rf'(^|[_-]){re.escape(token)}([_-]|$)', text) is not None

def build_perfect_key(cid):
    if pd.isna(cid):
        return "Unknown"

    cid_raw = str(cid).strip()
    cid_low = cid_raw.lower()

    if cid_raw == "" or "_adef-" in cid_low:
        return "Unknown"

    if cid_low == "sms_senders":
        return "SMS_Senders"
    if "navershopping" in cid_low:
        return "Naver shopping"

    # 1. 매체 판별
    media = "google"

    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver"]):
        media = "naverbsmo" if "mo-" in cid_low else "naverbspc"
    elif "kakaobsp" in cid_low:
        media = "kakaobsmo" if "mo-" in cid_low else "kakaobspc"
    elif "dsp_yt" in cid_low:
        media = "YouTube"
    elif "dsp_naver" in cid_low:
        media = "naverda"
    elif "dsp_kakao" in cid_low:
        if "catalog" in cid_low:
            media = "kakaodaC"
        elif any(x in cid_low for x in ["native", "kakaodad", "video", "dual"]):
            media = "kakaodaD"
        else:
            media = "kakaoda"
    elif "meta" in cid_low or "smp_fbig" in cid_low:
        if "catalog" in cid_low and ("advantage" in cid_low or "pixel" in cid_low):
            media = "metaC"
        elif "prospecting-na-na" in cid_low:
            media = "metam3"
        else:
            media = "meta"
    elif "pmax" in cid_low:
        if any(x in cid_low for x in ["w_prospecting", "demo-women", "pmaxw"]):
            media = "pmaxW"
        elif "pmaxm" in cid_low:
            media = "pmaxM"
        else:
            media = "pmaxC"
    elif "kakao-kw" in cid_low or "kakaotalksa" in cid_low:
        media = "kakaotalksa"
    elif "naverpc" in cid_low:
        media = "naverpc"
    elif "navermo" in cid_low:
        media = "navermo"
    elif "criteo" in cid_low:
        media = "criteo"

    # 2. 캠페인 Prefix
    camp = "alwayson"

    if media in ["kakaoda", "kakaodaC", "kakaodaD", "meta", "metaC", "metam3", "naverda"]:
        if any(x in cid_low for x in ["steadystate", "becalm", "bigcozy"]):
            camp = "Holiday"
        elif "train-winter2025-train" in cid_low:
            camp = "Train"
        elif "bottoms-spring2026-otm" in cid_low:
            camp = "Pants"
        elif "holiday-winter2025-general" in cid_low:
            camp = "Holiday"
        elif "yet-spring2026-run" in cid_low:
            camp = "26Run"
        elif "winter-2026-alwayson" in cid_low:
            camp = "alwayson"
        elif "men-2026-alwayson" in cid_low:
            camp = "alwayson"
        elif "spring-2026-alwayson" in cid_low:
            camp = "alwayson"
    else:
        if re.search(r'(^|[_-])product([_-]|$)', cid_low):
            camp = "product"
        elif re.search(r'(^|[_-])activity([_-]|$)', cid_low):
            camp = "activity"
        elif re.search(r'(^|[_-])brand([_-]|$)', cid_low):
            camp = "brand"

    # 3. 단계
    lvl = "middle-dm"
    if has_token(cid_low, "upper"):
        lvl = "upper-dm"
    elif has_token(cid_low, "lower"):
        lvl = "lower-dm"

    if media == "naverda" and lvl == "lower-dm":
        lvl = "middle-dm"

    if any(x in cid_low for x in ["brandzone", "naverbsp", "ps_naver", "kakaobsp"]):
        lvl = "BS-dm"

    # 4. 타겟
    target = "retargeting" if "retargeting" in cid_low else "prospecting"

    if media in [
        "naverpc", "navermo",
        "kakaotalksa",
        "naverbsmo", "naverbspc",
        "kakaobsmo", "kakaobspc"
    ]:
        target = "pro"

    return f"{camp}-{lvl}-{target}-{media}"
