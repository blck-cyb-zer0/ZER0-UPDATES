#!/usr/bin/env python3
"""Builds football_news.json and news.json (RSS -> Gemini summaries). Never hard-fails."""
import json, os, re, sys, time
from datetime import datetime, timezone
import feedparser, requests

MODEL = "gemini-flash-latest"
JOBS = {
    "football_news.json": {
        "feeds": ["http://feeds.bbci.co.uk/sport/football/rss.xml",
                  "https://www.theguardian.com/football/rss",
                  "https://www.skysports.com/rss/12040"],
        "cats": "Transfer, Match Report, Injury, Rumor, Other", "default": "Football", "words": 60},
    "news.json": {
        "feeds": ["https://techcrunch.com/feed/", "https://www.theverge.com/rss/index.xml",
                  "https://feeds.arstechnica.com/arstechnica/index", "https://www.engadget.com/rss.xml",
                  "http://feeds.bbci.co.uk/news/rss.xml"],
        "cats": "Tech, Business, Science, World, Other", "default": "News", "words": 40},
}
PER_FEED, MAX_ITEMS = 12, 36

def big(u):
    u = re.sub(r"(ichef\.bbci\.co\.uk/(?:ace/standard|ace/ws|news)/)\d+/", r"\g<1>976/", u or "")
    return re.sub(r"(i\.guim\.co\.uk[^ ]*[?&]width=)\d+", r"\g<1>1000", u)

def best_image(e):
    c = []
    for key in ("media_content", "media_thumbnail"):
        for m in e.get(key, []) or []:
            if m.get("url"):
                try: w = int(m.get("width") or 0)
                except ValueError: w = 0
                c.append((w, m["url"]))
    for l in e.get("links", []) or []:
        if l.get("rel") == "enclosure" and str(l.get("type", "")).startswith("image"):
            c.append((0, l.get("href", "")))
    blobs = [x.get("value", "") for x in e.get("content", []) or []] + [e.get("summary", "")]
    for b in blobs:
        for u in re.findall(r'<img[^>]+src=["\']([^"\']+)', b):
            c.append((0, u.replace("&amp;", "&")))
    c = [x for x in c if x[1].startswith("http")]
    return big(max(c, key=lambda x: x[0])[1]) if c else ""

def raw_items(feeds):
    out, seen = [], set()
    for url in feeds:
        try:
            for e in feedparser.parse(url).entries[:PER_FEED]:
                link = e.get("link", "")
                if link and link not in seen:
                    seen.add(link)
                    text = re.sub(r"<[^>]+>", " ", e.get("summary", ""))
                    out.append({"title": e.get("title", "").strip(), "text": " ".join(text.split())[:500],
                                "link": link, "image": best_image(e)})
        except Exception as ex:
            print(f"[warn] {url}: {ex}", file=sys.stderr)
    return out[:MAX_ITEMS]

def gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    for attempt in range(4):
        try:
            r = requests.post(url, headers={"x-goog-api-key": key}, timeout=120, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 12000}})
            if r.status_code == 200:
                txt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                try: return json.loads(txt)
                except ValueError:  # truncated: keep every complete object
                    return json.loads(txt[: txt.rfind("}") + 1] + "]")
            print(f"[warn] gemini {r.status_code}: {r.text[:200]}", file=sys.stderr)
        except Exception as ex:
            print(f"[warn] gemini error: {ex}", file=sys.stderr)
        time.sleep(15 * (attempt + 1))
    return None

def build(path, job):
    raw = raw_items(job["feeds"])
    if not raw:
        print(f"[warn] {path}: no feed items, keeping previous file", file=sys.stderr); return
    listing = [{"i": i, "title": x["title"], "text": x["text"]} for i, x in enumerate(raw)]
    prompt = (f"Rewrite these news items in your own words. Return a JSON array; each element has: "
              f"i (same number as the input), cat (one of: {job['cats']}), title (max 12 words), "
              f"summary (about {job['words']} words, no invented facts). Skip junk items.\n\n" + json.dumps(listing))
    ai = gemini(prompt)
    arts = []
    for a in ai or []:
        try: x = raw[int(a["i"])]
        except (KeyError, ValueError, IndexError, TypeError): continue
        arts.append({"cat": a.get("cat") or job["default"], "title": a.get("title") or x["title"],
                     "summary": a.get("summary") or x["text"], "link": x["link"], "image": x["image"]})
    if not arts:  # Gemini down: publish plain feed text instead of failing
        arts = [{"cat": job["default"], "title": x["title"], "summary": x["text"][:300],
                 "link": x["link"], "image": x["image"]} for x in raw]
    with open(path, "w") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "articles": arts}, f, indent=2)
    print(f"[ok] {path}: {len(arts)} articles, {sum(1 for a in arts if a['image'])} with images")

for p, j in JOBS.items():
    build(p, j)
