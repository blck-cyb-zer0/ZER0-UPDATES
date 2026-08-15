#!/usr/bin/env python3
"""Fetch trending memes via meme-api.com (no key needed)."""

import json, sys
from datetime import datetime, timezone
import requests

SUBREDDITS = ["memes", "dankmemes", "me_irl", "soccermemes", "footballmemes"]
COUNT_PER_SUB = 15
OUTPUT_PATH = "memes.json"


def fetch_from_subreddit(sub):
    url = f"https://meme-api.com/gimme/{sub}/{COUNT_PER_SUB}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[warn] failed to fetch r/{sub}: {e}", file=sys.stderr)
        return []

    memes = []
    for post in data.get("memes", []):
        if post.get("nsfw") or post.get("spoiler"):
            continue
        memes.append({
            "image": post.get("url", ""),
            "caption": post.get("title", "").strip()[:120],
        })
    return memes


def main():
    all_memes = []
    for sub in SUBREDDITS:
        all_memes.extend(fetch_from_subreddit(sub))

    if not all_memes:
        print("[error] no memes fetched", file=sys.stderr)
        sys.exit(1)

    output = {"generated_at": datetime.now(timezone.utc).isoformat(), "memes": all_memes}
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[ok] wrote {len(all_memes)} memes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
