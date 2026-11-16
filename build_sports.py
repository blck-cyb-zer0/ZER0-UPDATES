#!/usr/bin/env python3
"""Builds the football section as fast, standalone pages (no JavaScript needed to read them):
   /sports/                    News
   /sports/tables/             Tables & Fixtures (league picker)
   /sports/<league>-table/     one league: table, upcoming fixtures, latest results
Reads football_news.json and football/standings.json. Run from the repo root."""
import json, os
from urllib.parse import urlparse
from build_downloads import shell, write, e, NICE, SITE

def load(path, default):
    try: return json.load(open(path, encoding="utf-8"))
    except Exception: return default

def host(u): return urlparse(u).netloc.replace("www.", "")
def ok(u): return u if str(u).startswith(("http://", "https://")) else ""

def tabs(active):
    a = lambda k, h, t: f'<a href="{h}"{" aria-current=page" if k == active else ""}>{t}</a>'
    return f'<nav class="subtabs" aria-label="Football sections">{a("news", "/sports/", "News")}{a("tables", "/sports/tables/", "Tables &amp; Fixtures")}</nav>'

def chips(leagues, cur=None):
    return '<div class="chips" aria-label="Leagues">' + "".join(
        f'<a href="/sports/{L["slug"]}-table/"{" aria-current=page" if L["slug"] == cur else ""}>{e(L["name"])}</a>' for L in leagues) + "</div>"

# ------------------------------------------------------------------ News
NEWS_JS = """<script>(function(){var c=document.querySelectorAll('.news [data-cat]');if(!c.length)return;var cats={};[].forEach.call(c,function(x){var k=x.getAttribute('data-cat');cats[k]=(cats[k]||0)+1});
var keys=Object.keys(cats);if(keys.length<2)return;var bar=document.getElementById('catbar');if(!bar)return;
function mk(label,val){var b=document.createElement('button');b.type='button';b.textContent=label;b.setAttribute('aria-pressed',val===''?'true':'false');b.onclick=function(){[].forEach.call(bar.children,function(y){y.setAttribute('aria-pressed','false')});b.setAttribute('aria-pressed','true');[].forEach.call(c,function(x){x.hidden=val!==''&&x.getAttribute('data-cat')!==val})};bar.appendChild(b)}
mk('All','');keys.sort().forEach(function(k){mk(k+' ('+cats[k]+')',k)})})();</script>"""

def news_page(leagues, arts):
    cards, ld_items = "", []
    for a in arts[:40]:
        u = ok(a.get("link"))
        if not u or not a.get("title"): continue
        cards += (f'<article class="card" data-cat="{e(a.get("cat") or "Other")}"><span class="tag">{e(a.get("cat") or "Other")}</span>'
                  f'<h2><a href="{e(u)}" target="_blank" rel="nofollow noopener">{e(a["title"])}</a></h2><p>{e(a.get("summary", ""))}</p>'
                  f'<p class="m"><a href="{e(u)}" target="_blank" rel="nofollow noopener">Read the full story at {e(host(u))} &rarr;</a></p></article>')
        ld_items.append((a["title"], u))
    body = f"""<h1>Football News Today</h1>
<p class="lead">Transfers, match reports and injury updates, summarised and linked to the original sources. Updated {NICE}.</p>
{tabs("news")}
<div class="chips" id="catbar" aria-label="Filter by type"></div>
<div class="news">{cards or "<p>No football news yet. Check back soon.</p>"}</div>
<h2>League tables and fixtures</h2>{chips(leagues)}
<p><a class="btn" href="/sports/tables/">All tables and fixtures</a></p>{NEWS_JS}"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Football News Today", "url": f"{SITE}/sports/",
          "dateModified": NOW_ISO(), "isPartOf": {"@id": f"{SITE}/#site"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "url": u} for i, (n, u) in enumerate(ld_items[:20])]}}
    write("/sports/", shell("/sports/", "Football News Today: Transfers, Match Reports and Injury Updates | ZER0 Updates",
          "Today's football headlines: transfer news, match reports and injury updates, summarised with links to the original sources. Plus league tables and fixtures.",
          body, ld, "/sports/"))

def NOW_ISO():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ------------------------------------------------------------------ Tables hub
def hub_page(data):
    cards = ""
    for L in data:
        rows = (L.get("blocks") or [{}])[0].get("rows", [])[:3]
        top = "".join(f'<tr><td>{e(r["pos"])}</td><td class="tn">{e(r["team"])}</td><td class="pts">{e(r["pts"])}</td></tr>' for r in rows)
        nx = (L.get("next") or [None])[0]
        nxt = f'<p class="m"><b>Next:</b> {e(nx["home"])} vs {e(nx["away"])}<br>{e(nx["when"])}</p>' if nx else ""
        cards += (f'<div class="card"><h3>{e(L["name"])}</h3><p class="m">{e(L.get("season", ""))} season</p>'
                  f'<table class="fbt" style="margin:6px 0"><tr><th>#</th><th class="tn">Team</th><th>Pts</th></tr>{top}</table>{nxt}'
                  f'<p><a class="btn" href="/sports/{L["slug"]}-table/">Full table &amp; fixtures</a></p></div>')
    body = f"""<h1>Football Tables and Fixtures</h1>
<p class="lead">Pick a competition for the full table, upcoming fixtures and latest results. Updated {NICE}.</p>
{tabs("tables")}<div class="grid">{cards}</div>
<p class="m">Standings, fixtures and results come from a third-party football data provider and refresh several times a day. Times are shown in UTC.</p>"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Football Tables and Fixtures", "url": f"{SITE}/sports/tables/",
          "dateModified": NOW_ISO(), "isPartOf": {"@id": f"{SITE}/#site"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": L["name"] + " table and fixtures", "url": f"{SITE}/sports/{L['slug']}-table/"} for i, L in enumerate(data)]}}
    write("/sports/tables/", shell("/sports/tables/", "Football Tables and Fixtures: Premier League, La Liga, Bundesliga, Serie A, Ligue 1 | ZER0 Updates",
          "Current league tables, upcoming fixtures and latest results for the Premier League, La Liga, Bundesliga, Serie A, Ligue 1 and the Champions League.",
          body, ld, "/sports/"))

# ------------------------------------------------------------------ One league
def zone(L, pos):
    for z in L.get("zones", []):
        if z["from"] <= (pos or 0) <= z["to"]: return z["cls"]
    return ""

def table(L, b):
    rows = ""
    for t in b.get("rows", []):
        z = zone(L, t.get("pos"))
        crest = f'<img src="{e(ok(t.get("crest")))}" alt="" width="18" height="18" loading="lazy" referrerpolicy="no-referrer">' if ok(t.get("crest")) else ""
        form = "".join(f'<i class="f {e(x)}">{e(x)}</i>' for x in t.get("form", []))
        gd = t.get("gd")
        gd = f"+{gd}" if isinstance(gd, int) and gd > 0 else gd
        rows += (f'<tr{f" class=z-{z}" if z else ""}><td>{e(t.get("pos"))}</td><td class="tn">{crest}{e(t.get("team"))}</td><td>{e(t.get("p"))}</td><td>{e(t.get("w"))}</td>'
                 f'<td>{e(t.get("d"))}</td><td>{e(t.get("l"))}</td><td class="opt">{e(t.get("gf"))}</td><td class="opt">{e(t.get("ga"))}</td><td>{e(gd)}</td>'
                 f'<td class="pts">{e(t.get("pts"))}</td><td class="opt" style="text-align:left">{form}</td></tr>')
    head = (f'<h3 style="margin:18px 0 6px">{e(b["group"])}</h3>' if b.get("group") and len(L.get("blocks", [])) > 1 else "")
    return (f'{head}<div class="tw"><table class="fbt"><tr><th>#</th><th class="tn">Team</th><th>P</th><th>W</th><th>D</th><th>L</th>'
            f'<th class="opt">GF</th><th class="opt">GA</th><th>GD</th><th>Pts</th><th class="opt">Form</th></tr>{rows}</table></div>')

ZCOL = {"ucl": "#2f6bff", "uel": "#f08a1c", "uecl": "#1fa971", "po": "#a36bff", "rel": "#e5484d"}

def legend(L):
    seen, out = set(), ""
    for z in L.get("zones", []):
        if z["label"] in seen: continue
        seen.add(z["label"])
        out += f'<span><i style="background:{ZCOL.get(z["cls"], "#8a94ad")}"></i>{e(z["label"])}</span>'
    return f'<div class="key">{out}</div><p class="m">Usual qualification and relegation places. They can change with cup winners and European results.</p>' if out else ""

def h2h_note(m):
    h = m.get("h2h")
    if not h or not h.get("n"): return ""
    return f'<small>Head to head ({e(h["n"])} meetings): {e(m["home"])} {e(h["hw"])} wins, {e(h["d"])} draws, {e(m["away"])} {e(h["aw"])} wins.</small>'

def upcoming(items):
    if not items: return '<p class="m">No fixtures to show right now.</p>'
    return '<ul class="fx">' + "".join(f'<li><time datetime="{e(m.get("utc", ""))}">{e(m["when"])}</time><span class="mt">{e(m["home"])}<b>vs</b>{e(m["away"])}</span>{h2h_note(m)}</li>' for m in items) + "</ul>"

def results(items):
    if not items: return '<p class="m">No results to show right now.</p>'
    return '<ul class="fx">' + "".join(f'<li><time datetime="{e(m.get("utc", ""))}">{e(m["when"])}</time><span class="mt">{e(m["home"])}<b>{e(m.get("score") or "vs")}</b>{e(m["away"])}</span></li>' for m in items) + "</ul>"

def league_page(L, leagues):
    name, season = L["name"], L.get("season", "")
    path = f"/sports/{L['slug']}-table/"
    body = f"""<p class="crumbs"><a href="/sports/">Football</a> / <a href="/sports/tables/">Tables &amp; Fixtures</a> / {e(name)}</p>
<h1>{e(name)} Table and Fixtures</h1><p class="lead">{e(season)} season. Updated {e(L.get("updated") or NICE)}.</p>
{tabs("tables")}{chips(leagues, L["slug"])}
<p class="m">Jump to: <a href="#table">Table</a> &middot; <a href="#fixtures">Upcoming fixtures</a> &middot; <a href="#results">Latest results</a></p>
<h2 id="table">{e(name)} table</h2>{"".join(table(L, b) for b in L.get("blocks", []))}{legend(L)}
<h2 id="fixtures">Upcoming fixtures</h2>{upcoming(L.get("next", []))}
<h2 id="results">Latest results</h2>{results(L.get("done", []))}
<p class="m">Times are in UTC. Data comes from a third-party football data provider and can be delayed.</p>"""
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": f"{name} Table and Fixtures", "url": f"{SITE}{path}", "dateModified": NOW_ISO(),
          "isPartOf": {"@id": f"{SITE}/#site"}, "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Football", "item": f"{SITE}/sports/"},
              {"@type": "ListItem", "position": 2, "name": "Tables & Fixtures", "item": f"{SITE}/sports/tables/"},
              {"@type": "ListItem", "position": 3, "name": name, "item": f"{SITE}{path}"}]}}
    write(path, shell(path, f"{name} Table and Fixtures {season} | ZER0 Updates".replace("  ", " "),
          f"Current {name} table with points and goal difference, plus upcoming fixtures and the latest results. Updated {NICE}.", body, ld, "/sports/"))
    return path

def build():
    data = load("football/standings.json", {}).get("leagues", [])
    arts = load("football_news.json", {}).get("articles", [])
    out = []
    news_page(data, arts); out.append("sports/")
    if data:
        hub_page(data); out.append("sports/tables/")
        for L in data:
            out.append(league_page(L, data).strip("/") + "/")
    return out

if __name__ == "__main__":
    print("[ok] built", len(build()), "football pages")
