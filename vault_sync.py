#!/usr/bin/env python3
"""Run once after unpacking an update:   python vault_sync.py
Makes catalog.json match the Vault's scripts:
  - gives every ZERO script the accurate one-line description used on its guide page
  - adds any ZERO script that is not in the catalog yet (the file is served from zeroupdates.org/files/)
Entries added by hand are kept by the daily app update, so this is a one-off. Safe to run again any time."""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_downloads import TOOLS, SITE

CATALOG = "catalog.json"
norm = lambda x: re.sub(r"[^a-z0-9]", "", str(x).lower())


def human(n):
    return f"{n/1024:.1f} KB" if n >= 1024 else f"{n} B"


def main():
    cat = json.load(open(CATALOG, encoding="utf-8"))
    by = {norm(x.get("title")): x for x in cat}
    updated, added = [], []
    for t in TOOLS:
        keys = [norm(t["name"])] + ([norm(t["src"])] if t.get("src") else [])
        entry = next((by[k] for k in keys if k in by), None)
        if entry:
            if entry.get("description") != t["short"]:
                entry["description"] = t["short"]; updated.append(t["name"])
        elif t.get("file") and os.path.exists(t["file"]):
            cat.append({"title": t["src"], "category": "TOOLS", "tag": "SCRIPT", "version": "1.0",
                        "description": t["short"], "url": f"{SITE}/{t['file']}", "size": human(os.path.getsize(t["file"]))})
            added.append(t["name"])
    if updated or added:
        with open(CATALOG, "w", encoding="utf-8") as f:
            json.dump(cat, f, indent=2, ensure_ascii=False); f.write("\n")
    print(f"descriptions updated: {len(updated)}  scripts added: {len(added)}")
    for n in added: print("  + " + n)
    if not (updated or added): print("catalog.json already up to date")


if __name__ == "__main__":
    main()
