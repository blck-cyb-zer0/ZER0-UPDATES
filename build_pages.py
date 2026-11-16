#!/usr/bin/env python3
"""Builds crawlable static pages (sports/, news/, deals/, coupons/ and their category pages) plus sitemap.xml from the JSON data files."""
import html, json, os
from datetime import datetime, timezone
from urllib.parse import urlparse

SITE = "https://zeroupdates.org"
NOW = datetime.now(timezone.utc)
D, NICE = NOW.strftime("%Y-%m-%d"), NOW.strftime("%d %B %Y").lstrip("0")
e = lambda x: html.escape(str(x if x is not None else ""), quote=True)
ok = lambda u: u if str(u).startswith(("http://", "https://")) else ""
BUILT = []

import re

def shell(slug, title, desc, h1, intro, body, ld, view, chip):
    try: t = open("index.html").read()
    except Exception: return None
    url = f"{SITE}/{slug}/"
    sub = lambda pat, rep: re.subn(pat, lambda m: rep(m) if callable(rep) else rep, t, count=1, flags=re.S)[0]
    t = sub(r"<title>.*?</title>", f"<title>{e(title)}</title>")
    t = sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + e(desc) + m.group(2))
    t = sub(r'(<link rel="canonical" href=")[^"]*(")', lambda m: m.group(1) + url + m.group(2))
    t = sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + e(title) + m.group(2))
    t = sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + e(desc) + m.group(2))
    t = sub(r'(<meta property="og:url" content=")[^"]*(")', lambda m: m.group(1) + url + m.group(2))
    head = (f'<base href="/"><script>if(!location.hash)history.replaceState(null,"",location.pathname+"#{view}");</script>'
            f'<script type="application/ld+json">{json.dumps(ld)}</script>')
    t = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + head, t, count=1)
    ns = f'<noscript><div style="padding:16px;max-width:760px;margin:auto"><h1>{e(h1)}</h1><p>{e(intro)}</p>{body}</div></noscript>'
    t = re.sub(r'(<main class="wrap" id="main">)', lambda m: m.group(1) + ns, t, count=1)
    js = ("<script>(function(){var V=%s,H=%s,S=%s,C=%s,n=0;"
          "function head(){var s=document.querySelector('#sec-'+V+' .sec-head');if(!s)return;var h=s.querySelector('h1'),p=s.querySelector('p');if(h)h.textContent=H;if(p)p.textContent=S}"
          "function chip(){var q=document.querySelectorAll('#sec-'+V+' button');for(var i=0;i<q.length;i++){if(q[i].textContent.trim().toLowerCase()===C.toLowerCase()){q[i].click();return true}}return false}"
          "var t=setInterval(function(){n++;head();if(!C||chip()||n>40)clearInterval(t)},250)})();</script>") % (json.dumps(view), json.dumps(h1), json.dumps(intro), json.dumps(chip or ""))
    t = t.replace("</body>", js + "</body>", 1)
    return t


def load(f, key):
    try: return json.load(open(f)).get(key, []) or []
    except Exception: return []

CSS = """:root{--bg:#f4f7fc;--card:#fff;--ink:#0a1a3f;--mut:#5b6785;--line:#e3e8f3;--hi:#2f6bff}
@media(prefers-color-scheme:dark){:root{--bg:#0b0f1a;--card:#131a2b;--ink:#eef2ff;--mut:#9aa6c4;--line:#222c45;--hi:#4d8dff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 Inter,system-ui,sans-serif}
header{background:linear-gradient(135deg,#1e3cc8,#0a1a3f);padding:12px 16px}header a{display:inline-flex;align-items:center;gap:8px;line-height:0}header img{height:30px}header .w{height:13px}
main{max-width:760px;margin:0 auto;padding:22px 16px 50px}h1{font:700 27px/1.2 Poppins,Inter,sans-serif;margin:6px 0}
article{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:12px 0;box-shadow:0 1px 2px rgba(15,23,42,.05),0 6px 18px rgba(15,23,42,.06)}
article h2{font-size:18px;line-height:1.3;margin:0 0 4px}article p{margin:6px 0}.m{color:var(--mut);font-size:14px}a{color:var(--hi)}
.btn{display:inline-block;background:var(--hi);color:#fff!important;text-decoration:none;border-radius:10px;padding:8px 14px;font-weight:600;font-size:14px}
code{border:1px dashed var(--hi);border-radius:6px;padding:2px 8px;font-weight:700}s{color:var(--mut)}
footer{max-width:760px;margin:0 auto;padding:0 16px 40px;font-size:14px;color:var(--mut)}footer a{margin-right:14px}"""

NAV = [("", "Home"), ("sports/", "Sports"), ("news/", "News"), ("deals/", "Deals"), ("coupons/", "Coupons")]

def page(slug, title, desc, h1, intro, body, names_urls, extra="", view=None, chip=None):
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": f"{SITE}/{slug}/",
          "dateModified": D, "isPartOf": {"@id": f"{SITE}/#site"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "name": n, "url": u} for i, (n, u) in enumerate(names_urls[:20])]}}
    foot = "".join(f'<a href="/{p}">{n}</a>' for p, n in NAV)
    top = slug.split("/")[0]
    full = shell(slug, title, desc, h1, intro, body, ld, view or top, chip) if (view or top) in ("sports", "news", "deals", "coupons") else None
    out = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}/{slug}/"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/{slug}/"><meta property="og:image" content="{SITE}/og-image.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/favicon-32.png"><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"><style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld)}</script></head><body>
<header><a href="/" aria-label="ZER0 Updates home"><img src="/logo-mark.png" alt=""><img class="w" src="/logo-word.png" alt="ZER0 Updates"></a></header>
<main><h1>{e(h1)}</h1><p class="m">Updated {NICE}. {e(intro)}</p>
{body}
<p><a class="btn" href="/#{top}">Open the full interactive site</a></p></main>
<footer>{foot}</footer>{extra}</body></html>"""
    os.makedirs(slug, exist_ok=True)
    open(f"{slug}/index.html", "w").write(full or out)
    BUILT.append(slug)
    print(f"[ok] {slug}/ ({len(names_urls)} items)")

def host(u): return urlparse(u).netloc.replace("www.", "")

def articles(items):
    out, nu = [], []
    for a in items[:40]:
        u = ok(a.get("link"))
        if not u or not a.get("title"): continue
        out.append(f'<article><h2>{e(a["title"])}</h2><p class="m">{e(a.get("cat",""))}</p><p>{e(a.get("summary",""))}</p>'
                   f'<p><a href="{e(u)}" target="_blank" rel="nofollow noopener">Read the full story at {e(host(u))} &rarr;</a></p></article>')
        nu.append((a["title"], u))
    return "\n".join(out), nu

def deal_cards(items):
    out, nu = [], []
    for d in items[:40]:
        u = ok(d.get("link"))
        if not u or not d.get("title"): continue
        try: price = f'<p><strong>${e(d["now"])}</strong> <s>${e(d["was"])}</s></p>' if float(d.get("now", 0)) > 0 else ""
        except (TypeError, ValueError): price = ""
        out.append(f'<article><h2>{e(d["title"])}</h2><p class="m">{e(d.get("cat",""))}</p>{price}<p>{e(d.get("desc",""))}</p>'
                   f'<p><a class="btn" href="{e(u)}" target="_blank" rel="sponsored nofollow noopener">View deal</a></p></article>')
        nu.append((d["title"], u))
    return "\n".join(out), nu

def links(pairs, label):
    return f"<p><strong>{label}</strong> " + " · ".join(f'<a href="{h}">{e(t)}</a>' for h, t in pairs) + "</p>" if pairs else ""

def league_links():
    try: L = json.load(open("football/leagues.json"))
    except Exception: return ""
    return links([(f'/sports/{l["slug"]}-table/', f'{l["name"]} table and fixtures') for l in L], "Tables and fixtures:")

# (slug, data file, key, render fn, hub title, hub desc, hub h1, hub intro, category field, [(value, sub-slug, title, desc, h1)])
SECTIONS = [
    ("sports", "football_news.json", "articles", articles,
     "Football News Today: Transfers, Match Reports and Injury Updates | ZER0 Updates",
     "Today's football headlines: transfer news, match reports and injury updates, summarised with links to the original sources.",
     "Football News Today", "Transfers, match reports and injury news, summarised and linked to the original sources.", "cat",
     []),
    ("news", "news.json", "articles", articles,
     "Trending Tech and World News Today | ZER0 Updates",
     "Today's trending technology, business, science and world news in short summaries, each linked to its original source.",
     "Trending News Today", "Short AI-assisted summaries, each linked to the original article.", "cat",
     [(c, c.lower(), f"{c} News Today | ZER0 Updates", f"Today's {c.lower()} news in short summaries, each linked to its original source.", f"{c} News Today")
      for c in ("Tech", "Business", "Science", "World")]),
    ("deals", "deals.json", "deals", deal_cards,
     "Today's Best Deals and Discounts | ZER0 Updates",
     "Hand-picked discounts and price drops from across the web, refreshed every day. Some links are affiliate links.",
     "Today's Best Deals", "Prices change fast, so confirm at checkout. Some links are affiliate links.", "cat",
     [(c, c.lower(), f"{c} Deals Today | ZER0 Updates", f"Today's best {c.lower()} deals and discounts. Prices change fast, so confirm at checkout.", f"{c} Deals Today")
      for c in ("Tech", "Home", "Audio", "Software", "Outdoors", "Courses")]),
]
MIN_CAT = 3

for slug, f, key, fn, title, desc, h1, intro, field, cats in SECTIONS:
    items = load(f, key)
    extra = '<script src="/affiliate.js"></script>' if slug == "deals" else ""
    subs = []
    for val, sub, t, d, h in cats:
        sel = [x for x in items if str(x.get(field, "")).lower() == val.lower()]
        body, nu = fn(sel)
        if len(nu) >= MIN_CAT:
            page(f"{slug}/{sub}", t, d, h, intro, body, nu, extra, view=slug, chip=val); subs.append((f"/{slug}/{sub}/", h))
    body, nu = fn(items)
    if nu:
        pre = (league_links() if slug == "sports" else "") + links(subs, "Browse:")
        page(slug, title, desc, h1, intro, pre + body, nu, extra)

cps, nu, out = load("coupons.json", "coupons"), [], []
for c in cps[:40]:
    u = ok(c.get("link"))
    if not u or not c.get("code"): continue
    out.append(f'<article><h2>{e(c.get("store",""))}: {e(c.get("discount",""))}</h2><p>{e(c.get("desc",""))}</p>'
               f'<p>Code: <code>{e(c["code"])}</code></p><p><a class="btn" href="{e(u)}" target="_blank" rel="sponsored nofollow noopener">Go to the deal</a></p></article>')
    nu.append((f'{c.get("store","")} coupon code', u))
if nu: page("coupons", "Working Coupon Codes Today | ZER0 Updates",
            "Promo codes found in today's deal listings, checked against the source. Codes expire quickly, so confirm at checkout.",
            "Coupon Codes Today", "Only codes that appear in the source listing are shown.", "\n".join(out), nu)


def league_pages():
    try: data = json.load(open("football/standings.json")).get("leagues", [])
    except Exception: return
    for L in data:
        body = ""
        for b in L.get("blocks", []):
            rows = "".join(f'<tr><td>{e(t["pos"])}</td><td>{e(t["team"])}</td><td>{e(t["p"])}</td><td>{e(t["w"])}</td><td>{e(t["d"])}</td><td>{e(t["l"])}</td><td>{e(t["gf"])}</td><td>{e(t["ga"])}</td><td>{e(t["gd"])}</td><td>{e(t["pts"])}</td></tr>' for t in b.get("rows", []))
            body += f'<table><tr><th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr>{rows}</table>'
        fx = lambda a: "<ul>" + "".join(f'<li>{e(m["when"])}: {e(m["home"])} {e(m.get("score") or "vs")} {e(m["away"])}</li>' for m in a) + "</ul>"
        body += "<h2>Upcoming fixtures</h2>" + fx(L.get("next", [])) + "<h2>Latest results</h2>" + fx(L.get("done", []))
        name, season = L["name"], L.get("season", "")
        page(f'sports/{L["slug"]}-table', f"{name} Table and Fixtures {season} | ZER0 Updates".replace("  ", " "),
             f"Current {name} table with points and goal difference, plus upcoming fixtures and the latest results. Updated {NICE}.",
             f"{name} Table and Fixtures", f"{season} season. Updated {NICE}.".strip(), body, [(name + " table", f"{SITE}/sports/{L['slug']}-table/")], view="sports", chip=name)

league_pages()
# league pages
try: LEAGUES = json.load(open("football/leagues.json"))
except Exception: LEAGUES = []
paths = [f"sports/{l['slug']}-table" for l in LEAGUES if os.path.exists(f"sports/{l['slug']}-table/index.html")]

# old addresses: small redirect pages so nothing breaks
def moved(old, new):
    if os.path.isdir(old):
        open(f"{old}/index.html", "w").write(f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Moved</title>'
            f'<link rel="canonical" href="{SITE}/{new}/"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=/{new}/"></head>'
            f'<body><p>This page moved to <a href="/{new}/">{SITE}/{new}/</a></p></body></html>')
moved("football", "sports")
for l in LEAGUES: moved(f"football/{l['slug']}", f"sports/{l['slug']}-table")

try:
    import build_downloads
    STATIC = build_downloads.build()
except Exception as ex:
    print("[warn] build_downloads failed:", ex); STATIC = []
urls = [("", "daily")] + [(p + "/", "daily") for p in BUILT + [x for x in paths if x not in BUILT]]
_have = {u for u, _ in urls}
urls += [(p, "weekly") for p in STATIC if p not in _have]
sm = "".join(f"  <url><loc>{SITE}/{p}</loc><lastmod>{D}</lastmod>" + (f"<changefreq>{c}</changefreq>" if c else "") + "</url>\n" for p, c in urls)
for extra_page in ("about.html", "terms.html", "cookies.html"):
    if os.path.exists(extra_page): sm += f"  <url><loc>{SITE}/{extra_page}</loc><lastmod>{D}</lastmod></url>\n"
open("sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "</urlset>\n")
print("[ok] sitemap.xml:", len(urls), "urls")
