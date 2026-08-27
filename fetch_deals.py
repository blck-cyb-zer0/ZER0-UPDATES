#!/usr/bin/env python3
"""
Daily deals fetcher for Zer0 Updates.
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

MAX_ITEMS_PER_FEED = 35
OUTPUT_PATH = "deals.json"
GROQ_MODEL = "openai/gpt-oss-120b"
AMAZON_AFFILIATE_TAG = "zer0updates20"


def add_affiliate_tag(url):
    """If the link points to an Amazon product page, append our affiliate tag."""
    if not url:
        return url

    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(url)
    if "amazon." not in parsed.netloc:
        return url  # not an Amazon link, leave untouched

    query = parse_qs(parsed.query)
    query["tag"] = [AMAZON_AFFILIATE_TAG]  # overwrite/insert our tag
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


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
            elif "links" in entry:
                for l in entry.links:
                    if l.get("type", "").startswith("image"):
                        image = l.get("href", "")
                        break

            items.append({
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", "").strip(),
                "link": entry.get("link", ""),
                "image": image,
            })

    return items


SCHEMA_INSTRUCTIONS = """You are given a list of raw deal/news headlines and summaries.
Each raw item includes a "link" and possibly an "image" URL — you MUST carry these
through unchanged into your output for the matching deal.

Extract up to 9 real, distinct deals from them and return ONLY a JSON array
(no prose, no markdown fences) where each item has exactly these fields:

- cat: short category label, one of: Audio, Software, Outdoors, Courses, Home, Tech, Other
- hot: boolean, true for the 2-3 most compelling deals
- title: short punchy product/deal name (max ~8 words)
- desc: one sentence, no more than 18 words, plain and specific
- now: current price as a number (USD, no $ sign). If unknown, make a reasonable estimate from % off mentioned.
- was: original price as a number (USD). If unknown, estimate consistent with a realistic discount.
- expires: number of days until the deal likely expires (integer, 1-14). If unknown, use 5.
- link: the exact "link" value from the matching raw item (string, do not modify).
- image: the exact "image" value from the matching raw item if present, otherwise an empty string.

Skip anything that isn't an actual product/service discount (ignore pure news, unrelated posts).
If fewer than 9 genuine deals are present, return fewer items rather than inventing filler.
Return ONLY the JSON array."""


def build_deals_via_groq(raw_items):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    prompt = SCHEMA_INSTRUCTIONS + "\n\nRAW ITEMS:\n" + json.dumps(raw_items, indent=2)

    url = "https://api.groq.com/openai/v1/chat/completions"

    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        },
        timeout=60,
    )

    print(f"[debug] status={resp.status_code} body={resp.text[:500]}", file=sys.stderr)
    resp.raise_for_status()
    data = resp.json()

    text = data["choices"][0]["message"]["content"].strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    deals = json.loads(text)
    return deals

FEATURED_AMAZON_DEAL = {
    "cat": "Tech",
    "hot": True,
    "title": "ZER0 Picks: Todays Amazon Deals",
    "desc": "Browse todays top discounts on Amazon, hand-picked daily.",
    "now": 0,
    "was": 0,
    "expires": 1,
    "link": "https://www.amazon.com/deals?tag=zer0updates20",
    "image": "",
}


def main():
    raw_items = fetch_raw_items()
    if not raw_items:
        print("[error] no raw items fetched from any feed", file=sys.stderr)
        sys.exit(1)

    deals = build_deals_via_groq(raw_items)
    deals.insert(0, FEATURED_AMAZON_DEAL)

    # Apply our Amazon affiliate tag to any Amazon links
    for deal in deals:
        if "link" in deal:
            deal["link"] = add_affiliate_tag(deal["link"])

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "deals": deals,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[ok] wrote {len(deals)} deals to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
