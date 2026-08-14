#!/usr/bin/env python3
"""Daily football news fetcher for ZER0 Sports."""

import json, os, sys
from datetime import datetime, timezone
import feedparser
import requests

FEEDS = [
    "https://www.bbc.co.uk/sport/football/rss.xml",
]

MAX_ITEMS_PER_FEED = 15
OUTPUT_PATH = "football_news.json"
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
            items.append({
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", "").strip(),
                "link": entry.get("link", ""),
                "image": image,
            })
    return items


SCHEMA_INSTRUCTIONS = """You are given raw football news headlines and summaries.
Carry through "link" and "image" unchanged for the matching item.

Select up to 10 items and return ONLY a JSON array (no prose, no markdown fences)
where each item has exactly these fields:
- title: short headline (max 12 words), your own words, not copied verbatim
- summary: 1-2 sentences (max 35 words), your own words, not copied verbatim
- link: exact "link" value from the matching raw item
- image: exact "image" value if present, else empty string

Return ONLY the JSON array."""


def build_via_gemini(raw_items):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    prompt = SCHEMA_INSTRUCTIONS + "\n\nRAW ITEMS:\n" + json.dumps(raw_items, indent=2)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
        timeout=60,
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
        print("[error] no raw items fetched", file=sys.stderr)
        sys.exit(1)
    articles = build_via_gemini(raw_items)
    output = {"generated_at": datetime.now(timezone.utc).isoformat(), "articles": articles}
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"[ok] wrote {len(articles)} articles to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
