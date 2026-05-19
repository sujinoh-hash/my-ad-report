"""
매일 자동 실행 파이프라인
GitHub Actions에서 매일 오전 9시 실행
"""
import json
import os
from datetime import datetime
from pathlib import Path

from collector.naver_searchad import get_keyword_stats, get_related_keywords
from collector.naver_open_api import collect_all
from analyzer.claude_analyzer import run_full_analysis


# 분석할 키워드 목록 (필요 시 수정)
TARGET_KEYWORDS = [
    "야간러닝",
    "새벽러닝",
    "실내러닝",
    "여름러닝",
    "여름러닝웨어",
    "러닝웨어 추천",
    "기능성 러닝웨어",
]

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def save_json(data: dict, filename: str):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 저장 완료: {path}")


def run():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*50}")
    print(f"🚀 분석 시작: {today}")
    print(f"{'='*50}\n")

    # 1. 검색량 수집
    print("📡 [1/3] 네이버 검색광고 API - 검색량 수집 중...")
    keyword_stats = get_keyword_stats(TARGET_KEYWORDS)
    save_json({"date": today, "stats": keyword_stats}, f"keyword_stats_{today}.json")

    # 연관 키워드 추가 수집
    related = []
    for kw in TARGET_KEYWORDS[:3]:
        related.extend(get_related_keywords(kw))
    save_json({"date": today, "related": related}, f"related_keywords_{today}.json")

    # 2. 블로그/카페 수집
    print("\n📡 [2/3] 네이버 Open API - 블로그/카페 수집 중...")
    blog_cafe_data = collect_all(TARGET_KEYWORDS)
    save_json({"date": today, **blog_cafe_data}, f"blog_cafe_{today}.json")

    # 3. AI 분석
    print("\n🤖 [3/3] Claude AI 분석 중...")
    analysis = run_full_analysis(keyword_stats, blog_cafe_data)
    save_json({"date": today, **analysis}, f"analysis_{today}.json")

    # 최신 분석 결과 덮어쓰기 (대시보드에서 latest.json 참조)
    save_json({"date": today, "keyword_stats": keyword_stats, **analysis}, "latest.json")

    print(f"\n✅ 전체 완료! data/ 폴더에 저장됨")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run()
