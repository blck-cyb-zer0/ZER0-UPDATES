#!/usr/bin/env python3
"""Builds football tables, fixtures, results, team form and head-to-head history (football-data.org).

Writes:  football/standings.json   (used by the site's Sports tab and the league pages)
         football/<league>/index.html  (crawlable league pages with the interactive view)
         football/history.json, football/h2h.json  (small caches, so the free plan's call limit is respected)
"""
import html, json, os, sys, time
from datetime import datetime, timezone
import requests

SITE = "https://zeroupdates.org"
LEAGUES = [("PL", "premier-league", "Premier League"), ("CL", "champions-league", "UEFA Champions League"),
           ("PD", "la-liga", "La Liga"), ("BL1", "bundesliga", "Bundesliga"), ("SA", "serie-a", "Serie A"), ("FL1", "ligue-1", "Ligue 1")]
NOW = datetime.now(timezone.utc)
D, NICE = NOW.strftime("%Y-%m-%d"), NOW.strftime("%d %B %Y").lstrip("0")
SLEEP = 7                 # the free plan allows 10 calls a minute
HIST_CALLS = [8]          # max past-season downloads per run (they are cached for good afterwards)
H2H_CALLS = [10]          # max head-to-head endpoint calls per run
BLOCKED = {}              # "hist"/"h2h" -> HTTP code, when the free plan does not allow it
HISTORY_FILE, H2H_FILE = "football/history.json", "football/h2h.json"
e = lambda x: html.escape(str(x if x is not None else ""), quote=True)


def call(path):
    key = os.environ.get("FOOTBALL_API_KEY")
    if not key:
        return 0, None
    for _ in range(2):
        try:
            r = requests.get("https://api.football-data.org/v4/" + path, headers={"X-Auth-Token": key}, timeout=30)
        except Exception as ex:
            print(f"[warn] {path}: {ex}", file=sys.stderr)
            return 0, None
        if r.status_code == 200:
            return 200, r.json()
        print(f"[warn] {path} -> {r.status_code}", file=sys.stderr)
        if r.status_code != 429:
            return r.status_code, None
        time.sleep(62)
    return 429, None


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(data, open(path, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)


ZONES = {
    "PL": [(1, 4, "ucl", "Champions League"), (5, 5, "uel", "Europa League"), (6, 6, "uecl", "Conference League"), (18, 20, "rel", "Relegation")],
    "PD": [(1, 4, "ucl", "Champions League"), (5, 6, "uel", "Europa League"), (7, 7, "uecl", "Conference League"), (18, 20, "rel", "Relegation")],
    "SA": [(1, 4, "ucl", "Champions League"), (5, 5, "uel", "Europa League"), (6, 6, "uecl", "Conference League"), (18, 20, "rel", "Relegation")],
    "BL1": [(1, 4, "ucl", "Champions League"), (5, 5, "uel", "Europa League"), (6, 6, "uecl", "Conference League"), (16, 16, "po", "Relegation play-off"), (17, 18, "rel", "Relegation")],
    "FL1": [(1, 3, "ucl", "Champions League"), (4, 4, "uel", "Europa League"), (5, 5, "uecl", "Conference League"), (16, 16, "po", "Relegation play-off"), (17, 18, "rel", "Relegation")],
    "CL": [(1, 8, "ucl", "Round of 16"), (9, 24, "po", "Knockout play-offs"), (25, 36, "rel", "Eliminated")],
}


def zone_of(code, pos):
    for a, b, cls, _label in ZONES.get(code, []):
        try:
            if a <= int(pos) <= b:
                return cls
        except (TypeError, ValueError):
            pass
    return ""


# ---------------------------------------------------------------- match helpers
def tid(t):
    return (t or {}).get("id")


def when(m):
    try:
        return datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).strftime("%a %d %b, %H:%M UTC")
    except Exception:
        return ""


def goals(m):
    ft = (m.get("score") or {}).get("fullTime") or {}
    return ft.get("home"), ft.get("away")


def res(gf, ga):
    return "W" if gf > ga else ("D" if gf == ga else "L")


def team_stats(finished, ids):
    """Form, last 10, home/away records, clean sheets and streaks, worked out from the season's matches."""
    by = {i: [] for i in ids}
    for m in sorted(finished, key=lambda x: x.get("utcDate") or ""):
        hs, as_ = goals(m)
        h, a = tid(m.get("homeTeam")), tid(m.get("awayTeam"))
        if hs is None or as_ is None:
            continue
        d = (m.get("utcDate") or "")[:10]
        if h in by:
            by[h].append((d, True, a, hs, as_))
        if a in by:
            by[a].append((d, False, h, as_, hs))
    out = {}
    for i, ms in by.items():
        hm, aw = [0] * 6, [0] * 6
        cs = fts = 0
        for _d, home, _o, gf, ga in ms:
            blk = hm if home else aw
            blk[0] += 1
            blk[{"W": 1, "D": 2, "L": 3}[res(gf, ga)]] += 1
            blk[4] += gf
            blk[5] += ga
            cs += ga == 0
            fts += gf == 0
        results = [res(gf, ga) for _d, _h, _o, gf, ga in ms]
        streak = ub = 0
        if results:
            last = results[-1]
            for r in reversed(results):
                if r != last:
                    break
                streak += 1
            for r in reversed(results):
                if r == "L":
                    break
                ub += 1
        out[str(i)] = {
            "f": results[-5:], "hm": hm, "aw": aw, "cs": cs, "fts": fts,
            "st": (results[-1] + str(streak)) if results else "", "ub": ub,
            "last": [[d, "H" if home else "A", o, gf, ga, res(gf, ga)] for d, home, o, gf, ga in reversed(ms[-10:])],
        }
    return out


# ---------------------------------------------------------------- head-to-head
def compact(matches):
    out = []
    for m in matches or []:
        hs, as_ = goals(m)
        if m.get("status") == "FINISHED" and hs is not None and as_ is not None:
            out.append([(m.get("utcDate") or "")[:10], tid(m.get("homeTeam")), tid(m.get("awayTeam")), hs, as_])
    return out


def fill_history(code, cur_year, hist):
    """Past seasons never change, so each is downloaded once and kept in football/history.json."""
    seasons = hist.setdefault(code, {})
    for y in (cur_year - 1, cur_year - 2):
        if str(y) in seasons or BLOCKED.get("hist") or HIST_CALLS[0] <= 0:
            continue
        HIST_CALLS[0] -= 1
        status, d = call(f"competitions/{code}/matches?season={y}")
        time.sleep(SLEEP)
        if status in (400, 403, 404):
            BLOCKED["hist"] = status
            print(f"[info] past seasons are not available on this plan (HTTP {status}); using the head-to-head endpoint instead")
            continue
        if d is not None:
            seasons[str(y)] = compact(d.get("matches"))
    for k in [k for k in seasons if k not in (str(cur_year - 1), str(cur_year - 2))]:
        del seasons[k]


def api_h2h(match_id, a, b, cache):
    key = f"{min(a, b)}-{max(a, b)}"
    c = cache.get(key)
    if c and NOW.timestamp() - c.get("ts", 0) < 10 * 86400:
        return c["m"]
    if BLOCKED.get("h2h") or H2H_CALLS[0] <= 0 or not match_id:
        return c["m"] if c else []
    H2H_CALLS[0] -= 1
    status, d = call(f"matches/{match_id}/head2head?limit=10")
    time.sleep(SLEEP)
    if status in (400, 403, 404):
        BLOCKED["h2h"] = status
        print(f"[info] head-to-head endpoint not available on this plan (HTTP {status})")
        return []
    if d is None:
        return c["m"] if c else []
    ms = sorted(compact(d.get("matches")), reverse=True)
    cache[key] = {"ts": NOW.timestamp(), "m": ms}
    return ms


def meetings(a, b, sources):
    seen, out = set(), []
    for src in sources:
        for m in src:
            if {m[1], m[2]} == {a, b} and (m[0], m[1], m[2]) not in seen:
                seen.add((m[0], m[1], m[2]))
                out.append(m)
    return sorted(out, reverse=True)


def h2h_block(a, b, ms):
    if not ms:
        return None
    hw = sum(1 for _d, h, g, hs, as_ in ms if (h == a and hs > as_) or (g == a and as_ > hs))
    aw = sum(1 for _d, h, g, hs, as_ in ms if (h == b and hs > as_) or (g == b and as_ > hs))
    return {"m": ms[:6], "n": len(ms), "hw": hw, "d": len(ms) - hw - aw, "aw": aw}


# ---------------------------------------------------------------- crawlable page (the interactive view loads on top of this)
CSS = """:root{--bg:#f4f7fc;--surface:#fff;--surface-2:#f7f9fd;--text:#0a1a3f;--muted:#5b6785;--line:#e3e8f3;--brand:#1e3cc8;--brand-2:#2f6bff;--shadow:0 1px 2px rgba(15,23,42,.05),0 6px 18px rgba(15,23,42,.06);--radius:14px}
@media(prefers-color-scheme:dark){:root{--bg:#0a0f1f;--surface:#121a2e;--surface-2:#0e1526;--text:#e8edf8;--muted:#93a0ba;--line:#1f2a44;--brand:#5b86ff;--brand-2:#7fa1ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 Inter,system-ui,sans-serif}
header{background:linear-gradient(135deg,#1e3cc8,#0a1a3f);padding:12px 16px}header a{display:inline-flex;align-items:center;gap:8px;line-height:0}header img{height:30px}header .w{height:13px}
main{max-width:860px;margin:0 auto;padding:22px 16px 50px}h1{font:700 27px/1.2 Poppins,Inter,sans-serif;margin:6px 0}h2{margin:26px 0 8px}
table{width:100%;border-collapse:collapse;font-size:14px}td,th{border:1px solid var(--line);padding:6px 8px;text-align:left;background:var(--surface)}
ul{padding-left:18px}li{margin:6px 0}.m{color:var(--muted);font-size:14px}a{color:var(--brand-2)}.tw{overflow-x:auto}
footer{max-width:860px;margin:0 auto;padding:0 16px 40px;font-size:14px}footer a{margin-right:14px}img.c{width:18px;height:18px;vertical-align:-4px;margin-right:6px}"""


def team_label(tm, i):
    t = tm.get(str(i)) or {}
    img = f'<img class="c" src="{e(t["c"])}" alt="" width="18" height="18" loading="lazy">' if t.get("c") else ""
    return img + e(t.get("n", ""))


def pre_table(L):
    out = ""
    for b in L["blocks"]:
        rows = "".join(
            f'<tr><td>{e(r["pos"])}</td><td>{team_label(L["tm"], r["id"])}</td><td>{e(r["p"])}</td><td>{e(r["w"])}</td><td>{e(r["d"])}</td>'
            f'<td>{e(r["l"])}</td><td>{e(r["gf"])}</td><td>{e(r["ga"])}</td><td>{e(r["gd"])}</td><td><strong>{e(r["pts"])}</strong></td></tr>'
            for r in b["rows"])
        out += ((f'<h3>{e(b["group"])}</h3>' if b.get("group") else "") +
                '<div class="tw"><table><tr><th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr>' + rows + "</table></div>")
    return out


def pre_fx(L, items, scored):
    if not items:
        return "<p class='m'>Nothing to show right now.</p>"
    def li(m):
        mid = f'{m["hs"]} - {m["as"]}' if scored and m.get("hs") is not None else "vs"
        try:
            when = datetime.fromisoformat(m["utc"].replace("Z", "+00:00")).strftime("%a %d %b, %H:%M UTC")
        except Exception:
            when = ""
        return f'<li><span class="m">{e(when)}</span><br><strong>{team_label(L["tm"], m["h"])}</strong> {e(mid)} <strong>{team_label(L["tm"], m["a"])}</strong></li>'
    return "<ul>" + "".join(li(m) for m in items) + "</ul>"


def page(L, code):
    name, slug, season = L["name"], L["slug"], L["season"]
    title = f"{name} Table and Fixtures {season} | ZER0 Updates".replace("  ", " ")
    desc = (f"Current {name} table with team badges, points and form, upcoming fixtures with head-to-head history and the latest results. "
            f"Updated {NICE}.")
    url = f"{SITE}/sports/{slug}-table/"
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Sports", "item": SITE + "/sports/"},
        {"@type": "ListItem", "position": 3, "name": name, "item": url}]}
    data = json.dumps(L, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    fallback = (f'<h2>League table</h2>{pre_table(L)}<h2>Upcoming fixtures</h2>{pre_fx(L, L["next"], False)}'
                f'<h2>Latest results</h2>{pre_fx(L, L["done"], True)}')
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">'
            f'<meta name="robots" content="index,follow,max-image-preview:large"><meta property="og:title" content="{e(title)}">'
            f'<meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{url}">'
            f'<meta property="og:image" content="{SITE}/og-image.png"><meta name="twitter:card" content="summary_large_image">'
            f'<link rel="icon" type="image/png" href="/favicon-32.png"><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">'
            f'<style>{CSS}</style><link rel="stylesheet" href="/football-ui.css">'
            f'<script type="application/ld+json">{json.dumps(ld)}</script></head><body>'
            f'<header><a href="/" aria-label="ZER0 Updates home"><img src="/logo-mark.png" alt=""><img class="w" src="/logo-word.png" alt="ZER0 Updates"></a></header>'
            f'<main><h1>{e(name)} Table and Fixtures</h1><p class="m">{e(season)} season. Updated {NICE}.</p>'
            f'<div id="fb-app" data-fb-league>{fallback}</div>'
            f'<script type="application/json" id="fb-data">{data}</script>'
            f'<p><a href="/sports/">More football news</a></p></main>'
            f'<footer><a href="/">Home</a><a href="/sports/">Sports</a><a href="/news/">News</a><a href="/deals/">Deals</a><a href="/about.html">About</a><a href="/terms.html">Terms</a></footer>'
            f'<script src="/football-ui.js"></script></body></html>')


# ---------------------------------------------------------------- one league
def build(code, slug, name, hist, h2h_cache):
    st = call(f"competitions/{code}/standings")[1]
    time.sleep(SLEEP)
    ms = call(f"competitions/{code}/matches")[1]
    time.sleep(SLEEP)
    if not st or not ms:
        return None
    blocks = [b for b in st.get("standings", []) if b.get("type") == "TOTAL" and b.get("table")]
    if not blocks:
        return None
    sea = st.get("season", {})
    season, cur_year = "", None
    try:
        season = f'{sea["startDate"][:4]}/{sea["endDate"][2:4]}'
        cur_year = int(sea["startDate"][:4])
    except Exception:
        pass
    allm = ms.get("matches", [])
    finished = [m for m in allm if m.get("status") == "FINISHED"]
    upcoming = [m for m in allm if m.get("status") in ("SCHEDULED", "TIMED") and tid(m.get("homeTeam")) and tid(m.get("awayTeam"))]
    done, nxt = finished[-10:][::-1], upcoming[:10]

    tm = {}
    def reg(t):
        i = tid(t)
        if i is not None:
            tm.setdefault(str(i), {"n": t.get("shortName") or t.get("name") or "", "t": t.get("tla") or "", "c": t.get("crest") or ""})
    for b in blocks:
        for r in b["table"]:
            reg(r["team"])
    for m in allm:
        reg(m.get("homeTeam")); reg(m.get("awayTeam"))
    ids = [tid(r["team"]) for b in blocks for r in b["table"]]
    stats = team_stats(finished, ids)
    for m in upcoming:
        for me, opp, home in ((tid(m["homeTeam"]), tid(m["awayTeam"]), True), (tid(m["awayTeam"]), tid(m["homeTeam"]), False)):
            s = stats.get(str(me))
            if s is not None and "next" not in s:
                s["next"] = {"id": m.get("id"), "utc": m.get("utcDate"), "h": "H" if home else "A", "o": opp}

    if cur_year:
        fill_history(code, cur_year, hist)
    past = list((hist.get(code) or {}).values())
    cur = compact(finished)
    def fixture(m, scored):
        d = {"id": m.get("id"), "utc": m.get("utcDate"), "md": m.get("matchday"), "h": tid(m["homeTeam"]), "a": tid(m["awayTeam"]),
             "when": when(m), "home": tm[str(tid(m["homeTeam"]))]["n"], "away": tm[str(tid(m["awayTeam"]))]["n"], "score": ""}
        if scored:
            d["hs"], d["as"] = goals(m)
            if d["hs"] is not None:
                d["score"] = f'{d["hs"]} - {d["as"]}'
        else:
            a, b = d["h"], d["a"]
            found = meetings(a, b, past + [cur])
            if len(found) < 3:
                found = meetings(a, b, [found, api_h2h(d["id"], a, b, h2h_cache)])
            blk = h2h_block(a, b, found)
            if blk:
                d["h2h"] = blk
        return d
    nxt_out = [fixture(m, False) for m in nxt]
    done_out = [fixture(m, True) for m in done]

    L = {"slug": slug, "name": name, "season": season, "updated": NICE, "v": 2,
         "zones": [{"from": a, "to": b, "cls": c, "label": l} for a, b, c, l in ZONES.get(code, [])],
         "blocks": [{"group": (bl.get("group") or "").replace("_", " ").title(), "rows": [
             {"pos": t.get("position"), "id": tid(t["team"]), "team": tm[str(tid(t["team"]))]["n"], "tla": tm[str(tid(t["team"]))]["t"],
              "crest": tm[str(tid(t["team"]))]["c"], "p": t.get("playedGames"), "w": t.get("won"), "d": t.get("draw"), "l": t.get("lost"),
              "gf": t.get("goalsFor"), "ga": t.get("goalsAgainst"), "gd": t.get("goalDifference"), "pts": t.get("points"),
              "form": (stats.get(str(tid(t["team"]))) or {}).get("f", [])}
             for t in bl.get("table", [])]} for bl in blocks],
         "tm": tm, "teams": stats, "next": nxt_out, "done": done_out}
    os.makedirs(f"sports/{slug}-table", exist_ok=True)
    open(f"sports/{slug}-table/index.html", "w", encoding="utf-8").write(page(L, code))
    n_h2h = sum(1 for f in nxt_out if f.get("h2h"))
    print(f"[ok] sports/{slug}-table/ ({len(blocks)} table(s), {len(nxt_out)} fixtures, {n_h2h} with head-to-head, {len(done_out)} results)")
    return L


def main():
    hist, h2h_cache = load(HISTORY_FILE, {}), load(H2H_FILE, {})
    built = {}
    for code, slug, name in LEAGUES:
        L = build(code, slug, name, hist, h2h_cache)
        if L:
            built[slug] = L
    old = {l["slug"]: l for l in load("football/standings.json", {}).get("leagues", [])}
    old.update(built)
    merged = [old[sl] for _, sl, _ in LEAGUES if sl in old]
    if merged:
        save("football/standings.json", {"generated_at": NOW.isoformat(), "leagues": merged})
        save(HISTORY_FILE, hist)
        save(H2H_FILE, h2h_cache)
        try:
            import build_sports
            build_sports.build()
        except Exception as ex:
            print("[warn] build_sports failed:", ex)
    live = [{"slug": s, "name": n} for _, s, n in LEAGUES if os.path.exists(f"sports/{s}-table/index.html")]
    if live:
        save("football/leagues.json", live)
    print(f"[done] {len(built)} league(s) rebuilt; head-to-head: past seasons {'blocked' if BLOCKED.get('hist') else 'ok'}, endpoint {'blocked' if BLOCKED.get('h2h') else 'ok'}")


if __name__ == "__main__":
    main()
