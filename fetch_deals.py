#!/usr/bin/env python3
"""
Daily deals fetcher for Zer0 Updates.

1. Pulls recent items from a handful of deal/news RSS feeds.
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
    "https://slickdeals.net/newsearch.php?rss=1&q=&pp=20",
    "https://www.dealnews.com/rss.xml",
]

MAX_ITEMS_PER_FEED = 8
OUTPUT_PATH = "deals.json"
ANTHROPIC_MODEL = "claude-sonnet-4-6"


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
