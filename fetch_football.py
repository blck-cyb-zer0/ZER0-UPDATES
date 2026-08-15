#!/usr/bin/env python3
"""Daily football news fetcher for ZER0 Sports - direct from RSS, no AI needed."""

import json, re, sys
from datetime import datetime, timezone
import feedparser

FEEDS = [
    "https://www.bbc.co.uk/sport/football/rss.xml",
    "https://www.skysports.com/rss/12040",
    "https://sports.yahoo.com/rss/",
]

MAX_ITEMS_PER_FEED = 25
OUTPUT_PATH = "football_news.json"


def clean_html(raw):
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return text.strip()


def fetch_articles():
    articles = []
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

            title = clean_html(entry.get("title", ""))
            summary = clean_html(entry.get("summary", ""))[:200]

            if title and entry.get("link"):
                articles.append({
                    "title": title,
                    "summary": summary,
                    "link": entry.get("link", ""),
                    "image": image,
                })
    return articles


def main():
    articles = fetch_articles()
    if not articles:
        print("[error] no articles fetched", file=sys.stderr)
        sys.exit(1)
    output = {"generated_at": datetime.now(timezone.utc).isoformat(), "articles": articles}
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"[ok] wrote {len(articles)} articles to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
