"""
네이버 Open API - 블로그/카페 언급량 및 소비자 언어 수집
"""
import os
import json
import requests
import re
from datetime import datetime


NAVER_API_URL = "https://openapi.naver.com/v1/search"


def get_headers() -> dict:
    return {
        "X-Naver-Client-Id": os.environ["NAVER_CLIENT_ID"],
        "X-Naver-Client-Secret": os.environ["NAVER_CLIENT_SECRET"],
    }


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).replace("&quot;", '"').replace("&amp;", "&").strip()


def search_blog(keyword: str, display: int = 20) -> list[dict]:
    """블로그 게시글 수집"""
    params = {
        "query": keyword,
        "display": display,
        "sort": "date",
    }
    resp = requests.get(
        f"{NAVER_API_URL}/blog.json",
        headers=get_headers(),
        params=params,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])

    results = []
    for item in items:
        results.append({
            "type": "blog",
            "keyword": keyword,
            "title": strip_html(item.get("title", "")),
            "description": strip_html(item.get("description", "")),
            "blogger_name": item.get("bloggername", ""),
            "post_date": item.get("postdate", ""),
            "link": item.get("link", ""),
            "collected_at": datetime.now().isoformat(),
        })
    return results


def search_cafe(keyword: str, display: int = 20) -> list[dict]:
    """카페 게시글 수집"""
    params = {
        "query": keyword,
        "display": display,
        "sort": "date",
    }
    resp = requests.get(
        f"{NAVER_API_URL}/cafearticle.json",
        headers=get_headers(),
        params=params,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])

    results = []
    for item in items:
        results.append({
            "type": "cafe",
            "keyword": keyword,
            "title": strip_html(item.get("title", "")),
            "description": strip_html(item.get("description", "")),
            "cafe_name": item.get("cafename", ""),
            "post_date": item.get("postdate", ""),
            "link": item.get("link", ""),
            "collected_at": datetime.now().isoformat(),
        })
    return results


def collect_all(keywords: list[str]) -> dict:
    """키워드 목록 전체 수집"""
    all_results = {"blog": [], "cafe": [], "summary": {}}

    for kw in keywords:
        try:
            blogs = search_blog(kw, display=10)
            cafes = search_cafe(kw, display=10)
            all_results["blog"].extend(blogs)
            all_results["cafe"].extend(cafes)
            all_results["summary"][kw] = {
                "blog_count": len(blogs),
                "cafe_count": len(cafes),
                "total": len(blogs) + len(cafes),
            }
        except Exception as e:
            print(f"[ERROR] {kw}: {e}")

    return all_results


if __name__ == "__main__":
    keywords = ["야간러닝", "새벽러닝", "실내러닝", "여름러닝웨어"]
    result = collect_all(keywords)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
