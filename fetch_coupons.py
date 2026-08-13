#!/usr/bin/env python3
"""
Daily coupon code fetcher for Zer0 Updates.

1. Pulls recent items from deal/coupon RSS feeds.
2. Sends raw items to Gemini to extract genuine coupon/promo codes only.
3. Writes result to coupons.json at the repo root.
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
OUTPUT_PATH = "coupons.json"
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
            items.append({
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", "").strip(),
                "link": entry.get("link", ""),
            })

    return items


SCHEMA_INSTRUCTIONS = """You are given a list of raw deal headlines and summaries.
Extract ONLY items that mention an actual promo/coupon code (a specific code text
a shopper would enter at checkout). Skip anything that's just a plain price
discount with no code.

Return ONLY a JSON array (no prose, no markdown fences) where each item has
exactly these fields:

- store: the store/retailer name
- code: the coupon code text (if genuinely present in the source; if the source
  only implies "use code at checkout" without giving the actual code, skip that item)
- desc: one short sentence describing what the code gets you (max 18 words)
- discount: short label like "20% off" or "$10 off" (string)
- expires: number of days until likely expiry (integer, 1-14). If unknown, use 5.
- link: the exact "link" value from the matching raw item (string, do not modify)

If no items contain genuine coupon codes, return an empty array.
Return ONLY the JSON array."""


def build_coupons_via_gemini(raw_items):
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
        print("[error] no raw items fetched from any feed", file=sys.stderr)
        sys.exit(1)

    coupons = build_coupons_via_gemini(raw_items)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coupons": coupons,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[ok] wrote {len(coupons)} coupons to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

