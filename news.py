"""
services/news.py
NewsData.io wrapper — live Indian news for current-affairs flash cards.
Free tier: 200 req/day  →  newsdata.io
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

NEWSDATA_KEY = os.getenv("NEWSDATA_API_KEY", "")
_BASE_URL = "https://newsdata.io/api/1/news"


async def fetch_news(
    count: int = 5,
    country: str = "in",
    language: str = "en",
    category: str = "education,science,technology",
) -> list[dict]:
    """
    Fetch recent Indian news articles from NewsData.io.
    Returns a list of dicts: [{"title": "...", "description": "..."}]
    Falls back to an empty list if the API key is missing or the request fails.
    """
    if not NEWSDATA_KEY:
        # Return placeholder cards so the UI doesn't break during dev
        return [
            {
                "title": "Bharat leads in space technology milestones",
                "description": "ISRO's latest mission marks another achievement in India's growing space programme.",
            },
            {
                "title": "NEP 2020 implementation gains momentum across states",
                "description": "Several states have begun rolling out the National Education Policy with focus on foundational literacy.",
            },
            {
                "title": "AI in education: How Indian startups are bridging the gap",
                "description": "EdTech companies are leveraging AI to reach students in tier-2 and tier-3 cities.",
            },
            {
                "title": "Green energy push: India targets 500 GW renewable capacity by 2030",
                "description": "Solar and wind energy investments accelerate across Rajasthan and Gujarat.",
            },
            {
                "title": "Digital India: Internet penetration crosses 900 million users",
                "description": "Rural broadband expansion under BharatNet continues at record pace.",
            },
        ][:count]

    url = (
        f"{_BASE_URL}"
        f"?apikey={NEWSDATA_KEY}"
        f"&country={country}"
        f"&language={language}"
        f"&category={category}"
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("results", [])[:count]
            return [
                {
                    "title": a.get("title", ""),
                    "description": a.get("description", "") or a.get("content", "")[:200],
                }
                for a in articles
            ]
    except Exception:
        return []
