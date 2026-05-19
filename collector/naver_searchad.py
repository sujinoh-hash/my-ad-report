"""
네이버 검색광고 API - 키워드 검색량 수집
"""
import os
import json
import hmac
import hashlib
import base64
import time
import requests
from datetime import datetime


BASE_URL = "https://api.naver.com"


def get_signature(timestamp: str, method: str, path: str, secret_key: str) -> str:
    message = f"{timestamp}.{method}.{path}"
    sig = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(sig.digest()).decode()


def get_headers(method: str, path: str) -> dict:
    timestamp = str(int(time.time() * 1000))
    signature = get_signature(
        timestamp, method, path,
        os.environ["NAVER_AD_SECRET_KEY"]
    )
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": os.environ["NAVER_AD_ACCESS_LICENSE"],
        "X-Customer": os.environ["NAVER_AD_CUSTOMER_ID"],
        "X-Signature": signature,
    }


def get_keyword_stats(keywords: list[str]) -> list[dict]:
    """키워드 월간 검색량 조회 (PC + 모바일)"""
    path = "/keywordstool"
    url = BASE_URL + path
    headers = get_headers("GET", path)

    results = []
    # API 한 번에 최대 5개
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        params = {"hintKeywords": ",".join(batch), "showDetail": 1}
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("keywordList", []):
            results.append({
                "keyword": item["relKeyword"],
                "monthly_pc": item["monthlyPcQcCnt"],
                "monthly_mobile": item["monthlyMobileQcCnt"],
                "monthly_total": item["monthlyPcQcCnt"] + item["monthlyMobileQcCnt"],
                "competition": item.get("compIdx", ""),
                "collected_at": datetime.now().isoformat(),
            })
        time.sleep(0.5)

    return results


def get_related_keywords(keyword: str) -> list[dict]:
    """연관 키워드 조회"""
    path = "/keywordstool"
    url = BASE_URL + path
    headers = get_headers("GET", path)
    params = {"hintKeywords": keyword, "showDetail": 1}

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("keywordList", [])[:20]:
        results.append({
            "keyword": item["relKeyword"],
            "monthly_total": item["monthlyPcQcCnt"] + item["monthlyMobileQcCnt"],
            "competition": item.get("compIdx", ""),
        })

    return sorted(results, key=lambda x: x["monthly_total"], reverse=True)


if __name__ == "__main__":
    keywords = ["야간러닝", "새벽러닝", "실내러닝", "여름러닝", "러닝웨어"]
    stats = get_keyword_stats(keywords)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
