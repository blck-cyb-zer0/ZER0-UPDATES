#!/usr/bin/env python3
"""
Daily deals fetcher for Zer0 Updates.

1. Pulls recent items from a deal RSS feed.
2. Sends the raw items to Claude to extract & normalize into clean
   deal entries matching the site's schema.
3. Writes the result to deals.json at the repo root.
"""

import json
import os
import sys
from datetime import datetime, timezone

import feedparser
import requests

FEEDS = [
    "https://www.dealnews.com/?rss=1",
]

MAX_ITEMS_PER_FEED = 20
OUTPUT_PATH = "deals.json"
ANTHROPIC_MODEL = "claude-sonnet-5"


def fetch_raw_items():
    items = []
    for url in FEEDS:
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            print(f"[warn] failed to fetch {url}: {e}", file=sys.stderr)
            continue

        for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
            items.append({
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", "").strip(),
                "link": entry.get("link", ""),
            })

    return items


SCHEMA_INSTRUCTIONS = """You are given a list of raw deal/news headlines and summaries.
Extract up to 9 real, distinct deals from them and return ONLY a JSON array
(no prose, no markdown fences) where each item has exactly these fields:

- cat: short category label, one of: Audio, Software, Outdoors, Courses, Home, Tech, Other
- hot: boolean, true for the 2-3 most compelling deals
- title: short punchy product/deal name (max ~8 words)
- desc: one sentence, no more than 18 words, plain and specific
- now: current price as a number (USD, no $ sign). If unknown, make a reasonable estimate from % off mentioned.
- was: original price as a number (USD). If unknown, estimate consistent with a realistic discount.
- expires: number of days until the deal likely expires (integer, 1-14). If unknown, use 5.

Skip anything that isn't an actual product/service discount (ignore pure news, unrelated posts).
If fewer than 9 genuine deals are present, return fewer items rather than inventing filler.
Return ONLY the JSON array."""


def build_deals_via_claude(raw_items):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    user_content = SCHEMA_INSTRUCTIONS + "\n\nRAW ITEMS:\n" + json.dumps(raw_items, indent=2)

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": user_content}],
        },
        timeout=60,
    )

    print(f"[debug] status={resp.status_code} body={resp.text[:500]}", file=sys.stderr)
    resp.raise_for_status()
    data = resp.json()

    text = "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    ).strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    deals = json.loads(text)
    return deals


def main():
    raw_items = fetch_raw_items()
    if not raw_items:
        print("[error] no raw items fetched from any feed", file=sys.stderr)
        sys.exit(1)

    deals = build_deals_via_claude(raw_items)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "deals": deals,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[ok] wrote {len(deals)} deals to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
