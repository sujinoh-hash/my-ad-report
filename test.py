def build_campaign_key_v4(cid):
    if pd.isna(cid): return "Unknown"
    cid = str(cid).lower().strip()
    
    # 1. [캠페인키]
    camp = "alwayson" # 기본값
    if "yet-spring2026-run" in cid: camp = "26Run"
    elif "train-winter2025" in cid: camp = "Train"
    elif "bottoms-spring2026" in cid: camp = "Pants"
    elif "holiday-winter2025" in cid: camp = "Holiday"
    elif "men-2026" in cid: camp = "men"
    elif "activity" in cid: camp = "activity"
    elif "brand" in cid: camp = "brand"
    elif "product" in cid: camp = "product"

    # 2. [퍼널] & [dm] (사용자님 예시: BS-dm, upper-dm 등)
    funnel_dm = "middle-dm" # 기본값
    if "brandzone" in cid or "naverbsp" in cid or "kakaobsp" in cid: 
        funnel_dm = "BS-dm"
    elif "upper" in cid: funnel_dm = "upper-dm"
    elif "lower" in cid: funnel_dm = "lower-dm"
    elif "middle" in cid: funnel_dm = "middle-dm"

    # 3. [타겟팅]
    target = "pro" # 기본값 (prospecting의 약자)
    if "retargeting" in cid: target = "retargeting"
    elif "prospecting" in cid or "pro-" in cid: target = "pro"
    elif "kakaooptin-transactional" in cid: target = "kakaooptin-transactional"

    # 4. [매체명] (번역 규칙 반영)
    media = ""
    # 네이버 브랜드검색 (mo/pc 구분)
    if "brandzone" in cid or "naverbsp" in cid:
        media = "naverbsmo" if "mo-" in cid else "naverbspc"
    # 카카오 브랜드검색
    elif "kakaobsp" in cid:
        media = "kakaobsmo" if "mo-" in cid else "kakaobspc"
    # 메타 (metaC, metam3 등)
    elif "meta" in cid or "smp_fbig" in cid:
        if "catalog" in cid: media = "metaC"
        elif "prospecting-na-na" in cid: media = "metam3"
        else: media = "meta"
    # 카카오 (kakaoda, kakaodaD, kakaotalksa 등)
    elif "dsp_kakao" in cid or "kakao" in cid:
        if "native" in cid or "kakaodad" in cid: media = "kakaodaD"
        elif "kakao-kw" in cid: media = "kakaotalksa"
        else: media = "kakaoda"
    # 네이버 DA
    elif "dsp_naver" in cid or "naverda" in cid:
        media = "naverda"
    # 구글/유튜브/크리테오
    elif "google" in cid: media = "google"
    elif "youtube" in cid: media = "YouTube"
    elif "criteo" in cid: media = "criteo"

    # 5. [최종 조립] 캠페인키-퍼널-dm-타겟팅-매체명
    # 예시: alwayson-BS-dm-pro-naverbsmo
    result = f"{camp}-{funnel_dm}-{target}-{media}"
    
    return result
