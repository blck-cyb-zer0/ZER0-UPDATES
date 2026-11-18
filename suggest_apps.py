#!/usr/bin/env python3
"""Daily Vault suggestions.

Looks for open-source apps that are NOT in your Vault yet, on several sites:
  - GitHub search (Android, Windows, Linux apps)
  - F-Droid (newly added open-source Android apps)
  - Scoop (a curated list of Windows tools) and AppImageHub (a curated list of Linux apps), checked on GitHub
Then sends you a private Telegram message with the exact line to paste into apps.txt.
It never changes your site or your lists. Add the safety rules or sources you want near the top.
"""
import collections, datetime, json, os, random, re
import requests

OWNER_ID = os.environ.get("TELEGRAM_OWNER_ID") or "8419932637"   # your Telegram user id (not a secret)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
MANUAL_RUN = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
STATE = ".suggested_apps.json"
MAX_PER_DAY = 5
RECENT_DAYS = 365                  # GitHub projects must have been updated within this many days
FDROID_NEW_DAYS = 60               # F-Droid apps added within this many days
USE_IZZY = False                   # set True to also watch IzzyOnDroid (a bigger download)
MIN_STARS = 300                    # for GitHub search results; curated lists only need MIN_STARS_CURATED
MIN_STARS_CURATED = 100

QUERIES = {
    "ANDROID": ["topic:android-app stars:>{s} pushed:>{d}", "topic:fdroid stars:>{s} pushed:>{d}"],
    "WINDOWS": ["topic:windows topic:open-source stars:>{s} pushed:>{d}", "topic:windows-app stars:>{s} pushed:>{d}"],
    "LINUX": ["topic:linux topic:open-source stars:>{s} pushed:>{d}", "topic:appimage stars:>{s} pushed:>{d}"],
}
ASSET_EXT = {"ANDROID": (".apk",), "WINDOWS": (".exe", ".msi", ".msix", ".zip", ".7z"),
             "LINUX": (".appimage", ".deb", ".rpm", ".tar.gz", ".tar.xz")}
OS_HINT = {"ANDROID": "", "WINDOWS": " os=windows", "LINUX": " os=linux"}
# Words that keep a project out (matched on the name and description as whole words, and on topics exactly).
BLOCK_WORDS = re.compile(r"\b(crack|cracked|keygen|warez|pirated?|piracy|exploit|exploits|bypass|cheat|cheats|stealer|keylogger|"
                         r"ransomware|botnet|ddos|carding|spyware|stalkerware|nsfw|porn|xxx|mod[- ]?apk|spoofer|spammer|"
                         r"rootkit|trojan|rat|darkweb|followers[- ]?bot|free[- ]?followers|hacking[- ]?tool|hacktool)\b", re.I)
BLOCK_TOPICS = {"hacking", "hacking-tools", "exploit", "keylogger", "malware", "ransomware", "ddos", "crack", "warez", "pentest-tools", "nsfw"}
FDROID_BAD_FLAGS = {"NonFreeNet", "NonFreeAdd", "NonFreeAssets", "NonFreeDep", "Tracking", "UpstreamNonFree"}

why = collections.Counter()        # why candidates were skipped
errors = []                        # failed requests (shown in the Telegram report when nothing is found)
search_counts = {}                 # how many results each GitHub search returned
NOTIFY_WHEN_EMPTY = True           # message you even when nothing is found, with the reasons (set False once it is working)


def get_json(url, params=None, headers=None, timeout=30):
    h = {"User-Agent": "zer0-vault-suggest"}
    h.update(headers or {})
    r = requests.get(url, params=params, headers=h, timeout=timeout)
    if r.status_code != 200:
        print(f"[warn] {url.split('?')[0][:80]} -> {r.status_code}"); why[f"source error {r.status_code}"] += 1
        errors.append(f"{r.status_code} {url.split('?')[0].replace('https://', '')[:70]}")
        return None
    return r.json()


def gh(path, params=None):
    h = {"Accept": "application/vnd.github+json"}
    if GH_TOKEN: h["Authorization"] = f"Bearer {GH_TOKEN}"
    return get_json("https://api.github.com" + path, params, h)


def load(path, default):
    try: return json.load(open(path, encoding="utf-8"))
    except Exception: return default


def known():
    """Everything already in apps.txt or the catalog, as lower-case keys like 'github:owner/repo' or 'fdroid:pkg'."""
    out = set()
    try:
        for line in open("apps.txt", encoding="utf-8"):
            m = re.match(r"\s*(github|fdroid|izzy|pypi):([\w./-]+)", line)
            if m: out.add(f"{m.group(1)}:{m.group(2)}".lower())
    except Exception: pass
    for x in load("catalog.json", []):
        for k in ("url", "homepage", "source"):
            for m in re.finditer(r"github\.com/([\w.-]+/[\w.-]+)", str(x.get(k, ""))): out.add("github:" + m.group(1).lower())
    return out


def unsafe(name, desc, topics=()):
    if BLOCK_WORDS.search(f"{name} {desc}"): return True
    return any(t in BLOCK_TOPICS for t in (topics or []))


def good_license(spdx):
    return bool(spdx) and str(spdx).upper() not in ("NOASSERTION", "NONE", "OTHER", "UNKNOWN", "")


def pick_asset(assets, cat):
    for a in assets or []:
        n = (a.get("name") or "").lower()
        if not n.endswith(ASSET_EXT[cat]): continue
        if cat == "WINDOWS" and n.endswith((".zip", ".7z")) and not re.search(r"win|x64|x86|windows", n): continue
        return a["name"]
    return None


def fmt_stars(n):
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def check_repo(full, cat, min_stars, source):
    """GitHub checks shared by every source -> candidate dict or None."""
    repo = gh(f"/repos/{full}")
    if not repo: return None
    if repo.get("archived") or repo.get("fork"): why["archived or fork"] += 1; return None
    if repo.get("stargazers_count", 0) < min_stars: why["too few stars"] += 1; return None
    lic = (repo.get("license") or {}).get("spdx_id")
    if not good_license(lic): why["no clear license"] += 1; return None
    if unsafe(repo["full_name"], repo.get("description") or "", repo.get("topics")): why["blocked words"] += 1; return None
    rel = gh(f"/repos/{repo['full_name']}/releases/latest")
    asset = pick_asset((rel or {}).get("assets"), cat) if rel else None
    if not asset: why["no download file in latest release"] += 1; return None
    return {"key": f"github:{repo['full_name'].lower()}", "line": f"github:{repo['full_name']}{OS_HINT[cat]}", "name": repo["name"], "cat": cat,
            "desc": (repo.get("description") or "")[:140], "meta": f"*{fmt_stars(repo['stargazers_count'])}  {lic}  {rel.get('tag_name', '')}",
            "file": asset, "link": f"https://github.com/{repo['full_name']}", "source": source}


# ------------------------------------------------------------------ sources
def src_github_search(have, seen, today):
    out, tried = [], set()
    since = (today - datetime.timedelta(days=RECENT_DAYS)).isoformat()
    page = (today.toordinal() % 5) + 1                 # a different slice of the results each day
    for cat, qs in QUERIES.items():
        for q in qs:
            data = gh("/search/repositories", {"q": q.format(s=MIN_STARS, d=since), "sort": "stars", "order": "desc", "per_page": 30, "page": page})
            search_counts[q.split(" stars")[0]] = len((data or {}).get("items", []))
            for repo in (data or {}).get("items", []):
                key = "github:" + repo["full_name"].lower()
                if key in have or key in seen or key in tried: why["already known or suggested"] += 1; continue
                tried.add(key)
                if unsafe(repo["full_name"], repo.get("description") or "", repo.get("topics")): why["blocked words"] += 1; continue
                c = check_repo(repo["full_name"], cat, MIN_STARS, "GitHub")
                if c: out.append(c)
    return out


def loc(value):
    if isinstance(value, dict) and value:
        for k in ("en-US", "en", "en-GB"):
            if k in value: return value[k]
        return next(iter(value.values()))
    return value if isinstance(value, str) else ""


def src_fdroid(have, seen, today, base="https://f-droid.org/repo", tag="F-Droid", prefix="fdroid"):
    """Newly added open-source Android apps from an F-Droid style repository (index-v2 format)."""
    data = get_json(base + "/index-v2.json", timeout=240)
    out = []
    packages = (data or {}).get("packages") or {}
    if data is not None and not packages: errors.append(f"{tag}: index had no packages (format changed?)")
    cutoff = (today - datetime.timedelta(days=FDROID_NEW_DAYS)).toordinal()
    for pkg, entry in packages.items():
        meta = entry.get("metadata") or {}
        added = meta.get("added")
        if not added: continue
        if datetime.date.fromtimestamp(added / 1000).toordinal() < cutoff: continue
        key = f"{prefix}:{pkg}".lower()
        if key in have or key in seen: why["already known or suggested"] += 1; continue
        name, desc = loc(meta.get("name")) or pkg, loc(meta.get("summary"))
        lic = meta.get("license")
        if not good_license(lic): why["no clear license"] += 1; continue
        flags = set()
        for v in (entry.get("versions") or {}).values(): flags |= set((v.get("antiFeatures") or {}).keys())
        if FDROID_BAD_FLAGS & flags: why["F-Droid anti-feature flag"] += 1; continue
        if unsafe(name, desc): why["blocked words"] += 1; continue
        out.append({"key": key, "line": f"{prefix}:{pkg}", "name": name, "cat": "ANDROID", "desc": desc[:140],
                    "meta": f"{lic}  new on {tag}", "file": "APK", "link": meta.get("webSite") or meta.get("sourceCode") or f"https://f-droid.org/packages/{pkg}/", "source": tag})
    return out


def sample(items, n, today):
    rnd = random.Random(today.toordinal())
    items = list(items); rnd.shuffle(items)
    return items[:n]


def src_scoop(have, seen, today):
    """Scoop's Main bucket is a curated list of Windows tools. We look at a daily sample and check each on GitHub."""
    listing = gh("/repos/ScoopInstaller/Main/contents/bucket")
    out = []
    for item in sample([i["name"] for i in (listing or []) if i.get("name", "").endswith(".json")], 14, today):
        m = get_json(f"https://raw.githubusercontent.com/ScoopInstaller/Main/master/bucket/{item}")
        if not m: continue
        blob = (m.get("homepage") or "") + " " + json.dumps(m.get("checkver", "")) + " " + json.dumps(m.get("url", ""))
        g = re.search(r"github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?(?:[/\"'\s]|$)", blob)
        if not g: why["Scoop entry without a GitHub project"] += 1; continue
        key = "github:" + g.group(1).lower()
        if key in have or key in seen: why["already known or suggested"] += 1; continue
        c = check_repo(g.group(1), "WINDOWS", MIN_STARS_CURATED, "Scoop list")
        if c: out.append(c)
    return out


def src_appimage(have, seen, today):
    """AppImageHub is a curated list of Linux apps. We look at a daily sample and check each on GitHub."""
    data = get_json("https://appimage.github.io/feed.json", timeout=60)
    out = []
    items = [i for i in (data or {}).get("items", []) if any((l.get("type") or "").lower() == "github" for l in i.get("links") or [])]
    for it in sample(items, 14, today):
        link = next(l["url"] for l in it["links"] if (l.get("type") or "").lower() == "github")
        g = re.search(r"([\w.-]+/[\w.-]+)$", str(link).replace("https://github.com/", "").strip("/"))
        if not g: continue
        key = "github:" + g.group(1).lower()
        if key in have or key in seen: why["already known or suggested"] += 1; continue
        c = check_repo(g.group(1), "LINUX", MIN_STARS_CURATED, "AppImageHub")
        if c: out.append(c)
    return out


# ------------------------------------------------------------------ message
def build_message(items):
    lines = [f"New Vault suggestions ({len(items)})", "Nothing is added until you paste a line into apps.txt.", ""]
    for i, c in enumerate(items, 1):
        lines += [f"{i}) {c['name']}  {c['meta']}", f"{c['cat'].title()} (found on {c['source']}): {c['desc']}".strip(),
                  f"File: {c['file']}", c["link"], f"Add this line:  {c['line']}", ""]
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
    seen = {s.lower() for s in state.get("seen", [])}
    have, today = known(), datetime.date.today()
    sources = [("GitHub search", src_github_search), ("F-Droid", src_fdroid), ("Scoop", src_scoop), ("AppImageHub", src_appimage)]
    if USE_IZZY:
        sources.append(("IzzyOnDroid", lambda h, s, t: src_fdroid(h, s, t, "https://apt.izzysoft.de/fdroid/repo", "IzzyOnDroid", "izzy")))
    per_source = {}
    for name, fn in sources:
        try: per_source[name] = fn(have, seen, today)
        except Exception as ex:
            print(f"[warn] {name} failed: {ex}"); why[f"{name} crashed"] += 1; per_source[name] = []
        print(f"{name}: {len(per_source[name])} candidates")
    # round-robin so one site cannot fill the whole message, strongest first inside each site
    picks, used = [], set()
    queues = [sorted(v, key=lambda c: c["name"].lower()) for v in per_source.values() if v]
    while queues and len(picks) < MAX_PER_DAY:
        for q in list(queues):
            while q and q[0]["key"] in used: q.pop(0)
            if q and len(picks) < MAX_PER_DAY:
                c = q.pop(0); picks.append(c); used.add(c["key"])
            if not q: queues.remove(q)
    summary = "; ".join(f"{k}: {v}" for k, v in why.most_common()) or "nothing skipped"
    print("Skipped ->", summary)
    if not picks:
        print("Nothing new and safe-looking today.")
        if NOTIFY_WHEN_EMPTY or MANUAL_RUN:
            rl = gh("/rate_limit")
            core = ((rl or {}).get("resources") or {}).get("search") or {}
            send("No new Vault suggestions this time.\n"
                 "Candidates per site: " + ", ".join(f"{k} {len(v)}" for k, v in per_source.items()) + "\n"
                 "GitHub searches returned: " + (", ".join(f"{k}={v}" for k, v in search_counts.items()) or "none ran") + "\n"
                 f"GitHub token: {'yes' if GH_TOKEN else 'NO'}; search limit left: {core.get('remaining', '?')}\n"
                 f"Skipped: {summary}\n"
                 "Problems: " + ("; ".join(errors[:6]) if errors else "none"))
        return
    if send(build_message(picks)):
        state["seen"] = sorted(seen | {c["key"] for c in picks})[-600:]
        json.dump(state, open(STATE, "w", encoding="utf-8"), indent=1)
        print("Sent", len(picks), "suggestions")


if __name__ == "__main__":
    main()
