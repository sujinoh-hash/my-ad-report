"""
Claude AI 분석 엔진
- 키워드 트렌드 분석
- 소비자 언어 → 소구점 분류
- 광고 카피 추천
"""
import os
import json
import anthropic
from datetime import datetime


client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def analyze_keywords(keyword_stats: list[dict]) -> dict:
    """검색량 데이터 기반 트렌드 분석"""
    stats_text = "\n".join([
        f"- {item['keyword']}: 월간 {item['monthly_total']:,}회 (PC {item['monthly_pc']:,} / 모바일 {item['monthly_mobile']:,}), 경쟁도: {item['competition']}"
        for item in sorted(keyword_stats, key=lambda x: x["monthly_total"], reverse=True)
    ])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""다음은 네이버 검색광고 키워드 검색량 데이터입니다.

{stats_text}

아래 JSON 형식으로만 분석 결과를 출력하세요. 다른 텍스트 없이:
{{
  "top_keywords": ["검색량 상위 키워드 3개"],
  "trend_summary": "2줄 이내 트렌드 요약",
  "opportunity_keywords": ["경쟁도 낮고 검색량 있는 기회 키워드 3개"],
  "peak_insight": "광고 집행 타이밍 인사이트 1줄"
}}"""
        }]
    )

    text = message.content[0].text
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def classify_consumer_language(posts: list[dict], keyword: str) -> dict:
    """블로그/카페 게시글에서 소비자 언어 분류"""
    sample = posts[:15]
    content_text = "\n".join([
        f"[{p['type']}] 제목: {p['title']} / 내용: {p['description'][:100]}"
        for p in sample
    ])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f""""{keyword}" 관련 네이버 블로그/카페 게시글입니다.

{content_text}

소비자 언어를 분석해서 아래 JSON 형식으로만 출력하세요:
{{
  "pain_points": ["페인포인트 키워드 5개"],
  "benefits": ["혜택/결과 키워드 5개"],
  "copy_materials": ["광고 카피 소재 키워드 8개"],
  "trends": ["트렌드 표현 3개"],
  "consumer_insight": "소비자 핵심 니즈 1줄 요약"
}}"""
        }]
    )

    text = message.content[0].text
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def generate_ad_copies(keyword: str, consumer_data: dict, format_type: str = "search") -> list[dict]:
    """광고 카피 자동 생성"""
    format_guide = {
        "search": "네이버 검색광고 헤드라인 (15자 이내)",
        "sns": "SNS 배너 카피 (짧고 감성적)",
        "both": "검색광고 + SNS 배너 두 가지 모두",
    }

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""키워드: "{keyword}"
소비자 인사이트: {consumer_data.get('consumer_insight', '')}
페인포인트: {', '.join(consumer_data.get('pain_points', []))}
혜택: {', '.join(consumer_data.get('benefits', []))}
트렌드: {', '.join(consumer_data.get('trends', []))}

위 데이터를 바탕으로 {format_guide[format_type]} 카피를 생성하세요.

아래 JSON 형식으로만 출력하세요:
{{
  "copies": [
    {{"headline": "카피 텍스트", "angle": "소구 방향 (상황/기능/감성 중 하나)", "note": "10자 이내 설명"}},
    {{"headline": "카피 텍스트", "angle": "소구 방향", "note": "10자 이내 설명"}},
    {{"headline": "카피 텍스트", "angle": "소구 방향", "note": "10자 이내 설명"}},
    {{"headline": "카피 텍스트", "angle": "소구 방향", "note": "10자 이내 설명"}},
    {{"headline": "카피 텍스트", "angle": "소구 방향", "note": "10자 이내 설명"}}
  ]
}}"""
        }]
    )

    text = message.content[0].text
    result = json.loads(text.replace("```json", "").replace("```", "").strip())
    return result.get("copies", [])


def run_full_analysis(keyword_stats: list[dict], blog_cafe_data: dict) -> dict:
    """전체 분석 파이프라인 실행"""
    print("📊 키워드 트렌드 분석 중...")
    trend_analysis = analyze_keywords(keyword_stats)

    results = {
        "analyzed_at": datetime.now().isoformat(),
        "trend_analysis": trend_analysis,
        "keyword_analysis": {},
    }

    keywords = list(blog_cafe_data.get("summary", {}).keys())
    for kw in keywords:
        print(f"🔍 '{kw}' 소비자 언어 분석 중...")
        posts = [
            p for p in blog_cafe_data.get("blog", []) + blog_cafe_data.get("cafe", [])
            if p["keyword"] == kw
        ]

        if not posts:
            continue

        consumer_data = classify_consumer_language(posts, kw)
        copies = generate_ad_copies(kw, consumer_data, format_type="both")

        results["keyword_analysis"][kw] = {
            "consumer_language": consumer_data,
            "ad_copies": copies,
            "post_count": len(posts),
        }

    return results


if __name__ == "__main__":
    # 테스트용 더미 데이터
    dummy_stats = [
        {"keyword": "야간러닝", "monthly_pc": 1200, "monthly_mobile": 8500, "monthly_total": 9700, "competition": "중간"},
        {"keyword": "새벽러닝", "monthly_pc": 800, "monthly_mobile": 6200, "monthly_total": 7000, "competition": "낮음"},
    ]
    print(json.dumps(analyze_keywords(dummy_stats), ensure_ascii=False, indent=2))
