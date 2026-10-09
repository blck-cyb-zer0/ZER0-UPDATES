#!/usr/bin/env python3
"""
Daily news fetcher for Zer0 Updates.
Uses Groq (OpenAI-compatible API) instead of Gemini for rewriting/categorizing.
"""

import json
import os
import re
import sys
import time
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

MAX_ITEMS_PER_FEED = 20
OUTPUT_PATH = "news.json"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_best_image(entry):
    """Prefer the largest real image available; media_thumbnail is usually
    a small icon, so it's used only as a last-resort fallback."""
    candidates = []
    if "media_content" in entry and entry.media_content:
        for m in entry.media_content:
            url = m.get("url", "")
            if not url:
                continue
            try:
                width = int(m.get("width", 0))
            except (TypeError, ValueError):
                width = 0
            candidates.append((width, url))
    if candidates:
        candidates.sort(key=lambda c: c[0], reverse=True)
        return candidates[0][1]

    html_fields = []
    if "content" in entry and entry.content:
        html_fields.append(entry.content[0].get("value", ""))
    if entry.get("summary"):
        html_fields.append(entry.get("summary", ""))
    for html in html_fields:
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        if match:
            return match.group(1)

    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and link.get("type", "").startswith("image"):
            return link.get("href", "")

    if "media_thumbnail" in entry and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")

    return ""


def fetch_raw_items():
    items = []
    for url in FEEDS:
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            print(f"[warn] failed to fetch {url}: {e}", file=sys.stderr)
            continue

        for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
            image = extract_best_image(entry)

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
Return ONLY the JSON array, nothing else — no markdown fences, no explanation."""


def call_groq_with_retry(payload, headers, timeout, max_retries=5, base_delay=5, max_total_seconds=180):
    """Call the Groq API, retrying on transient server errors with
    exponential backoff, bounded by both attempt count and a total
    time budget so a slow run can't drag on forever."""
    last_exc = None
    start = time.monotonic()
    for attempt in range(1, max_retries + 1):
        elapsed = time.monotonic() - start
        if elapsed >= max_total_seconds:
            print(f"[warn] Groq retry time budget ({max_total_seconds}s) exceeded, giving up.", file=sys.stderr)
            break
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.exceptions.HTTPError(f"{resp.status_code} server error", response=resp)
            resp.raise_for_status()
            return resp
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_exc = e
            if attempt == max_retries:
                break
            delay = base_delay * (2 ** (attempt - 1))
            print(f"[warn] Groq call failed (attempt {attempt}/{max_retries}, {elapsed:.0f}s elapsed): {e}. Retrying in {delay}s...", file=sys.stderr)
            time.sleep(delay)
    raise last_exc


def build_news_via_groq(raw_items):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    prompt = SCHEMA_INSTRUCTIONS + "\n\nRAW ITEMS:\n" + json.dumps(raw_items, indent=2)

    resp = call_groq_with_retry(
        payload={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8000,
            "temperature": 0.4,
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        timeout=100,
    )

    print(f"[debug] status={resp.status_code} body={resp.text[:500]}", file=sys.stderr)
    data = resp.json()

    text = data["choices"][0]["message"]["content"].strip()

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

    articles = build_news_via_groq(raw_items)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[ok] wrote {len(articles)} articles to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
