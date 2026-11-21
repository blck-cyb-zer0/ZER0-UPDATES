#!/usr/bin/env python3
"""Pulls the awesome-selfhosted list (official open data) into assets/selfhosted.json.

Source : https://github.com/awesome-selfhosted/awesome-selfhosted-data  (the data behind awesome-selfhosted.net)
License: CC BY-SA 3.0 - you may reuse it with credit, under the same license. The page that shows it gives that credit.
Run    : python fetch_selfhosted.py        (needs: pip install requests pyyaml)
It only writes the file if it parsed a sensible number of projects, so a bad download never wipes a good directory.
"""
import collections, datetime, io, json, os, re, sys, tarfile

import requests
import yaml

TARBALL = "https://api.github.com/repos/awesome-selfhosted/awesome-selfhosted-data/tarball"
OUT = "assets/selfhosted.json"
NOTICE = "assets/selfhosted-LICENSE.txt"
MIN_EXPECTED = 300

# Projects whose main purpose is copying copyrighted media are left out, to keep the site safe for ad networks.
# Edit freely; matched against the name and description.
HIDE = re.compile(r"(?i)\b(library genesis|libgen|spotify|youtube[- ]?dl|yt-dlp|torrent indexer|dht crawler|"
                  r"download(?:s|er)? (?:video|audio|music|videos)|video and audio downloader|roms?\b|crack(?:ed)?|keygen|warez|"
                  r"pirat\w*|stremio addon|usenet indexer)\b")


def clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def as_list(v):
    if v is None: return []
    return [clean(x) for x in v] if isinstance(v, (list, tuple)) else [clean(v)]


def parse(d):
    """One software .yml -> compact dict, or None if it is unusable."""
    if not isinstance(d, dict): return None
    name, desc = clean(d.get("name")), clean(d.get("description"))
    if not name or not desc: return None
    return {
        "n": name, "d": desc,
        "w": clean(d.get("website_url")), "s": clean(d.get("source_code_url")), "demo": clean(d.get("demo_url")),
        "l": as_list(d.get("licenses")), "p": as_list(d.get("platforms")), "t": as_list(d.get("tags")),
        "st": int(d.get("stargazers_count") or 0) if str(d.get("stargazers_count") or "0").isdigit() else 0,
        "u": clean(d.get("updated_at") or d.get("last_updated") or ""),
        "af": 1 if d.get("depends_3rdparty") else 0,
    }


def load_items(tar_bytes):
    items, skipped = [], collections.Counter()
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tf:
        for m in tf.getmembers():
            if not (m.isfile() and re.search(r"/software/[^/]+\.ya?ml$", m.name)): continue
            try:
                item = parse(yaml.safe_load(tf.extractfile(m).read().decode("utf-8", "replace")))
            except Exception:
                skipped["unreadable file"] += 1; continue
            if not item: skipped["missing name or description"] += 1; continue
            if HIDE.search(item["n"] + " " + item["d"]): skipped["left out (copyrighted-media downloaders)"] += 1; continue
            items.append(item)
    items.sort(key=lambda i: (-i["st"], i["n"].lower()))
    return items, skipped


def main():
    h = {"User-Agent": "zer0-selfhosted-import", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"): h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    print("Downloading the list...")
    r = requests.get(TARBALL, headers=h, timeout=180)
    if r.status_code != 200:
        print("Download failed:", r.status_code, r.text[:200]); sys.exit(1)
    items, skipped = load_items(r.content)
    print(f"Parsed {len(items)} projects. Skipped: {dict(skipped) or 'none'}")
    if len(items) < MIN_EXPECTED:
        print(f"Only {len(items)} projects found (expected {MIN_EXPECTED}+). The data format may have changed, so nothing was written.")
        sys.exit(1)
    tags = collections.Counter(t for i in items for t in i["t"])
    print("Top categories:", tags.most_common(5))
    os.makedirs("assets", exist_ok=True)
    meta = {"source": "https://github.com/awesome-selfhosted/awesome-selfhosted-data", "site": "https://awesome-selfhosted.net",
            "license": "CC BY-SA 3.0", "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
            "generated": datetime.date.today().isoformat(), "count": len(items),
            "changes": "Reformatted into one JSON file, a few projects left out, sorted by stars."}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "items": items}, f, ensure_ascii=False, separators=(",", ":"))
    open(NOTICE, "w", encoding="utf-8").write(
        "selfhosted.json is derived from awesome-selfhosted-data (https://github.com/awesome-selfhosted/awesome-selfhosted-data),\n"
        "(c) the awesome-selfhosted contributors, licensed CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/).\n"
        "Changes: reformatted into a single JSON file, a few projects left out, sorted by stars.\n"
        "This file is shared under the same license (CC BY-SA 3.0).\n")
    print(f"Wrote {OUT} ({os.path.getsize(OUT)//1024} KB)")


if __name__ == "__main__":
    main()
