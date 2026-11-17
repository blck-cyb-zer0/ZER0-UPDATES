#!/usr/bin/env python3
"""Daily Vault suggestions.

Looks on GitHub for well-known open-source apps that are NOT in your Vault yet and sends you a private
Telegram message with the exact line to paste into apps.txt. It never changes your site or your lists.
No message means there was nothing new and safe-looking today.
"""
import datetime, json, os, re, sys
import requests

OWNER_ID = os.environ.get("TELEGRAM_OWNER_ID") or "8419932637"   # your Telegram user id (not a secret)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
STATE = ".suggested_apps.json"
MAX_PER_DAY = 3
MIN_STARS = {"ANDROID": 1500, "WINDOWS": 1500, "LINUX": 1500}
RECENT_DAYS = 120

# What to look for. Edit freely. {d} becomes the "pushed since" date.
QUERIES = {
    "ANDROID": ["topic:android-app stars:>1500 pushed:>{d}", "topic:fdroid stars:>800 pushed:>{d}"],
    "WINDOWS": ["topic:windows topic:open-source stars:>1500 pushed:>{d}", "topic:windows-app stars:>1000 pushed:>{d}"],
    "LINUX": ["topic:linux topic:open-source stars:>1500 pushed:>{d}", "topic:appimage stars:>500 pushed:>{d}"],
}
ASSET_EXT = {
    "ANDROID": (".apk",),
    "WINDOWS": (".exe", ".msi", ".msix", ".zip"),
    "LINUX": (".appimage", ".deb", ".rpm", ".tar.gz", ".tar.xz"),
}
OS_HINT = {"ANDROID": "", "WINDOWS": " os=windows", "LINUX": " os=linux"}
# Keep out anything that could get the site flagged or hurt visitors.
BLOCK = re.compile(r"crack|keygen|serial|warez|pirat|hack|exploit|bypass|cheat|stealer|keylog|ransom|botnet|ddos|"
                   r"carding|spyware|stalker|nsfw|adult|porn|xxx|mod[- ]?apk|premium[- ]?unlock|spoof|spammer|"
                   r"free[- ]?followers|followers[- ]?bot|darkweb|rootkit|payload|trojan|\brat\b", re.I)


def gh(path, params=None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "zer0-vault-suggest"}
    if GH_TOKEN: h["Authorization"] = f"Bearer {GH_TOKEN}"
    r = requests.get("https://api.github.com" + path, params=params, headers=h, timeout=25)
    if r.status_code != 200:
        print(f"[warn] {path} -> {r.status_code}"); return None
    return r.json()


def load(path, default):
    try: return json.load(open(path, encoding="utf-8"))
    except Exception: return default


def known_repos():
    """owner/repo values already in apps.txt or catalog.json (lower case)."""
    out = set()
    try:
        for line in open("apps.txt", encoding="utf-8"):
            m = re.match(r"\s*github:([\w.-]+/[\w.-]+)", line)
            if m: out.add(m.group(1).lower())
    except Exception: pass
    for x in load("catalog.json", []):
        for k in ("url", "homepage", "source"):
            for m in re.finditer(r"github\.com/([\w.-]+/[\w.-]+)", str(x.get(k, ""))):
                out.add(m.group(1).lower())
    return out


def looks_unsafe(repo):
    text = " ".join([repo.get("full_name", ""), repo.get("description") or "", " ".join(repo.get("topics") or [])])
    return bool(BLOCK.search(text))


def good_license(repo):
    lic = (repo.get("license") or {}).get("spdx_id")
    return bool(lic) and lic not in ("NOASSERTION", "NONE")


def pick_asset(assets, cat):
    exts = ASSET_EXT[cat]
    for a in assets or []:
        n = (a.get("name") or "").lower()
        if n.endswith(exts) and not n.endswith((".sha256", ".asc", ".sig")):
            if cat == "WINDOWS" and n.endswith(".zip") and not re.search(r"win|x64|x86|windows", n): continue
            return a["name"]
    return None


def fmt_stars(n):
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def build_message(items):
    lines = [f"New Vault suggestions ({len(items)})", "Nothing is added until you paste a line into apps.txt.", ""]
    for i, c in enumerate(items, 1):
        lines += [f"{i}) {c['name']}  *{fmt_stars(c['stars'])}  {c['license']}  {c['tag']}",
                  f"{c['cat'].title()}: {c['desc']}",
                  f"File: {c['asset']}",
                  f"https://github.com/{c['full']}",
                  f"Add this line:  github:{c['full']}{OS_HINT[c['cat']]}", ""]
    return "\n".join(lines).strip()[:3900]


def send(text):
    if not BOT_TOKEN:
        print("[warn] TELEGRAM_BOT_TOKEN missing; message not sent:\n" + text); return False
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={"chat_id": OWNER_ID, "text": text, "disable_web_page_preview": "true"}, timeout=25)
    if r.status_code != 200:
        print("[warn] Telegram said:", r.status_code, r.text[:200])
        if r.status_code in (400, 403): print("[hint] open your bot in Telegram and send /start so it is allowed to message you")
        return False
    return True


def main():
    state = load(STATE, {"seen": []})
    seen = set(state.get("seen", []))
    have = known_repos()
    since = (datetime.date.today() - datetime.timedelta(days=RECENT_DAYS)).isoformat()
    page = (datetime.date.today().toordinal() % 5) + 1          # a different slice of results each day
    found, tried = [], set()
    for cat, qs in QUERIES.items():
        for q in qs:
            data = gh("/search/repositories", {"q": q.format(d=since), "sort": "stars", "order": "desc", "per_page": 30, "page": page})
            for repo in (data or {}).get("items", []):
                full = repo["full_name"].lower()
                if full in have or full in seen or full in tried: continue
                tried.add(full)
                if repo.get("archived") or repo.get("fork") or repo.get("stargazers_count", 0) < MIN_STARS[cat]: continue
                if not good_license(repo) or looks_unsafe(repo): continue
                rel = gh(f"/repos/{repo['full_name']}/releases/latest")
                asset = pick_asset((rel or {}).get("assets"), cat) if rel else None
                if not asset: continue
                found.append({"full": repo["full_name"], "name": repo["name"], "stars": repo["stargazers_count"],
                              "license": repo["license"]["spdx_id"], "tag": rel.get("tag_name", ""), "cat": cat,
                              "desc": (repo.get("description") or "")[:140], "asset": asset})
                if len(found) >= MAX_PER_DAY * 3: break
    # take a mix: best first, but at most one per category until we run out
    found.sort(key=lambda c: -c["stars"])
    picks, used = [], set()
    for c in found:
        if c["cat"] not in used: picks.append(c); used.add(c["cat"])
    for c in found:
        if len(picks) >= MAX_PER_DAY: break
        if c not in picks: picks.append(c)
    picks = picks[:MAX_PER_DAY]
    if not picks:
        print("Nothing new and safe-looking today."); return
    if send(build_message(picks)):
        state["seen"] = sorted(seen | {c["full"].lower() for c in picks})[-500:]
        json.dump(state, open(STATE, "w", encoding="utf-8"), indent=1)
        print("Sent", len(picks), "suggestions")


if __name__ == "__main__":
    main()
