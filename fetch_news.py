#!/usr/bin/env python3
"""
Daily news fetcher for Zer0 Updates.
"""

import json
import os
import sys
from datetime import datetime, timezone

import feedparser
import requests

FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.engadget.com/rss.xml",
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://www.wired.com/feed/rss",
    "https://www.techradar.com/rss",
    "https://feeds.npr.org/1001/rss.xml",
]

MAX_ITEMS_PER_FEED = 30
OUTPUT_PATH = "news.json"
GEMINI_MODEL = "gemini-flash-latest"


def fetch_raw_items():
    items = []
    for url in FEEDS:
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            print(f"[warn] failed to fetch {url}: {e}", file=sys.stderr)
            continue

        for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
            image = ""
            if "media_thumbnail" in entry and entry.media_thumbnail:
                image = entry.media_thumbnail[0].get("url", "")
            elif "media_content" in entry and entry.media_content:
                image = entry.media_content[0].get("url", "")

            items.append({
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", "").strip(),
                "link": entry.get("link", ""),
                "image": image,
                "published": entry.get("published", ""),
            })

    seen = set()
    deduped = []
    for it in items:
        if it["link"] and it["link"] not in seen:
            seen.add(it["link"])
            deduped.append(it)
    return deduped


SCHEMA_INSTRUCTIONS = """You are given a list of raw news headlines and summaries.
Each raw item includes a "link" and possibly an "image" URL — carry these through
unchanged into your output for the matching article.

Select up to 70 distinct, genuinely newsworthy items and return ONLY a JSON array
(no prose, no markdown fences) where each item has exactly these fields:

- cat: short category label, one of: Tech, Business, Science, World, Other
- title: short headline (max ~12 words), written in your own words, not copied verbatim
- summary: 1-2 sentences (max 35 words total), written in your own words, not copied verbatim from the source
- link: the exact "link" value from the matching raw item (string, do not modify)
- image: the exact "image" value from the matching raw item if present, otherwise an empty string

Use as many of the raw items as genuinely qualify — do not artificially limit below 70 if more are available.
Return ONLY the JSON array."""


def build_news_via_gemini(raw_items):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    prompt = SCHEMA_INSTRUCTIONS + "\n\nRAW ITEMS:\n" + json.dumps(raw_items, indent=2)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 16000},
        },
        timeout=120,
    )

    print(f"[debug] status={resp.status_code} body={resp.text[:500]}", file=sys.stderr)
    resp.raise_for_status()
    data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


def main():
    raw_items = fetch_raw_items()
    if not raw_items:
        print("[error] no raw items fetched from any feed", file=sys.stderr)
        sys.exit(1)

    print(f"[info] fetched {len(raw_items)} raw items total", file=sys.stderr)

    articles = build_news_via_gemini(raw_items)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[ok] wrote {len(articles)} articles to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
