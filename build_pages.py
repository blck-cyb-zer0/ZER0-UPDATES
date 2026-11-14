#!/usr/bin/env python3
"""Builds crawlable static pages (football/, news/, deals/, coupons/) plus sitemap.xml from the JSON data files."""
import html, json, os
from datetime import datetime, timezone
from urllib.parse import urlparse

SITE = "https://zeroupdates.org"
NOW = datetime.now(timezone.utc)
D, NICE = NOW.strftime("%Y-%m-%d"), NOW.strftime("%d %B %Y").lstrip("0")
e = lambda x: html.escape(str(x if x is not None else ""), quote=True)
ok = lambda u: u if str(u).startswith(("http://", "https://")) else ""

def load(f, key):
    try: return json.load(open(f)).get(key, []) or []
    except Exception: return []

CSS = """:root{--bg:#f4f7fc;--card:#fff;--ink:#0a1a3f;--mut:#5b6785;--line:#e3e8f3;--hi:#2f6bff}
@media(prefers-color-scheme:dark){:root{--bg:#0b0f1a;--card:#131a2b;--ink:#eef2ff;--mut:#9aa6c4;--line:#222c45;--hi:#4d8dff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 Inter,system-ui,sans-serif}
header{background:#05050a;padding:10px 16px}header a{display:inline-flex;align-items:center;gap:8px;line-height:0}header img{height:30px}header .w{height:13px}
main{max-width:760px;margin:0 auto;padding:22px 16px 50px}h1{font:700 27px/1.2 Poppins,Inter,sans-serif;margin:6px 0}
article{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:12px 0}
article h2{font-size:18px;line-height:1.3;margin:0 0 4px}article p{margin:6px 0}.m{color:var(--mut);font-size:14px}a{color:var(--hi)}
.btn{display:inline-block;background:var(--hi);color:#fff!important;text-decoration:none;border-radius:10px;padding:8px 14px;font-weight:600;font-size:14px}
code{border:1px dashed var(--hi);border-radius:6px;padding:2px 8px;font-weight:700}s{color:var(--mut)}
footer{max-width:760px;margin:0 auto;padding:0 16px 40px;font-size:14px;color:var(--mut)}footer a{margin-right:14px}"""

NAV = [("", "Home"), ("football/", "Football"), ("news/", "News"), ("deals/", "Deals"), ("coupons/", "Coupons"),
       ("about.html", "About"), ("terms.html", "Terms"), ("cookies.html", "Cookies")]

def page(slug, title, desc, h1, intro, body, names_urls, extra=""):
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": f"{SITE}/{slug}/",
          "dateModified": D, "isPartOf": {"@id": f"{SITE}/#site"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "name": n, "url": u} for i, (n, u) in enumerate(names_urls[:20])]}}
    foot = "".join(f'<a href="/{p}">{n}</a>' for p, n in NAV)
    out = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}/{slug}/"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/{slug}/"><meta property="og:image" content="{SITE}/og-image.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/favicon-32.png"><style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld)}</script></head><body>
<header><a href="/" aria-label="ZER0 Updates home"><img src="/logo-mark.png" alt=""><img class="w" src="/logo-word.png" alt="ZER0 Updates"></a></header>
<main><h1>{e(h1)}</h1><p class="m">Updated {NICE}. {e(intro)}</p>
{body}
<p><a class="btn" href="/#{slug.split('/')[0] if slug != 'football' else 'sports'}">Open the full interactive site</a></p></main>
<footer>{foot}</footer>{extra}</body></html>"""
    os.makedirs(slug, exist_ok=True)
    open(f"{slug}/index.html", "w").write(out)
    print(f"[ok] {slug}/ ({len(names_urls)} items)")

def league_links():
    try: L = json.load(open("football/leagues.json"))
    except Exception: return ""
    return "<p><strong>Tables and fixtures:</strong> " + " · ".join(f'<a href="/football/{l["slug"]}/">{e(l["name"])}</a>' for l in L) + "</p>"

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

for slug, f, title, desc, h1, intro in [
    ("football", "football_news.json", "Football News Today: Transfers, Match Reports and Injury Updates | ZER0 Updates",
     "Today's football headlines: transfer news, match reports and injury updates, summarised with links to the original sources.",
     "Football News Today", "Transfers, match reports and injury news, summarised and linked to the original sources."),
    ("news", "news.json", "Trending Tech and World News Today | ZER0 Updates",
     "Today's trending technology, business and world news in short summaries, each linked to its original source.",
     "Trending News Today", "Short AI-assisted summaries, each linked to the original article.")]:
    body, nu = articles(load(f, "articles"))
    if nu: page(slug, title, desc, h1, intro, (league_links() if slug == "football" else "") + body, nu)

deals, nu, out = load("deals.json", "deals"), [], []
for d in deals[:40]:
    u = ok(d.get("link"))
    if not u or not d.get("title"): continue
    try: price = f'<p><strong>${e(d["now"])}</strong> <s>${e(d["was"])}</s></p>' if float(d.get("now", 0)) > 0 else ""
    except (TypeError, ValueError): price = ""
    out.append(f'<article><h2>{e(d["title"])}</h2><p class="m">{e(d.get("cat",""))}</p>{price}<p>{e(d.get("desc",""))}</p>'
               f'<p><a class="btn" href="{e(u)}" target="_blank" rel="sponsored nofollow noopener">View deal</a></p></article>')
    nu.append((d["title"], u))
if nu: page("deals", "Today's Best Deals and Discounts | ZER0 Updates",
            "Hand-picked discounts and price drops from across the web, refreshed every day. Some links are affiliate links.",
            "Today's Best Deals", "Prices change fast, so confirm at checkout. Some links are affiliate links.",
            "\n".join(out), nu, '<script src="/affiliate.js"></script>')

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

urls = [("", "daily"), ("about.html", None), ("terms.html", None), ("cookies.html", None)]
urls += [(f"{s}/", "daily") for s in ("football", "news", "deals", "coupons") if os.path.exists(f"{s}/index.html")]
try: urls += [(f'football/{l["slug"]}/', "daily") for l in json.load(open("football/leagues.json"))]
except Exception: pass
sm = "".join(f"  <url><loc>{SITE}/{p}</loc><lastmod>{D}</lastmod>" + (f"<changefreq>{c}</changefreq>" if c else "") + "</url>\n" for p, c in urls)
open("sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "</urlset>\n")
print("[ok] sitemap.xml:", len(urls), "urls")
