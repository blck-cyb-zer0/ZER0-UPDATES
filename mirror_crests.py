#!/usr/bin/env python3
"""Keeps a copy of every team badge in /crests so pages don't depend on a third-party CDN at view time.
Safe to run any time: it only downloads badges that are missing, and never fails the build."""
import json, os, time, urllib.request, urllib.parse

DEST = "crests"
try:
    leagues = json.load(open("football/standings.json")).get("leagues", [])
except Exception as ex:
    print("[mirror] no standings:", ex); raise SystemExit(0)

urls = set()
for L in leagues:
    for b in L.get("blocks", []):
        for r in b.get("rows", []):
            u = r.get("crest") or ""
            if u.startswith("https://crests.football-data.org/"): urls.add(u)
os.makedirs(DEST, exist_ok=True)
got = miss = 0
for u in sorted(urls):
    name = os.path.basename(urllib.parse.urlparse(u).path)
    path = os.path.join(DEST, name)
    if os.path.exists(path) and os.path.getsize(path) > 200: continue
    for attempt in range(3):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (zeroupdates.org badge mirror)"})
            data = urllib.request.urlopen(req, timeout=15).read()
            if len(data) > 200:
                open(path, "wb").write(data); got += 1; break
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    else:
        miss += 1
    time.sleep(0.4)
print(f"[mirror] {len(urls)} badges, {got} downloaded, {miss} missed")
