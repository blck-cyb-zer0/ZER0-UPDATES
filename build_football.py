#!/usr/bin/env python3
"""Fetches tables, fixtures and results (football-data.org) and builds static pages at football/<league>/."""
import html, json, os, sys, time
from datetime import datetime, timezone
import requests

SITE = "https://zeroupdates.org"
LEAGUES = [("PL", "premier-league", "Premier League"), ("CL", "champions-league", "UEFA Champions League"),
           ("PD", "la-liga", "La Liga"), ("BL1", "bundesliga", "Bundesliga"), ("SA", "serie-a", "Serie A"), ("FL1", "ligue-1", "Ligue 1")]
NOW = datetime.now(timezone.utc)
D, NICE = NOW.strftime("%Y-%m-%d"), NOW.strftime("%d %B %Y").lstrip("0")
e = lambda x: html.escape(str(x if x is not None else ""), quote=True)

def get(path):
    key = os.environ.get("FOOTBALL_API_KEY")
    if not key: return None
    for _ in range(2):
        try:
            r = requests.get("https://api.football-data.org/v4/" + path, headers={"X-Auth-Token": key}, timeout=30)
            if r.status_code == 200: return r.json()
            print(f"[warn] {path} -> {r.status_code}", file=sys.stderr)
            if r.status_code != 429: return None
            time.sleep(62)
        except Exception as ex:
            print(f"[warn] {path}: {ex}", file=sys.stderr); return None
    return None

def when(m):
    try: return datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).strftime("%a %d %b, %H:%M UTC")
    except Exception: return ""

ZONES = {
    "PL": [(1, 4, "ucl", "Champions League"), (5, 5, "uel", "Europa League"), (6, 6, "uecl", "Conference League"), (18, 20, "rel", "Relegation")],
    "PD": [(1, 4, "ucl", "Champions League"), (5, 6, "uel", "Europa League"), (7, 7, "uecl", "Conference League"), (18, 20, "rel", "Relegation")],
    "SA": [(1, 4, "ucl", "Champions League"), (5, 5, "uel", "Europa League"), (6, 6, "uecl", "Conference League"), (18, 20, "rel", "Relegation")],
    "BL1": [(1, 4, "ucl", "Champions League"), (5, 5, "uel", "Europa League"), (6, 6, "uecl", "Conference League"), (16, 16, "po", "Relegation play-off"), (17, 18, "rel", "Relegation")],
    "FL1": [(1, 3, "ucl", "Champions League"), (4, 4, "uel", "Europa League"), (5, 5, "uecl", "Conference League"), (16, 16, "po", "Relegation play-off"), (17, 18, "rel", "Relegation")],
    "CL": [(1, 8, "ucl", "Round of 16"), (9, 24, "po", "Knockout play-offs"), (25, 36, "rel", "Eliminated")],
}

def zone_of(code, pos):
    for a, b, cls, label in ZONES.get(code, []):
        try:
            if a <= int(pos) <= b: return cls
        except (TypeError, ValueError): pass
    return ""

def legend(code):
    seen, out = set(), []
    for a, b, cls, label in ZONES.get(code, []):
        if cls not in seen:
            seen.add(cls); out.append(f'<span class="lg z-{cls}"><i></i>{e(label)}</span>')
    if not out: return ""
    return ('<p class="legend">' + "".join(out) + '</p><p class="m">Colours show the usual qualification and relegation places. '
            'They can change with cup winners and European results.</p>')

def form(t):
    f = [x for x in str(t.get("form") or "").replace(" ", "").split(",") if x in ("W", "D", "L")][-5:]
    return "".join(f'<i class="f f{x}">{x}</i>' for x in f)

def table(block, code=""):
    rows = ""
    for t in block.get("table", []):
        z = zone_of(code, t.get("position"))
        rows += (f'<tr class="z z-{z}">' if z else "<tr>") + (
            f'<td>{e(t.get("position"))}</td><td class="tn">{e(t["team"].get("shortName") or t["team"].get("name"))}</td>'
            f'<td>{e(t.get("playedGames"))}</td><td>{e(t.get("won"))}</td><td>{e(t.get("draw"))}</td><td>{e(t.get("lost"))}</td>'
            f'<td>{e(t.get("goalsFor"))}</td><td>{e(t.get("goalsAgainst"))}</td><td>{e(t.get("goalDifference"))}</td>'
            f'<td><strong>{e(t.get("points"))}</strong></td><td class="fm">{form(t)}</td></tr>')
    head = f'<h3>{e(block["group"].replace("_", " ").title())}</h3>' if block.get("group") else ""
    return (head + '<div class="tw"><table><tr><th>#</th><th class="tn">Team</th><th>P</th><th>W</th><th>D</th><th>L</th>'
            '<th>GF</th><th>GA</th><th>GD</th><th>Pts</th><th>Form</th></tr>' + rows + "</table></div>")

def fixtures(ms, scored):
    def line(m):
        h, a = m["homeTeam"].get("shortName") or m["homeTeam"].get("name"), m["awayTeam"].get("shortName") or m["awayTeam"].get("name")
        ft = (m.get("score") or {}).get("fullTime") or {}
        mid = f'{ft.get("home")} - {ft.get("away")}' if scored and ft.get("home") is not None else "vs"
        return f'<li><span class="m">{e(when(m))}</span><br><strong>{e(h)}</strong> {e(mid)} <strong>{e(a)}</strong></li>'
    return "<ul>" + "".join(line(m) for m in ms) + "</ul>" if ms else "<p class='m'>Nothing to show right now.</p>"

CSS = """:root{--bg:#f4f7fc;--card:#fff;--ink:#0a1a3f;--mut:#5b6785;--line:#e3e8f3;--hi:#2f6bff}
@media(prefers-color-scheme:dark){:root{--bg:#0b0f1a;--card:#131a2b;--ink:#eef2ff;--mut:#9aa6c4;--line:#222c45;--hi:#4d8dff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 Inter,system-ui,sans-serif}
header{background:#05050a;padding:10px 16px}header a{display:inline-flex;align-items:center;gap:8px;line-height:0}header img{height:30px}header .w{height:13px}
main{max-width:760px;margin:0 auto;padding:22px 16px 50px}h1{font:700 27px/1.2 Poppins,Inter,sans-serif;margin:6px 0}h2{margin:26px 0 8px}h3{margin:14px 0 4px}
table{width:100%;border-collapse:collapse;font-size:14px}td,th{border:1px solid var(--line);padding:6px 8px;text-align:left;background:var(--card)}
ul{padding-left:18px}li{margin:8px 0}.m{color:var(--mut);font-size:14px}a{color:var(--hi)}
.tw{overflow-x:auto}td.tn,th.tn{position:sticky;left:0;font-weight:600;white-space:nowrap}td,th{white-space:nowrap}th{background:var(--card)}
tr.z td{background:color-mix(in srgb,var(--z) 13%,var(--card))}tr.z td:first-child{border-left:4px solid var(--z)}
.z-ucl{--z:#2f6bff}.z-uel{--z:#f59e0b}.z-uecl{--z:#14b8a6}.z-po{--z:#a855f7}.z-rel{--z:#ef4444}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;margin:10px 0 4px;font-size:13px}.lg{display:inline-flex;align-items:center;gap:6px}
.lg i{width:12px;height:12px;border-radius:3px;background:var(--z);display:inline-block}
.f{font-style:normal;display:inline-block;width:19px;height:19px;line-height:19px;text-align:center;border-radius:4px;font-size:11px;font-weight:700;color:#fff;margin-right:2px}
.fW{background:#22c55e}.fD{background:#9ca3af}.fL{background:#ef4444}
footer{max-width:760px;margin:0 auto;padding:0 16px 40px;font-size:14px}footer a{margin-right:14px}"""

def build(code, slug, name):
    st = get(f"competitions/{code}/standings"); time.sleep(7)
    ms = get(f"competitions/{code}/matches"); time.sleep(7)
    if not st or not ms: return False
    blocks = [b for b in st.get("standings", []) if b.get("type") == "TOTAL" and b.get("table")]
    if not blocks: return False
    sea = st.get("season", {}); season = ""
    try: season = f'{sea["startDate"][:4]}/{sea["endDate"][2:4]}'
    except Exception: pass
    allm = ms.get("matches", [])
    done = [m for m in allm if m.get("status") == "FINISHED"][-10:][::-1]
    nxt = [m for m in allm if m.get("status") in ("SCHEDULED", "TIMED")][:10]
    title = f"{name} Table, Fixtures and Results {season} | ZER0 Updates".replace("  ", " ")
    desc = f"Current {name} table with points and goal difference, plus upcoming fixtures and the latest results. Updated {NICE}."
    url = f"{SITE}/football/{slug}/"
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Football", "item": SITE + "/football/"},
        {"@type": "ListItem", "position": 3, "name": name, "item": url}]}
    body = (f'<h1>{e(name)} Table, Fixtures and Results</h1><p class="m">{e(season)} season. Updated {NICE}.</p>'
            f'<h2>League table</h2>{"".join(table(b, code) for b in blocks)}{legend(code)}<h2>Upcoming fixtures</h2>{fixtures(nxt, False)}'
            f'<h2>Latest results</h2>{fixtures(done, True)}<p><a href="/football/">More football news</a></p>')
    out = (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           f'<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">'
           f'<meta name="robots" content="index,follow,max-image-preview:large"><meta property="og:title" content="{e(title)}">'
           f'<meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{url}">'
           f'<meta property="og:image" content="{SITE}/og-image.png"><meta name="twitter:card" content="summary_large_image">'
           f'<link rel="icon" type="image/png" href="/favicon-32.png"><style>{CSS}</style>'
           f'<script type="application/ld+json">{json.dumps(ld)}</script></head><body>'
           f'<header><a href="/" aria-label="ZER0 Updates home"><img src="/logo-mark.png" alt=""><img class="w" src="/logo-word.png" alt="ZER0 Updates"></a></header>'
           f'<main>{body}</main><footer><a href="/">Home</a><a href="/football/">Football</a><a href="/news/">News</a><a href="/deals/">Deals</a><a href="/about.html">About</a><a href="/terms.html">Terms</a></footer></body></html>')
    os.makedirs(f"football/{slug}", exist_ok=True)
    open(f"football/{slug}/index.html", "w").write(out)
    print(f"[ok] football/{slug}/ ({len(blocks)} table(s), {len(nxt)} fixtures, {len(done)} results)")
    return True

def main():
    for code, slug, name in LEAGUES:
        build(code, slug, name)
    live = [{"slug": s, "name": n} for _, s, n in LEAGUES if os.path.exists(f"football/{s}/index.html")]
    if live:
        os.makedirs("football", exist_ok=True)
        json.dump(live, open("football/leagues.json", "w"))

if __name__ == "__main__":
    main()
