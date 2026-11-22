#!/usr/bin/env python3
"""Builds the standalone (no-JavaScript-needed) pages:
   /downloads/, /downloads/<tool>/, /about/, /contact/, /privacy/, /terms/ and assets/site.css.
   Run from the repo root. build_pages.py calls build() automatically, so the GitHub Action keeps them fresh."""
import collections, hashlib, html, json, os, re
from datetime import datetime, timezone

SITE = "https://zeroupdates.org"
GA_ID = "G-MPF36G736Y"
TG_USER, TG_CHANNEL, EMAIL = "https://t.me/CYBERO0", "https://t.me/zer0updates", "cyber@zeroupdates.org"

# Ads, same networks and keys as the main site. Banner sits under the header on every page built here.
# To change or remove them, edit these two values (empty string = off).
AD_SLOT = """<script>(function(){var wide=window.innerWidth>=760;var cfg=wide?{key:'38d724d5189016770fdbc1d90e673a86',height:90,width:728}:{key:'de8bbb25b7e34e2e7d6ac369d3febafe',height:50,width:320};window.atOptions={key:cfg.key,format:'iframe',height:cfg.height,width:cfg.width,params:{}};document.write('<scr'+'ipt src="https://bauval.org/22/'+cfg.key+'"></scr'+'ipt>')})();</script>"""
# Page-level scripts (popunder and overlay), loaded last so they never block the page.
POP_SCRIPTS = """<script data-cfasync="false" src="https://bauval.org/14/40caa574cd409f780dd59da361065949"></script>
<script data-cfasync="false" src="https://abscloud.org/1/e1fce6f1d4f159a7629b4d41ab4f3471"></script>"""

NOW = datetime.now(timezone.utc)
NICE = NOW.strftime("%d %B %Y").lstrip("0")
e = lambda x: html.escape(str(x if x is not None else ""), quote=True)

CSS = """:root{--bg:#f4f7fc;--surface:#fff;--surface-2:#f7f9fd;--text:#0f172a;--muted:#64748b;--line:#e3e8f2;--brand:#1e3cc8;--brand-2:#2f6bff;--shadow:0 1px 2px rgba(15,23,42,.05),0 6px 18px rgba(15,23,42,.06);--radius:14px;
--card:var(--surface);--ink:var(--text);--mut:var(--muted);--hi:var(--brand-2);--warn:#fff7e6;--warnl:#f5d58a}
html[data-theme=dark]{--bg:#0a0f1f;--surface:#121a2e;--surface-2:#0e1526;--text:#e8edf8;--muted:#93a0ba;--line:#1f2a44;--brand:#5b86ff;--brand-2:#7fa1ff;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.35);--warn:#2a2412;--warnl:#5c4a17}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;-webkit-font-smoothing:antialiased;padding-bottom:84px;transition:background .25s,color .25s}
img{max-width:100%}button{font:inherit;color:inherit;cursor:pointer;background:none;border:0}[hidden]{display:none!important}
svg.i{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:0 0 auto}
.topbar{position:sticky;top:0;z-index:50;background:var(--surface);border-bottom:1px solid var(--line)}
.bar{max-width:1180px;margin:0 auto;height:60px;padding:0 16px;display:flex;align-items:center;gap:14px}
.brandlogo{display:inline-flex;align-items:center;gap:8px;background:#05050a;border-radius:12px;padding:5px 12px 5px 8px;line-height:0;text-decoration:none}.brandlogo .lm{height:30px;width:auto}.brandlogo .lw{height:13px;width:auto}
.tabs{display:none;gap:4px}.tabs a{padding:8px 12px;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px;color:var(--muted)}.tabs a:hover,.tabs a[aria-current]{color:var(--brand);background:var(--surface-2)}
.actions-r{margin-left:auto;display:flex;gap:8px}
.icon-btn{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;border:1px solid var(--line);background:var(--surface);color:var(--text)}.icon-btn:active{transform:scale(.93)}
main{max-width:860px;margin:0 auto;padding:18px 16px 40px}
.bottom-nav{position:fixed;left:0;right:0;bottom:0;z-index:60;display:flex;justify-content:space-around;padding:6px 6px calc(6px + env(safe-area-inset-bottom));background:var(--surface);border-top:1px solid var(--line);box-shadow:0 -6px 20px rgba(15,23,42,.07)}
.bottom-nav a,.bottom-nav button{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 0;border-radius:10px;font-size:10.5px;font-weight:500;color:var(--muted);text-decoration:none}.bottom-nav .active{color:var(--brand)}
.scrim{position:fixed;inset:0;background:rgba(2,6,23,.55);opacity:0;pointer-events:none;transition:opacity .2s;z-index:90}.scrim.open{opacity:1;pointer-events:auto}
.drawer{position:fixed;top:0;right:0;bottom:0;width:min(86vw,330px);background:var(--surface);z-index:100;transform:translateX(105%);transition:transform .25s ease;padding:14px;overflow-y:auto;box-shadow:-12px 0 30px rgba(0,0,0,.25)}.drawer.open{transform:none}
.drawer .dh{display:flex;align-items:center;justify-content:space-between;padding:4px 4px 10px}
.drawer a{display:flex;align-items:center;gap:12px;padding:12px;border-radius:12px;text-decoration:none;font-weight:500}.drawer a:hover,.drawer a.active{background:var(--surface-2);color:var(--brand)}
.drawer h4{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:16px 12px 6px;font-weight:600}
@media(min-width:900px){body{padding-bottom:0}.tabs{display:flex}.bottom-nav{display:none}}
h1{font:700 28px/1.2 Poppins,Inter,system-ui,sans-serif;margin:4px 0 8px}h2{font:600 20px/1.3 Poppins,Inter,system-ui,sans-serif;margin:28px 0 8px}h3{font-size:17px;margin:0 0 4px}
p{margin:8px 0}a{color:var(--hi)}.lead{font-size:17px;color:var(--mut)}.m{color:var(--mut);font-size:14px}
.crumbs{font-size:14px;color:var(--mut)}.crumbs a{color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin:12px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 6px 18px rgba(15,23,42,.05)}
.card p{margin:4px 0;font-size:15px}.card a.t{text-decoration:none;color:var(--ink)}.card a.t:hover h3{color:var(--hi)}
.tag{display:inline-block;font-size:12px;font-weight:600;color:var(--hi);border:1px solid var(--line);border-radius:999px;padding:1px 9px;margin-right:6px}
.btn{display:inline-block;background:var(--brand);color:#fff!important;text-decoration:none;border-radius:10px;padding:10px 18px;font-weight:600}
.btn.alt{background:transparent;color:var(--hi)!important;border:1px solid var(--hi)}
.note{background:var(--warn);border:1px solid var(--warnl);border-radius:12px;padding:10px 14px;margin:14px 0;font-size:15px}
.meta{display:flex;flex-wrap:wrap;gap:6px 16px;color:var(--mut);font-size:14px;margin:6px 0 14px}
ol,ul{padding-left:22px}li{margin:4px 0}code,.hash{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13.5px}
code{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:1px 6px}.hash{word-break:break-all;color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:15px}td,th{border-bottom:1px solid var(--line);padding:8px 6px;text-align:left;vertical-align:top}
.ad-wrap{width:100%;margin:0 0 16px}
.ad-label{display:block;text-align:center;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.ad-slot{display:flex;justify-content:center;align-items:center;min-height:58px;overflow-x:auto;border-radius:12px;background:var(--surface);border:1px solid var(--line);padding:4px}
@media(min-width:760px){.ad-slot{min-height:98px}}
footer.site{border-top:1px solid var(--line);padding:24px 16px 30px;text-align:center;font-size:12.5px;color:var(--muted)}footer.site a{margin:0 9px;color:var(--text);text-decoration:none;font-weight:500}footer.site p{max-width:640px;margin:8px auto}
.subtabs{display:flex;gap:6px;margin:14px 0 6px;border-bottom:1px solid var(--line)}
.subtabs a{padding:10px 16px;font-weight:600;text-decoration:none;color:var(--mut);border-bottom:3px solid transparent;margin-bottom:-1px}
.subtabs a[aria-current]{color:var(--hi);border-bottom-color:var(--hi)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.chips a,.chips button{font:inherit;font-size:14px;font-weight:600;text-decoration:none;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:6px 14px;cursor:pointer}
.chips a[aria-current],.chips button[aria-pressed=true]{background:var(--hi);border-color:var(--hi);color:#fff}
.news .card{margin:12px 0}.news h2{font-size:18px;margin:6px 0}.news h2 a{color:var(--ink);text-decoration:none}.news h2 a:hover{color:var(--hi)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--card)}
table.fbt{min-width:100%;font-size:14px}table.fbt th,table.fbt td{padding:8px 6px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap}
table.fbt th{font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}table.fbt td.tn,table.fbt th.tn{text-align:left}
table.fbt td.tn img{width:18px;height:18px;vertical-align:-4px;margin-right:8px;object-fit:contain}
table.fbt tr td:first-child{border-left:4px solid transparent;font-weight:600}
table.fbt tr.z-ucl td:first-child{border-left-color:#2f6bff}table.fbt tr.z-uel td:first-child{border-left-color:#f08a1c}table.fbt tr.z-uecl td:first-child{border-left-color:#1fa971}
table.fbt tr.z-po td:first-child{border-left-color:#a36bff}table.fbt tr.z-rel td:first-child{border-left-color:#e5484d}
table.fbt td.pts{font-weight:700}
.f{display:inline-block;width:18px;height:18px;line-height:18px;border-radius:4px;font:700 11px/18px Inter,system-ui,sans-serif;text-align:center;color:#fff;font-style:normal;margin-right:2px}
.f.W{background:#1fa971}.f.D{background:#8a94ad}.f.L{background:#e5484d}
.key{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--mut);margin:10px 0}.key i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}
.fx{list-style:none;padding:0;margin:8px 0}.fx li{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:8px 0}
.fx time{display:block;font-size:13px;color:var(--mut)}.fx .mt{font-weight:600}.fx .mt b{color:var(--hi);padding:0 6px}.fx small{display:block;color:var(--mut);margin-top:2px}
@media(max-width:560px){.opt{display:none}}
.sh-bar{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0}.sh-bar input{grid-column:1/-1}
.sh-bar input,.sh-bar select{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:12px;background:var(--surface);color:var(--text);font:inherit;font-size:15px}
@media(min-width:700px){.sh-bar{grid-template-columns:2fr 1.3fr 1fr 1fr 1fr}.sh-bar input{grid-column:auto}}
.sh-item h3{margin:0 0 4px;font-size:17px}.sh-item h3 a{color:var(--text);text-decoration:none}.sh-item h3 a:hover{color:var(--brand)}
.sh-meta{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;font-size:12.5px;color:var(--muted);align-items:center}
.sh-links a{margin-right:14px;font-weight:600;font-size:14px}
.tag.warn{color:#b45309;border-color:#f5d58a;background:var(--warn)}
.sh-art{margin:-14px -16px 12px;height:84px;overflow:hidden;border-radius:14px 14px 0 0}.sh-art svg,.hero-art svg{display:block;width:100%;height:100%}
.sh-dl{display:flex;flex-wrap:wrap;gap:8px}.sh-dl .btn{padding:9px 14px;font-size:14px}.sh-dl .btn small{opacity:.8;font-weight:400}
.hero-art{border-radius:16px;overflow:hidden;margin:12px 0;height:120px}
.credit{font-size:13.5px;color:var(--muted);border-top:1px solid var(--line);margin-top:26px;padding-top:12px}
.hero{position:relative;overflow:hidden;border-radius:20px;padding:26px 22px;color:#fff;box-shadow:var(--shadow);margin:0 0 18px;background:radial-gradient(900px 320px at 100% 0,rgba(111,149,255,.5),transparent 60%),linear-gradient(135deg,#0a1a3f,#1e3cc8)}
.hero h1{color:#fff;font-size:clamp(25px,5.4vw,38px);line-height:1.15;letter-spacing:-.01em;margin:8px 0 0;max-width:20em}
.hero .lead,.hero p{color:rgba(255,255,255,.88);font-size:15px;max-width:40em;margin:10px 0 0}
.hero .meta{color:rgba(255,255,255,.85);margin:12px 0 0}.hero .meta b{color:#fff}
.hero .cta{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap}
.hero .btn{background:#fff;color:#0a1a3f!important}
.hero .btn.ghost{background:rgba(255,255,255,.14);color:#fff!important;border:1px solid rgba(255,255,255,.35)}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.85)}
.eyebrow:before{content:"";width:8px;height:8px;border-radius:50%;background:#22c55e}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:6px 14px 10px;box-shadow:var(--shadow);margin:14px 0;scroll-margin-top:76px}
.card{transition:transform .15s ease,box-shadow .15s ease}.card:hover{transform:translateY(-2px)}
.pager{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;align-items:center;margin:24px 0 8px}
.pager button{min-width:40px;height:40px;padding:0 12px;border-radius:12px;border:1px solid var(--line);background:var(--surface);font-weight:600;color:var(--text)}
.pager button[aria-current=page]{background:var(--brand);border-color:var(--brand);color:#fff}
.pager button:disabled{opacity:.4;cursor:default}.pager .gap{padding:0 4px;color:var(--muted)}
.toolgrid{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin:12px 0}
.toolgrid li{margin:0}.toolgrid a{display:block;height:100%;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;text-decoration:none;color:var(--text);box-shadow:var(--shadow);transition:transform .15s ease}
.toolgrid a:hover{transform:translateY(-2px)}.toolgrid a b{display:block;color:var(--hi);margin-bottom:2px}.toolgrid a span{font-size:14px;color:var(--mut)}"""

NAV = [("/sports/", "Football"), ("/downloads/", "Downloads"), ("/news/", "News"), ("/deals/", "Deals"), ("/coupons/", "Coupons"), ("/about/", "About")]

ICONS = {
 "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
 "sports": '<circle cx="12" cy="12" r="9"/><path d="M12 7l4 3-1.5 5h-5L8 10z"/>',
 "news": '<path d="M4 5h13v14H6a2 2 0 0 1-2-2z"/><path d="M17 9h3v8a2 2 0 0 1-2 2"/><path d="M8 9h5M8 13h5"/>',
 "deals": '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.2"/>',
 "coupons": '<path d="M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4z"/><path d="M14 7v10" stroke-dasharray="2 2"/>',
 "downloads": '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
 "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 1-1 1.7M12 17h.01"/>',
 "privacy": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
 "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>', "close": '<path d="M6 6l12 12M18 6L6 18"/>',
 "more": '<circle cx="5" cy="12" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="19" cy="12" r="1.2"/>',
 "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
}
ic = lambda n: f'<svg class="i" viewBox="0 0 24 24" aria-hidden="true">{ICONS[n]}</svg>'
BOTTOM = [("/", "Home", "home"), ("/sports/", "Sports", "sports"), ("/news/", "News", "news"), ("/deals/", "Deals", "deals"), ("/coupons/", "Coupons", "coupons")]
DRAWER = BOTTOM + [("/downloads/", "Vault", "downloads"), ("/downloads/selfhosted/", "Self-Hosted", "downloads")]
DRAWER2 = [("/about/", "About", "help"), ("/contact/", "Contact", "mail"), ("/privacy/", "Privacy Policy", "privacy"), ("/terms/", "Terms of Use", "help")]
THEME_JS = """<script>(function(){var h=document.documentElement,b=document.getElementById('themeBtn'),m=document.getElementById('menuBtn'),d=document.getElementById('drawer'),s=document.getElementById('scrim'),mo=document.getElementById('moreBtn');
var SUN='<svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',MOON='<svg class="i" viewBox="0 0 24 24"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z"/></svg>';
function paint(){b.innerHTML=h.getAttribute('data-theme')==='dark'?SUN:MOON}paint();
b.onclick=function(){var t=h.getAttribute('data-theme')==='dark'?'light':'dark';if(t==='dark')h.setAttribute('data-theme','dark');else h.removeAttribute('data-theme');try{localStorage.setItem('theme',t)}catch(e){}paint()};
function open(o){d.classList.toggle('open',o);s.classList.toggle('open',o)}m.onclick=function(){open(true)};if(mo)mo.onclick=function(){open(true)};s.onclick=function(){open(false)};document.getElementById('closeBtn').onclick=function(){open(false)}})();</script>"""

def shell(path, title, desc, body, ld=None, current=None, robots="index,follow,max-image-preview:large"):
    url = f"{SITE}{path}"
    active = next((h for h, _, _ in BOTTOM if h != "/" and (current or path).startswith(h)), None)
    tabs = "".join(f'<a href="{h}"{" aria-current=page" if h == active or (h in ("/downloads/", "/downloads/selfhosted/") and (current or path).startswith(h)) else ""}>{t}</a>' for h, t, _ in DRAWER)
    bn = "".join(f'<a href="{h}"{" class=active" if h == active else ""}>{ic(i)}<span>{t}</span></a>' for h, t, i in BOTTOM)
    bn += f'<button type="button" id="moreBtn"{" class=active" if not active else ""} aria-label="More">{ic("more")}<span>More</span></button>'
    dr = "".join(f'<a href="{h}"{" class=active" if h == (current or path) else ""}>{ic(i)}{t}</a>' for h, t, i in DRAWER) + "<h4>More</h4>" + "".join(f'<a href="{h}">{ic(i)}{t}</a>' for h, t, i in DRAWER2)
    ad = (f'<div class="ad-wrap" id="adTop"><span class="ad-label">Advertisement</span><div class="ad-slot" id="adSlot">{AD_SLOT}</div></div>') if AD_SLOT.strip() else ""
    ldt = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><base href="/"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">
<meta name="robots" content="{robots}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#f4f7fc">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700&display=swap" rel="stylesheet">
<script>try{{if(localStorage.getItem('theme')==='dark')document.documentElement.setAttribute('data-theme','dark')}}catch(e){{}}</script>
<link rel="stylesheet" href="/assets/site.css?v=7">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA_ID}");</script>
{ldt}</head><body>
<header class="topbar"><div class="bar"><a class="brandlogo" href="/" aria-label="ZER0 Updates home"><img class="lm" src="/logo-mark.png" alt="ZER0 Updates logo" width="46" height="30"><img class="lw" src="/logo-word.png" alt="ZER0 Updates" width="154" height="13"></a>
<nav class="tabs" aria-label="Sections">{tabs}</nav>
<div class="actions-r"><button class="icon-btn" id="themeBtn" type="button" aria-label="Toggle light and dark theme"></button><button class="icon-btn" id="menuBtn" type="button" aria-label="Open menu" aria-controls="drawer">{ic("menu")}</button></div></div></header>
<main>{ad}{body}</main>
<footer class="site"><p><a href="/downloads/">ZER0 Vault</a><a href="/downloads/selfhosted/">Self-Hosted</a><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></p>
<p>&copy; {NOW.year} ZER0 Updates. Some links are affiliate links and we may earn a commission at no extra cost to you. Ads are served by third-party networks.</p></footer>
<nav class="bottom-nav" aria-label="Main">{bn}</nav>
<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer" aria-label="Menu"><div class="dh"><strong>Menu</strong><button class="icon-btn" id="closeBtn" type="button" aria-label="Close menu">{ic("close")}</button></div>{dr}</aside>
{THEME_JS}
<script src="/art.min.js?v=1"></script><script>document.querySelectorAll('[data-art]').forEach(function(e){{e.innerHTML=ZeroArt.svg(e.getAttribute('data-art'),e.getAttribute('data-cat'))}})</script>
<script src="/assistant.min.js?v=1"></script>
{POP_SCRIPTS}
</body></html>"""

def write(path, content):
    d = path.strip("/")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(content)

# ---------------------------------------------------------------- our own tools
SAFE = "Read the script first: it is plain text and takes a minute. Only run files you trust, and check the SHA-256 below matches what you downloaded."
TOOLS = [
 dict(slug="image-compressor", alias="compressor", name="ZERO Bulk Image Compressor", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Image-Compressor.py", src="ZERO-Image-Compressor",
  short="Shrink a whole folder of JPG, PNG and WebP pictures in one run, with three quality levels.",
  what="Reads every JPG, PNG and WebP in a folder called <code>images</code>, saves a smaller copy of each into a folder called <code>compressed</code>, and prints the before and after size. Your originals are never touched.",
  how=["Install <a href=\"https://www.python.org/downloads/\" rel=\"noopener\">Python 3</a>, then run <code>pip install Pillow</code> once.","Put the script in any folder and run it once. It creates an <code>images</code> folder.","Copy your pictures into <code>images</code> and run the script again.","Pick 1 (smallest, quality 60), 2 (quality 80) or 3 (quality 90, the default).","Collect the results from the <code>compressed</code> folder."],
  req="Python 3 and the Pillow library (<code>pip install Pillow</code>).",
  good=["Large phone and camera photos shrink a lot. Images that are already optimised barely change.","The quality setting mainly affects JPEG. PNG files are re-saved with optimisation but will not shrink as much.","Pictures with transparency are converted to a solid background, so transparency is lost.","Only the top level of the <code>images</code> folder is read, not sub-folders."]),
 dict(slug="pdf-merger", alias="pdfmerger", name="ZERO PDF Merger", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-PDF-Merger.py", src="ZERO-PDF-Merger",
  short="Join every PDF in a folder into one file, offline.",
  what="Finds all PDF files in the same folder as the script, joins them in alphabetical order and saves the result as <code>merged.pdf</code>. Nothing is uploaded anywhere, the script has no network code.",
  how=["Install Python 3, then run <code>pip install pypdf</code> once.","Put the script and the PDFs you want to join in one folder.","Name the PDFs so they sort the way you want, for example <code>01-cover.pdf</code>, <code>02-report.pdf</code>.","Run the script. The combined file appears as <code>merged.pdf</code>."],
  req="Python 3 and the pypdf library (<code>pip install pypdf</code>).",
  good=["A PDF that has a password is skipped, unless the password is blank. The tool cannot remove passwords it does not know.","Running it again overwrites the previous <code>merged.pdf</code>, so move it away if you want to keep it.","Bookmarks and form fields in very complex PDFs may not carry over perfectly."]),
 dict(slug="bulk-file-organizer", alias="organizer", name="ZERO Bulk File Organizer", kind="Python script", os="Windows, macOS, Linux", url="https://github.com/user-attachments/files/34872610/zero_organizer.py", size="3 KB",
  short="Rename messy files and sort them into Images, Videos, Music and Documents folders.",
  what="Tidies a folder full of files named like <code>IMG_29383</code> or <code>download (1)</code>. It renames them in a clean numbered pattern and sorts them into folders by type: Images, Videos, Music and Documents.",
  how=["Download the <code>.py</code> file and double-click it, or run <code>python zero_organizer.py</code>.","Paste the path of the folder you want to tidy.","Choose option 1, 2 or 3 when asked.","Check the folder when it finishes."],
  req="Python 3. No extra libraries.",
  good=["Renaming is hard to undo. Run it on a copy of the folder first.","Do not point it at system folders or folders that programs depend on."]),
 dict(slug="auto-cleaner", alias="cleaner", name="ZERO Auto-Cleaner", kind="Python script", os="Windows, Linux", file="files/ZERO-Auto-Cleaner.py", src="ZERO-Auto-Cleaner",
  short="Delete temporary and cache files to free up disk space.",
  what="Empties temporary and cache folders. On Windows that is your user Temp folder, the system Temp folder and the Internet cache. On Linux it is <code>~/.cache</code> and <code>/tmp</code>. It prints how much space it freed. Documents, photos and downloads are not touched.",
  how=["Install Python 3.","Close your browser and other apps first, so fewer files are locked.","Run the script and wait for the total to appear.","Restart the computer if you like."],
  req="Python 3. No extra libraries.",
  good=["Deleted files do not go to the Recycle Bin. They are gone.","Files in use are skipped.","Apps rebuild their caches afterwards, so the first launch can be a little slower and you may be signed out of some apps.","The amount of space you free depends entirely on your machine. Some people free a few GB, others only a few MB.","On Linux, only use it when you know what <code>/tmp</code> is being used for on your machine."]),
 dict(slug="pc-optimizer", alias="optimizer", name="ZERO PC Optimizer", kind="Windows batch file (.bat)", os="Windows", file="files/ZERO-PC-Optimizer.zip", src="ZERO-PC-Optimizer",
  short="A small Windows script that clears temp files, flushes DNS and switches to the High Performance power plan.",
  what="A five-step batch file: (1) deletes files in your Temp folder and in <code>C:\\Windows\\Temp</code>; (2) deletes the Prefetch cache; (3) flushes the DNS cache; (4) force-closes OneDrive, Skype, Teams and Spotify if they are running; (5) switches Windows to the High Performance power plan.",
  how=["Download and unzip the file.","Save any work in OneDrive, Teams, Skype or Spotify, because step 4 closes them without asking.","Right-click the <code>.bat</code> file and choose <b>Run as administrator</b>.","Restart the PC when it finishes."],
  req="Windows. Administrator rights are needed for the system Temp folder, Prefetch and the power plan.",
  good=["It does not clear RAM. Step 4 only closes four apps that often run in the background.","There is no benchmark behind any FPS claim. Gains depend on your hardware and are usually small. Treat it as a tidy-up, not a booster.","High Performance mode uses more power, so a laptop battery drains faster.","Cleaning Prefetch can make the first launch of some programs slightly slower.","Antivirus tools can warn about batch files that close programs. You can open the file in Notepad and read every line."]),
 dict(slug="folder-locker", alias="locker", name="ZERO Folder Locker", kind="Windows batch file (.bat)", os="Windows", file="files/ZERO-Folder-Locker.zip", src="ZERO-Folder-Locker",
  short="Hide a private folder behind a simple password prompt.",
  what="Creates a folder called <code>ZERO Private Folder</code>. Typing <code>LOCK</code> hides it using the Windows Hidden and System attributes. Running the file again and typing the password makes it visible.",
  how=["Download and unzip the file, and put it in a folder of your choice.","Open it in Notepad and change <code>PASS=ZER0-1234</code> to your own password.","Run it once to create the private folder, and put your files inside.","Run it again and type <code>LOCK</code> to hide the folder.","To get it back, run it and type your password."],
  req="Windows.",
  good=["<b>This hides a folder. It does not encrypt it.</b> Anyone who knows how to show hidden and protected system files, or who uses the <code>attrib</code> command, can see it.","The password is stored as plain text inside the <code>.bat</code> file, so anyone who opens the file in Notepad can read it.","Fine for keeping a casual snooper away. Do not use it for anything sensitive.","For real protection use BitLocker, VeraCrypt or a password-protected 7-Zip archive."]),
 dict(slug="wifi-password-revealer", alias="wifi", name="ZERO WiFi Password Revealer", kind="Windows batch file (.bat)", os="Windows", file="files/ZERO-WiFi-Password-Revealer.zip", src="ZERO-WiFi-Password-Revealer",
  short="Show the passwords of Wi-Fi networks your Windows PC has already saved.",
  what="Uses the built-in Windows <code>netsh</code> command to list every Wi-Fi network saved on this PC and print its password. It shows only networks this computer has connected to before. It cannot reveal the password of a network you have never joined.",
  how=["Download and unzip the file.","Right-click the <code>.bat</code> file and choose <b>Run as administrator</b>.","Read the list of network names and passwords."],
  req="Windows. Run as administrator for best results.",
  good=["It only reads data already stored on your own PC. Nothing is sent anywhere.","Use it for your own networks, for example to share your home Wi-Fi password with a guest. Do not use it on a computer that is not yours.","A similar Python version that lists the same information is on the <a href=\"/wifiviewer/\">WiFi Password Viewer</a> page."]),
 dict(slug="wifi-password-viewer", alias="wifiviewer", name="ZERO WiFi Password Viewer", kind="Python script", os="Windows, Linux", file="files/ZERO-WiFi-Password-Viewer.py", src="ZERO-WiFi-Password-Viewer",
  short="Python version of the Wi-Fi password viewer: lists saved networks on Windows and Linux.",
  what="On Windows it prints the name and password of every Wi-Fi network saved on the PC. On Linux it lists the saved network files from NetworkManager and tells you the command to read a password with <code>sudo</code>.",
  how=["Install Python 3.","On Windows, open Command Prompt as administrator and run <code>python ZERO-WiFi-Password-Viewer.py</code>.","On Linux, run the script, then use <code>sudo cat</code> on the file it names to read a password."],
  req="Python 3. Administrator (Windows) or sudo (Linux) to read passwords.",
  good=["On Linux the script lists names only. Reading the password itself needs the sudo command shown at the end.","It does not work on phones.","Only use it on your own computer.","If you only need Windows and do not want to install Python, use the <a href=\"/wifi/\">batch file version</a>."]),
 dict(slug="playlist-to-mp3", alias="playlist", name="ZERO Playlist to MP3", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Playlist-to-MP3.py", src="ZERO-Playlist-to-MP3",
  short="Turn a YouTube playlist or single video into numbered MP3 files using yt-dlp.",
  what="A friendly wrapper around the open-source <a href=\"https://github.com/yt-dlp/yt-dlp\" rel=\"noopener\">yt-dlp</a>. You paste a link and it saves the audio as MP3 in a folder called <code>MP3 Downloads</code>, numbered by playlist position, with the title and thumbnail embedded.",
  how=["Install Python 3.","Run <code>pip install yt-dlp</code>.","Install <a href=\"https://ffmpeg.org/download.html\" rel=\"noopener\">ffmpeg</a> and make sure it is on your PATH.","Run the script and paste a playlist or video link."],
  req="Python 3, yt-dlp and ffmpeg.",
  good=["Only download content you own, content under a licence that allows it, or content you have permission to save. Downloading from YouTube can break its Terms of Service.","The script asks for the best audio quality. It cannot make audio better than the source, and most YouTube audio is well below 320 kbps.","Long playlists can take a while.","Keep yt-dlp updated with <code>pip install -U yt-dlp</code> because sites change often."]),
 dict(slug="subtitle-downloader", alias="subtitles", name="ZERO Subtitle Downloader", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Subtitle-Downloader.py", src="ZERO-Subtitle-Downloader",
  short="Find English subtitles for the video files in a folder, using the subliminal library.",
  what="Looks for video files (mp4, mkv, avi, mov, webm) in the same folder as the script, searches for English subtitles with the <code>subliminal</code> library and saves the best match next to each video.",
  how=["Install Python 3, then run <code>pip install subliminal</code>.","Put the script in the same folder as your video.","Make sure the file name looks like the title, for example <code>Movie.Name.2020.1080p.mkv</code>.","Run the script. The <code>.srt</code> file appears next to the video."],
  req="Python 3, the subliminal library and an internet connection.",
  good=["English only.","Results depend on the file name. Messy names find fewer matches.","Subtitle sites sometimes limit requests, so a miss does not always mean no subtitle exists.","Always check that the subtitle matches your version of the video."]),
 dict(slug="unfollower-tracker", alias="unfollow", name="ZERO Unfollower Tracker", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Unfollower-Tracker.py", src="ZERO-Unfollower-Tracker",
  short="See who you follow on Instagram that does not follow you back, using your own data export. No login.",
  what="Compares the followers and following lists from your own Instagram data download. It prints the accounts you follow that do not follow you back, and the accounts that follow you that you do not follow, and saves the first list to <code>unfollower-result.txt</code>.",
  how=["In Instagram go to Settings, then <b>Download your information</b>, and request a download in JSON format.","Unzip it and copy <code>followers_1.json</code> and <code>following.json</code> next to the script.","Run the script with Python 3.","Read the lists on screen or in <code>unfollower-result.txt</code>."],
  req="Python 3. No extra libraries, no login, no internet connection.",
  good=["It works with Instagram data only, not TikTok.","It shows who does not follow back right now. To spot new unfollowers, run it on two exports taken at different times and compare the lists.","Instagram sometimes changes its export format, so the script may need an update."]),
 dict(slug="duplicate-finder", alias="duplicates", name="ZERO Duplicate File Finder", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Duplicate-Finder.py", src="ZERO-Duplicate-Finder",
  short="Find identical files in a folder and optionally move the extra copies aside. Nothing is deleted.",
  what="Scans a folder and every folder inside it, groups files that are exactly the same (same size first, then the same SHA-256 fingerprint), saves the list to <code>duplicates-report.txt</code> and tells you how much space the extra copies use. It can then move the extra copies into a folder called <code>duplicates-moved</code>.",
  how=["Install Python 3 (no extra libraries needed).","Run the script and drag the folder you want to check into the window, or paste its path.","Read the summary, and open <code>duplicates-report.txt</code> to see every group.","Type <code>y</code> if you want the extra copies moved into <code>duplicates-moved</code>. The first file of each group stays where it is."],
  req="Python 3. No extra libraries.",
  good=["It never deletes anything. Review the <code>duplicates-moved</code> folder, then delete it yourself if you agree.","It compares what is inside the files, not their names, so two different names with the same content count as duplicates.","Photos that look the same but were saved or compressed differently are not exact copies, so they are not found.","Empty files are ignored.","Big folders take a while, because every file that shares a size with another file is read in full."]),
 dict(slug="password-generator", alias="password", name="ZERO Password Generator", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Password-Generator.py", src="ZERO-Password-Generator",
  short="Make strong random passwords on your own computer. Nothing is saved or sent.",
  what="Creates random passwords of the length you choose, with an option to add symbols and to avoid look-alike characters such as O and 0. It uses Python's <code>secrets</code> module, which is built for security, and shows a rough strength rating in bits. Every password contains at least one lowercase letter, one capital, one digit and, if you chose them, one symbol.",
  how=["Install Python 3 (no extra libraries needed).","Run the script.","Choose a length (16 or more is a good default) and how many passwords you want.","Copy the one you like into your password manager."],
  req="Python 3. No extra libraries, no internet connection.",
  good=["Nothing is written to disk and nothing is sent anywhere. Close the window and the passwords are gone.","Use a different password for every account, and a password manager so you do not have to remember them.","The strength figure is an estimate for random characters. A short password stays weak however it is made."]),
 dict(slug="hash-checker", alias="hashcheck", name="ZERO File Hash Checker", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Hash-Checker.py", src="ZERO-Hash-Checker",
  short="Check that a download is exactly the file the publisher meant you to get.",
  what="Works out a file's checksum (SHA-256, SHA-1 or MD5) and, if you paste the checksum the publisher gave you, tells you whether the two match. A mismatch means the file is damaged or has been changed.",
  how=["Install Python 3 (no extra libraries needed).","Run the script and drag the file into the window, or paste its path.","Pick SHA-256 unless the publisher lists a different type.","Paste the published checksum when asked, or press Enter to just see the checksum."],
  req="Python 3. No extra libraries, no internet connection.",
  good=["A match proves the file was not damaged or changed after the checksum was published. It does not prove the file is harmless, so only trust files from sources you trust.","Get the checksum from the publisher's official page, not from the same place as the download.","SHA-1 and MD5 are older and weaker. Use SHA-256 when you can.","Very large files take a moment to read."]),
 dict(slug="qr-code-maker", alias="qr", name="ZERO QR Code Maker", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-QR-Code-Maker.py", src="ZERO-QR-Code-Maker",
  short="Turn a link, some text or your Wi-Fi details into a QR code image.",
  what="Makes a PNG QR code for a link or any text, or for a Wi-Fi network so guests can join by scanning with their phone camera. Images are saved in a folder called <code>qr-codes</code> next to the script.",
  how=["Install Python 3, then run <code>pip install \"qrcode[pil]\"</code> once.","Run the script and choose 1 for a link or text, or 2 for Wi-Fi.","Type the link, or the Wi-Fi name, security type and password.","Open the image in <code>qr-codes</code> and scan it with your phone to test it before you print or share it."],
  req="Python 3 and the qrcode library (<code>pip install \"qrcode[pil]\"</code>).",
  good=["A Wi-Fi QR code contains the password in readable form for anyone who scans it. Only share it with people you would give the password to.","Most modern phone cameras can join a Wi-Fi network from a QR code. Some older phones cannot.","Everything is made on your computer. No website sees your link or password.","Always scan the finished code once to check it works."]),
 dict(slug="bulk-renamer", alias="renamer", name="ZERO Bulk Renamer", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Bulk-Renamer.py", src="ZERO-Bulk-Renamer",
  short="Rename lots of files at once, with a preview first and an undo.",
  what="Renames the files directly inside a folder in one go. You can number them (<code>trip-001.jpg</code>, <code>trip-002.jpg</code> and so on), find and replace text in the names, or tidy them up so they are lowercase with dashes instead of spaces. It shows you what will change and asks before it does anything, and it keeps an undo file.",
  how=["Install Python 3 (no extra libraries needed).","Run the script and drag the folder in, or paste its path.","Choose 1 (number them), 2 (find and replace) or 3 (tidy up).","Read the preview, type <code>y</code> to go ahead.","Changed your mind? Run it again and choose <code>U</code> to put the old names back."],
  req="Python 3. No extra libraries.",
  good=["It only renames files directly inside the folder you give it, not files in sub-folders, and it skips hidden files.","If a new name would clash with a file that already exists, that file is left alone.","The undo file, <code>rename-undo.json</code>, remembers only the most recent rename in that folder. Undo before you rename again.","Try it on a copy of the folder first if the files matter a lot."]),
 dict(slug="folder-size-report", alias="foldersize", name="ZERO Folder Size Report", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Folder-Size-Report.py", src="ZERO-Folder-Size-Report",
  short="See which folders and files take up the most space on your drive.",
  what="Measures a folder and lists the biggest things directly inside it and the 20 biggest files anywhere inside it, with sizes in plain units. A copy of the report is saved as <code>size-report.txt</code>. It only reads, it never changes or deletes anything.",
  how=["Install Python 3 (no extra libraries needed).","Run the script and drag the folder you want to check into the window.","Wait while it measures. Big folders can take a minute.","Read the lists, then decide yourself what to clean up."],
  req="Python 3. No extra libraries.",
  good=["It cannot read folders you do not have permission to open. Those are skipped, so the total can be a little low.","Shortcuts and symbolic links are not followed, so nothing is counted twice.","Point it at a whole drive for an overview, but expect it to take longer.","Use it with the Duplicate File Finder to see where copies are wasting space."]),
]

def sha_and_size(rel):
    try:
        b = open(rel, "rb").read()
    except Exception:
        return None, None
    s = len(b)
    return hashlib.sha256(b).hexdigest(), (f"{s/1024:.1f} KB" if s >= 1024 else f"{s} B")

H1S = {
 "image-compressor": "Free Bulk Image Compressor: Shrink JPG, PNG and WebP Photos in One Run",
 "pdf-merger": "Free PDF Merger Script: Combine Multiple PDF Files Into One, Offline",
 "bulk-file-organizer": "Bulk File Organizer: Rename and Sort Messy Files Into Folders Automatically",
 "auto-cleaner": "Temp File Cleaner for Windows and Linux: Free Up Disk Space Fast",
 "pc-optimizer": "ZERO PC Optimizer: Clear Temp Files, Flush DNS and Set High Performance (Windows .bat)",
 "folder-locker": "Folder Locker for Windows: Hide a Private Folder Behind a Password Prompt (.bat)",
 "wifi-password-revealer": "Show Saved Wi-Fi Passwords on Windows: Free WiFi Password Revealer (.bat)",
 "wifi-password-viewer": "WiFi Password Viewer for Windows and Linux: List Your Saved Networks (Python)",
 "playlist-to-mp3": "Playlist to MP3 Script: Save Audio as Numbered MP3 Files With yt-dlp",
 "subtitle-downloader": "Free Subtitle Downloader: Find English Subtitles for Your Video Files Automatically",
 "duplicate-finder": "Free Duplicate File Finder: Find Identical Files and Free Up Disk Space (Python)",
 "password-generator": "Free Password Generator Script: Strong Random Passwords, Made Offline",
 "hash-checker": "File Hash Checker: Verify a Download With SHA-256, SHA-1 or MD5",
 "qr-code-maker": "QR Code Maker: Create QR Codes for Links, Text and Wi-Fi Networks (Python)",
 "bulk-renamer": "Bulk File Renamer: Number, Find and Replace or Tidy File Names, With Undo",
 "folder-size-report": "Folder Size Report: Find the Biggest Files and Folders Taking Up Your Disk Space",
 "unfollower-tracker": "Instagram Unfollower Tracker: See Who Does Not Follow You Back From Your Own Data Export",
}

def tool_page(t, others):
    path = tool_path(t)
    href = "/" + t["file"] if t.get("file") else t["url"]
    dl_attr = f'download rel="noopener"' if t.get("file") else 'rel="noopener nofollow" target="_blank"'
    sha, size = sha_and_size(t["file"]) if t.get("file") else (None, t.get("size"))
    fname = os.path.basename(t["file"]) if t.get("file") else t["url"].rsplit("/", 1)[-1]
    how = "".join(f"<li>{x}</li>" for x in t["how"])
    good = "".join(f"<li>{x}</li>" for x in t["good"])
    rel = "".join(f'<li><a href="{tool_path(o)}"><b>{e(o["name"])}</b><span>{e(o["short"])}</span></a></li>' for o in others if o["slug"] != t["slug"])
    hashblock = f'<p class="m">SHA-256 of <code>{e(fname)}</code>:</p><p class="hash">{sha}</p><p class="m">On Windows: <code>certutil -hashfile {e(fname)} SHA256</code>. On macOS or Linux: <code>shasum -a 256 {e(fname)}</code>.</p>' if sha else '<p class="m">This file is hosted on GitHub. We could not publish a checksum for it here, so open it in a text editor and read it before running.</p>'
    body = f"""<p class="crumbs"><a href="/">Home</a> / <a href="/downloads/">ZER0 Vault</a> / {e(t['name'])}</p>
<section class="hero"><span class="eyebrow">Free download &middot; ZER0 Vault</span>
<h1>{e(H1S.get(t['slug'], t['name']))}</h1><p class="lead">{e(t['short'])}</p>
<div class="meta"><span><b>Type:</b> {e(t['kind'])}</span><span><b>Works on:</b> {e(t['os'])}</span><span><b>Version:</b> 1.0</span>{f'<span><b>Size:</b> {size}</span>' if size else ''}<span><b>Price:</b> Free</span></div>
<div class="cta"><a class="btn" href="{href}" {dl_attr}>Download {e(fname)}</a><a class="btn ghost" href="/downloads/">Back to the Vault</a></div></section>
<p class="m">Short link to share: <b>zeroupdates.org/{e(t.get("alias", t["slug"]))}</b></p>
<h2>What it does</h2><p>{t['what']}</p>
<h2>How to use it</h2><ol>{how}</ol>
<h2>Requirements</h2><p>{t['req']}</p>
<h2>Good to know</h2><ul>{good}</ul>
<h2>Is it safe?</h2><p>{SAFE}</p>{hashblock}
<p class="note">Made by ZER0 Updates and provided as is, with no warranty. You are responsible for how you use it. Back up anything important before running a tool that changes or deletes files.</p>
<h2>More tools</h2><ul class="toolgrid">{rel}</ul>"""
    ld = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": t["name"], "description": t["short"],
          "applicationCategory": "UtilitiesApplication", "operatingSystem": t["os"], "softwareVersion": "1.0", "url": f"{SITE}{path}",
          "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "publisher": {"@type": "Organization", "name": "ZER0 Updates", "url": SITE}}
    write_page(path, shell(path, f"{t['name']} - Free Download | ZER0 Updates", t["short"], body, ld, "/downloads/"))
    return path

# ---------------------------------------------------------------- third-party apps from catalog.json
def third_party():
    """Everything in catalog.json that is not one of the scripts above (those have their own guide pages).
    Anything you add later, including new ZERO tools, still shows up here."""
    try: cat = json.load(open("catalog.json", encoding="utf-8"))
    except Exception: return []
    norm = lambda x: re.sub(r"[^a-z0-9]", "", str(x).lower())
    ours = {norm(t["name"]) for t in TOOLS} | {norm(t["src"]) for t in TOOLS if t.get("src")}
    seen, out = set(), []
    for x in cat:
        title = str(x.get("title", "")).strip()
        if not title or norm(title) in ours: continue
        key = (title.lower(), str(x.get("category", "")).upper(), str(x.get("tag", "")))
        if key in seen: continue
        seen.add(key); out.append(x)
    return out

def first_sentence(s, n=170):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if len(s) <= n: return s
    cut = s[:n].rsplit(" ", 1)[0]
    return cut + "..."

RESERVED = {"about", "contact", "privacy", "terms", "sports", "news", "deals", "coupons", "downloads", "files", "crests",
            "assets", "football", "index", "scripts", "images", "fonts", "static", "api", "selfhosted"}
ALIAS_MARK = "<!-- zer0-alias -->"
ALIAS_DIRS = []


def kebab(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "app"


PAGE_MARK = "<!-- zer0-vault-page -->"


def owned(dir_):
    """True if /dir_/ is free or was written by this builder (so we never overwrite anything of yours)."""
    p = os.path.join(dir_, "index.html")
    if not os.path.exists(p): return not os.path.exists(dir_)
    head = open(p, encoding="utf-8", errors="ignore").read(600)
    return ALIAS_MARK in head or PAGE_MARK in head


def root_ok(name):
    name = kebab(name)
    return bool(name) and name not in RESERVED and owned(name)


def tool_path(t):
    al = kebab(t.get("alias", t["slug"]))
    return f"/{al}/" if root_ok(al) else f"/downloads/{t['slug']}/"


def app_path(slug):
    return f"/{slug}/" if root_ok(slug) else f"/downloads/{slug}/"


def write_page(path, html_):
    write(path, html_.replace("<!DOCTYPE html>", "<!DOCTYPE html>" + PAGE_MARK, 1))
    if path.count("/") == 2: ALIAS_DIRS.append(path.strip("/"))


def redirect_stub(dir_, target, title, desc):
    """Old address -> the page's real address. Keeps old links working."""
    full = SITE + target
    page = f"""<!DOCTYPE html>{ALIAS_MARK}
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | ZER0 Vault</title><meta name="description" content="{e(desc)}"><meta name="robots" content="noindex,follow">
<link rel="canonical" href="{full}"><meta http-equiv="refresh" content="0;url={target}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{full}"><meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image"><script>location.replace("{target}")</script></head>
<body><p><a href="{target}">Continue to {e(title)}</a></p></body></html>"""
    os.makedirs(dir_, exist_ok=True)
    open(os.path.join(dir_, "index.html"), "w", encoding="utf-8").write(page)


def clean_desc(text, limit=480):
    t = re.split(r"(?i)what.?s new|changelog|release notes|\n\s*\n\s*[-*\u2022]", str(text or ""))[0]
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= limit: return t
    cut = t[:limit]
    return (cut[: cut.rfind(". ") + 1] if ". " in cut else cut.rsplit(" ", 1)[0] + "...")


HOW = {
    "ANDROID": ["Download the file. It ends in <code>.apk</code>.", "Open it from your notifications or your Files app.", "If Android blocks it, allow <b>Install unknown apps</b> for your browser or file manager when asked.", "Tap <b>Install</b>. To update later, download the newer version or use the app's own updater."],
    "WINDOWS": ["Download the file. Installers end in <code>.exe</code> or <code>.msi</code>; portable builds are a <code>.zip</code> you unzip.", "Run the installer, or unzip the folder and open the program inside.", "Windows may show a SmartScreen warning for lesser-known publishers. Only continue if you downloaded from the official page."],
    "LINUX": ["Download the file for your system.", "For an <code>.AppImage</code>, right-click it, allow it to run as a program, then open it. For a <code>.deb</code>, install it with your software installer or <code>sudo apt install ./file.deb</code>.", "Many distributions also have it in their own software store, which keeps it updated for you."],
}


def app_entries():
    """Every catalog.json item that does not already have a hand-written tool page, with a unique page name."""
    used = {t["slug"] for t in TOOLS}
    out = []
    for x in third_party():
        slug = kebab(x["title"])
        if slug in used: slug = slug + "-" + kebab(x.get("category", "app"))
        n = 2
        while slug in used: slug, n = f"{kebab(x['title'])}-{n}", n + 1
        used.add(slug)
        out.append((slug, x))
    return out


def app_page(slug, x, siblings):
    title = str(x["title"]).strip()
    cat = str(x.get("category", "")).upper()
    mine = re.sub(r"[^a-z0-9]", "", title.lower()).startswith("zero")
    url = x.get("url", "")
    href = ("/" + url) if url and not url.startswith("http") else url
    desc = clean_desc(x.get("description")) or "A free app listed in the ZER0 Vault."
    short = first_sentence(desc, 150)
    plat = {"ANDROID": "Android", "WINDOWS": "Windows", "LINUX": "Linux", "PYTHON": "Python", "SCRIPTS": "Scripts", "TOOLS": "Tools"}.get(cat, cat.title() or "Any")
    meta = f"<span><b>Platform:</b> {e(plat)}</span>"
    for label, key in (("Version", "version"), ("Size", "size"), ("License", "license"), ("Updated", "updated")):
        if x.get(key): meta += f"<span><b>{label}:</b> {e(str(x[key])[:24])}</span>"
    meta += "<span><b>Price:</b> Free</span>"
    how = "".join(f"<li>{i}</li>" for i in HOW.get(cat, ["Open the download link.", "Follow the developer's own instructions for your device."]))
    who = ("This one is made by ZER0 Updates." if mine else "We did not make this app and we do not host the file. The button goes straight to the developer's own download.")
    related = "".join(f'<li><a href="{tool_path(o)}"><b>{e(o["name"])}</b><span>{e(o["short"])}</span></a></li>' for o in TOOLS[:6])
    body = f"""<p class="crumbs"><a href="/">Home</a> / <a href="/downloads/">ZER0 Vault</a> / {e(title)}</p>
<section class="hero"><span class="eyebrow">Vault app &middot; ZER0 Updates</span>
<h1>{e(title)}: {e(short)}</h1>
<div class="meta">{meta}</div>
<div class="cta"><a class="btn" href="{e(href)}" rel="noopener nofollow" target="_blank">Download {e(title)}</a><a class="btn ghost" href="/downloads/">Back to the Vault</a></div></section>
<p class="m">Short link to share: <b>zeroupdates.org/{e(slug)}</b></p>
<h2>What it is</h2><p>{e(desc)}</p>
<h2>How to install</h2><ol>{how}</ol>
<h2>Before you download</h2><p>{who} Check that the version and publisher look right, keep the app updated, and only install software from sources you trust.</p>
<p class="note">Listings are refreshed automatically, so version numbers and links can change. If something looks wrong, <a href="/contact/">tell us</a>.</p>
<h2>More from the Vault</h2><ul class="toolgrid">{related}</ul>"""
    path = app_path(slug)
    write_page(path, shell(path, f"{title} Download | ZER0 Vault", short or desc[:150], body, None, "/downloads/", robots="noindex,follow"))
    return path


SH_FUNCS = r"""/*F*/
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function safeUrl(u){return /^https?:\/\//i.test(u||'')?u:''}
function filterItems(list,f){var words=(f.q||'').trim().toLowerCase().split(/\s+/).filter(Boolean);
 return list.filter(function(i){
  if(f.dl&&!(i.dl&&i.dl.length))return false;
  if(f.tag&&i.t.indexOf(f.tag)<0)return false;
  if(f.plat&&i.p.indexOf(f.plat)<0)return false;
  if(f.lic&&i.l.indexOf(f.lic)<0)return false;
  if(!words.length)return true;
  var hay=(i.n+' '+i.d+' '+i.t.join(' ')+' '+i.p.join(' ')).toLowerCase();
  return words.every(function(w){return hay.indexOf(w)>=0});});}
function sortItems(list,by){var a=list.slice();
 if(by==='name')a.sort(function(x,y){return x.n.toLowerCase()<y.n.toLowerCase()?-1:1});
 else if(by==='updated')a.sort(function(x,y){var p=y.u||'',q=x.u||'';return p<q?-1:p>q?1:0});
 else a.sort(function(x,y){return y.st-x.st});
 return a;}
function fmtStars(n){return n>=1000?(n/1000).toFixed(1)+'k':String(n)}
function fmtSize(b){return b>=1048576?(b/1048576).toFixed(1)+' MB':b>=1024?Math.round(b/1024)+' KB':''}
function card(i){
 var art=(typeof ZeroArt!=='undefined')?'<div class="sh-art">'+ZeroArt.svg(i.n,(i.t&&i.t[0])||'')+'</div>':'';
 var h='<article class="card sh-item">'+art+'<h3>'+esc(i.n)+'</h3><p>'+esc(i.d)+'</p><div class="sh-meta">';
 (i.t.slice(0,2)).forEach(function(t){h+='<span class="tag">'+esc(t)+'</span>'});
 if(i.l[0])h+='<span>'+esc(i.l.slice(0,2).join(' / '))+'</span>';
 if(i.p.length)h+='<span>'+esc(i.p.slice(0,3).join(', '))+'</span>';
 if(i.st)h+='<span>\u2605 '+fmtStars(i.st)+'</span>';
 if(i.u)h+='<span>Updated '+esc(i.u)+'</span>';
 if(i.af)h+='<span class="tag warn" title="The source list marks this project with a caveat, for example it relies on a non-free service.">\u26a0 caveat</span>';
 h+='</div><div class="sh-dl">';
 if(i.dl&&i.dl.length){i.dl.forEach(function(d){if(safeUrl(d[1]))h+='<a class="btn" href="'+esc(d[1])+'" rel="noopener nofollow">Download'+(d[0]!=='Download'?' for '+esc(d[0]):'')+(fmtSize(d[2])?' <small>'+fmtSize(d[2])+'</small>':'')+'</a>'});}
 else h+='<span class="m">No direct download. This one is installed with Docker or from source.</span>';
 return h+'</div></article>';}
/*END*/"""

SH_WIRE = r"""(function(){
var PER=24,items=null,st={q:'',tag:'',plat:'',lic:'',dl:true,sort:'stars',page:1};
var $=function(id){return document.getElementById(id)};
function nums(cur,total){var o=[],i;if(total<=7){for(i=1;i<=total;i++)o.push(i);return o}
 if(cur<=4){for(i=1;i<=5;i++)o.push(i);o.push(0,total);return o}
 if(cur>=total-3){o.push(1,0);for(i=total-4;i<=total;i++)o.push(i);return o}
 o.push(1,0);for(i=cur-1;i<=cur+1;i++)o.push(i);o.push(0,total);return o}
function pager(cur,total){var nav=$('shpager');if(total<=1){nav.innerHTML='';return}
 var h='<button type="button" data-p="'+(cur-1)+'"'+(cur<=1?' disabled':'')+' aria-label="Previous page">&lsaquo; Prev</button>';
 nums(cur,total).forEach(function(x){h+=x===0?'<span class="gap">&hellip;</span>':'<button type="button" data-p="'+x+'"'+(x===cur?' aria-current="page"':'')+' aria-label="Page '+x+'">'+x+'</button>'});
 h+='<button type="button" data-p="'+(cur+1)+'"'+(cur>=total?' disabled':'')+' aria-label="Next page">Next &rsaquo;</button>';
 nav.innerHTML=h}
function render(go){
 var list=sortItems(filterItems(items,st),st.sort),total=Math.max(1,Math.ceil(list.length/PER));
 if(st.page>total)st.page=total;if(st.page<1)st.page=1;
 var from=(st.page-1)*PER,box=$('shlist');
 box.innerHTML=list.slice(from,from+PER).map(card).join('')||'<p class="m">Nothing matches. Try fewer words, clear a filter, or untick "Direct downloads only".</p>';
 $('shcount').textContent=list.length?'Showing '+(from+1).toLocaleString()+'\u2013'+Math.min(from+PER,list.length).toLocaleString()+' of '+list.length.toLocaleString()+' apps \u00b7 page '+st.page+' of '+total:'No apps match';
 pager(st.page,total);
 if(go){try{$('shtop').scrollIntoView({behavior:'smooth',block:'start'})}catch(e){}}
 try{var p=new URLSearchParams();['q','tag','plat','lic'].forEach(function(k){if(st[k])p.set(k,st[k])});if(st.sort!=='stars')p.set('sort',st.sort);if(!st.dl)p.set('all','1');if(st.page>1)p.set('page',st.page);
  history.replaceState(null,'',location.pathname+(p.toString()?'?'+p:''))}catch(e){}}
function bind(id,key){var el=$(id),t;el.addEventListener(key==='q'?'input':'change',function(){clearTimeout(t);t=setTimeout(function(){st[key]=key==='dl'?el.checked:el.value;st.page=1;if(items)render()},key==='q'?150:0)})}
bind('shq','q');bind('shtag','tag');bind('shplat','plat');bind('shlic','lic');bind('shsort','sort');bind('shdl','dl');
$('shpager').addEventListener('click',function(e){var b=e.target.closest?e.target.closest('button[data-p]'):null;if(!b||b.disabled||!items)return;st.page=parseInt(b.getAttribute('data-p'),10)||1;render(true)});
try{var p=new URLSearchParams(location.search);['q','tag','plat','lic'].forEach(function(k){if(p.get(k)){st[k]=p.get(k);var el=$({q:'shq',tag:'shtag',plat:'shplat',lic:'shlic'}[k]);if(el)el.value=st[k]}});if(p.get('sort')){st.sort=p.get('sort');$('shsort').value=st.sort}if(p.get('all')){st.dl=false;$('shdl').checked=false}if(p.get('page'))st.page=parseInt(p.get('page'),10)||1}catch(e){}
fetch('/assets/selfhosted.json').then(function(r){return r.json()}).then(function(d){items=d.items||[];render()}).catch(function(){});
})();"""


def selfhosted_page():
    try:
        data = json.load(open("assets/selfhosted.json", encoding="utf-8"))
    except Exception:
        print("[info] assets/selfhosted.json not found yet, Self-Hosted page skipped"); return None
    items, meta = data.get("items", []), data.get("meta", {})
    n = len(items)
    if n < 50: return None
    with_dl = [i for i in items if i.get("dl")]
    top = [{"n": i["n"], "d": i["d"][:150], "t": (i["t"] or [""])[0], "dl": i["dl"][:1]} for i in with_dl[:12]]
    json.dump({"count": n, "withDl": len(with_dl), "items": top}, open("assets/selfhosted-top.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    count = lambda key: collections.Counter(x for i in items for x in i[key]).most_common()
    opt = lambda pairs, lim: "".join(f'<option value="{e(k)}">{e(k)} ({v})</option>' for k, v in pairs[:lim])
    size = lambda b: (f"{b/1048576:.1f} MB" if b >= 1048576 else (f"{b//1024} KB" if b >= 1024 else ""))
    def ssr(i):
        btns = "".join(f'<a class="btn" href="{e(d[1])}" rel="noopener nofollow">Download{"" if d[0] == "Download" else " for " + e(d[0])}{" <small>" + size(d[2]) + "</small>" if size(d[2]) else ""}</a>' for d in i["dl"] if str(d[1]).startswith("http"))
        chips = "".join(f'<span class="tag">{e(t)}</span>' for t in i["t"][:2])
        extra = (f'<span>{e(" / ".join(i["l"][:2]))}</span>' if i["l"] else "") + (f'<span>{e(", ".join(i["p"][:3]))}</span>' if i["p"] else "")
        return f'<article class="card sh-item"><h3>{e(i["n"])}</h3><p>{e(i["d"])}</p><div class="sh-meta">{chips}{extra}</div><div class="sh-dl">{btns}</div></article>'
    first = "".join(ssr(i) for i in with_dl[:24])
    body = f"""<div class="subtabs"><a href="/downloads/">Vault</a><a href="/downloads/selfhosted/" aria-current="page">Self-Hosted</a></div>
<section class="hero"><span class="eyebrow">Open-source directory</span>
<h1>Self-Hosted Apps Directory: {n:,} Free Software Projects You Can Run on Your Own Server</h1>
<p class="lead">Search a long list of open-source apps you can run yourself, from photo galleries and password managers to wikis, finance trackers and home automation. Filter by category, platform or license, and download the latest version straight from here.</p>
<div class="cta"><a class="btn" href="#shtop">Browse the apps</a><a class="btn ghost" href="/downloads/">Open the Vault</a></div></section>
<div class="panel" id="shtop">
<div class="sh-bar"><input id="shq" type="search" placeholder="Search apps, e.g. photos, passwords, wiki, budget" aria-label="Search apps" autocomplete="off">
<select id="shtag" aria-label="Category"><option value="">All categories</option>{opt(count("t"), 90)}</select>
<select id="shplat" aria-label="Platform"><option value="">Any platform</option>{opt(count("p"), 30)}</select>
<select id="shlic" aria-label="License"><option value="">Any license</option>{opt(count("l"), 25)}</select>
<select id="shsort" aria-label="Sort by"><option value="stars">Most stars</option><option value="updated">Recently updated</option><option value="name">A to Z</option></select></div>
<p class="m"><label><input type="checkbox" id="shdl" checked> Direct downloads only ({len(with_dl):,} of {n:,} apps have one)</label></p>
</div>
<p id="shcount" class="m">Showing 1&ndash;24 of {len(with_dl):,} apps</p>
<div id="shlist">{first}</div>
<nav id="shpager" class="pager" aria-label="Pages"></nav>
<h2>What does self-hosting mean?</h2>
<p>Self-hosting means running an app on a computer you control, such as a small home server, a cheap rented server or a Raspberry Pi, instead of using a company's online service. You keep your own data, you decide when to update, and many of these apps are free. The trade-off is that you look after the setup, the backups and the security yourself.</p>
<h2>Before you install anything</h2>
<p>Check the notes that come with each download, make sure the app is still being updated, and keep your server patched. Looking for ready-to-run apps for your phone or computer instead? Browse the <a href="/downloads/">ZER0 Vault</a>.</p>
<p class="credit">This directory is based on <a href="{e(meta.get("site", "https://awesome-selfhosted.net"))}" rel="noopener">awesome-selfhosted</a> by the awesome-selfhosted contributors, using their open data (<a href="{e(meta.get("source", ""))}" rel="noopener">awesome-selfhosted-data</a>), licensed under <a href="{e(meta.get("license_url", "https://creativecommons.org/licenses/by-sa/3.0/"))}" rel="noopener">{e(meta.get("license", "CC BY-SA 3.0"))}</a>. Changes made: reformatted into one searchable list, direct download links added, sorted by stars. This list is shared under the same license. Data last refreshed {e(meta.get("generated", ""))}.</p>
<script src="/art.min.js?v=1"></script>
<script>{SH_FUNCS}
{SH_WIRE}</script>"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Self-Hosted Apps Directory", "url": f"{SITE}/downloads/selfhosted/",
          "description": f"A searchable directory of {n:,} open-source apps you can run on your own server."}
    write_page("/downloads/selfhosted/", shell("/downloads/selfhosted/", "Self-Hosted Apps Directory: Free Software to Run on Your Own Server | ZER0 Updates",
          f"Search {n:,} free, open-source apps you can self-host and download the latest version. Filter by category, platform and license. Based on awesome-selfhosted (CC BY-SA 3.0).", body, ld))
    return "/downloads/selfhosted/"


def vault_page():
    """Content for /downloads/ (the Vault). build_pages.py opens it inside the app so it keeps the app's look,
    with this plain list underneath for search engines. Returns (title, description, h1, intro, body, items)."""
    mine = "".join(f'<li><a href="{tool_path(t)}">{e(t["name"])}</a>: {e(t["short"])} ({e(t["kind"].split(" (")[0])}, {e(t["os"])})</li>' for t in TOOLS)
    groups = {}
    for x in third_party():
        groups.setdefault(str(x.get("category", "OTHER")).title(), []).append(x)
    other = ""
    for cat in sorted(groups):
        other += f"<h3>{e(cat)}</h3><ul>"
        for x in groups[cat]:
            url = x.get("url", "")
            href = ("/" + url) if url and not url.startswith("http") else url
            other += f'<li><a href="{e(href)}" rel="noopener nofollow">{e(x["title"])}</a>: {e(first_sentence(x.get("description")))}</li>'
        other += "</ul>"
    body = (f"<h2>Our scripts</h2><ul>{mine}</ul>"
            '<p>Looking for server software you run yourself? Browse the <a href="/downloads/selfhosted/">Self-Hosted apps directory</a>.</p>'
            "<p>Before you run anything: the scripts are plain text, so open them in a text editor and read them first. Each tool page lists a SHA-256 checksum so you can confirm the file is the one we published, and says plainly what the tool cannot do.</p>"
            f"<h2>Open-source apps we recommend</h2><p>Made by other developers. We link to each project's own release page.</p>{other}")
    title = "ZER0 Vault: Free PC Scripts and Open-Source App Downloads | ZER0 Updates"
    desc = "The ZER0 Vault: free PC scripts and open-source apps with clear how-to pages. Image compressor, PDF merger, file organizer, cleaner and more, with checksums."
    h1 = "ZER0 Vault: Free PC Scripts and Open-Source App Downloads"
    intro = ("The Vault is our library of free tools: small PC scripts we wrote ourselves, plus open-source apps we think are worth having. "
             "Every script has its own page that explains what it does, how to use it, what it needs and where it falls short, so you know what you are running before you run it.")
    items = [(t["name"], SITE + tool_path(t)) for t in TOOLS]
    return title, desc, h1, intro, body, items

# ---------------------------------------------------------------- trust pages
def trust_pages():
    about = f"""<h1>About ZER0 Updates</h1>
<p class="lead">ZER0 Updates is an independent, free website for football fans and people who like useful free software.</p>
<h2>What you will find here</h2>
<ul><li><b>Football:</b> headlines, league tables, fixtures and results for the Premier League, La Liga, Bundesliga, Serie A, Ligue 1 and the Champions League.</li>
<li><b>Downloads:</b> small scripts written by us and open-source apps, each with plain-language instructions and honest notes about limits.</li>
<li><b>Deals, coupons and trending news:</b> collected from public sources and refreshed automatically.</li></ul>
<h2>How the content is made</h2>
<p>Football tables, fixtures, news, deals and coupons are gathered and updated automatically by software, several times a day. Headlines link to the original publisher, so you can read the full story at the source. We do not copy full articles. The tools on the Downloads pages are written and maintained by us, and the pages explaining them are written by hand.</p>
<h2>How we make money</h2>
<p>The site is free to use. It is supported by advertising from third-party networks and by affiliate links, which may pay us a commission when you buy something, at no extra cost to you. Paid placements are labelled as Sponsored. Ads and affiliate links do not decide what appears in the football tables or which tools we publish.</p>
<h2>Accuracy and corrections</h2>
<p>Automatic data can be late or wrong. League tables and scores come from third-party data providers, and prices and coupon codes can change at any time, so always confirm a price or code on the retailer's own site. If you spot a mistake, <a href="/contact/">please tell us</a> and we will fix it.</p>"""
    contact = f"""<h1>Contact ZER0 Updates</h1>
<p class="lead">The quickest way to reach us is Telegram. Email works too.</p>
<div class="grid"><div class="card"><h3>Telegram</h3><p><a href="{TG_USER}" rel="noopener">@CYBERO0</a></p><p class="m">Fastest reply. Bug reports, tool requests, corrections.</p></div>
<div class="card"><h3>Email</h3><p><a href="mailto:{EMAIL}">{EMAIL}</a></p><p class="m">Business, advertising and takedown requests.</p></div>
<div class="card"><h3>Telegram channel</h3><p><a href="{TG_CHANNEL}" rel="noopener">t.me/zer0updates</a></p><p class="m">Daily updates and new tools.</p></div></div>
<h2>What to include</h2><ul><li>For a bug: the page address, what you expected and what happened, and your device and browser.</li><li>For a download problem: the tool name and the error message.</li><li>For a correction: the page and the part that is wrong.</li></ul>
<p>We read every message, but cannot promise an instant answer."""
    privacy = f"""<h1>Privacy Policy</h1><p class="m">Last updated: {NICE}</p>
<p>This policy explains what happens to information when you use zeroupdates.org. You do not need an account to use the site, and we do not ask for your name or email to browse or download.</p>
<h2>Information collected automatically</h2><p>We use Google Analytics to count visits and see which pages are popular. It collects data such as your approximate location, device type, browser and the pages you view. This is aggregated and we do not use it to identify you.</p>
<h2>Advertising and cookies</h2><p>The site shows ads from third-party advertising networks. These partners may use cookies or similar technologies to show and measure ads, and some ads may open in a new tab or window. We do not control what third-party ads contain. You can limit ad cookies in your browser settings, and you can opt out of personalised advertising through your device or browser privacy controls.</p>
<h2>Affiliate links</h2><p>Some links to shops and services are affiliate links. If you buy through them we may earn a commission at no extra cost to you. The shop may place its own cookies when you click.</p>
<h2>Local storage</h2><p>Your browser stores a few settings on your device, such as your light or dark theme choice. This stays on your device.</p>
<h2>ZER0 Assistant</h2><p>If you use the assistant on the main site, the message you type is sent to our server and to an AI service so that a reply can be created. Please do not type personal or sensitive information into it.</p>
<h2>Downloads</h2><p>Our own scripts run entirely on your computer and, unless a page says otherwise, do not send your data anywhere. Third-party apps linked from our Downloads page are made by other developers and have their own privacy practices.</p>
<h2>Third-party sites</h2><p>We link to news publishers, shops and other sites. We are not responsible for their content or privacy practices.</p>
<h2>Children</h2><p>The site is not aimed at children under 13 and we do not knowingly collect their personal information.</p>
<h2>Changes</h2><p>We may update this page. The date at the top shows when it last changed.</p>
<h2>Contact</h2><p>Questions about this policy? See our <a href="/contact/">contact page</a>.</p>"""
    terms = f"""<h1>Terms of Use</h1><p class="m">Last updated: {NICE}</p>
<p>By using zeroupdates.org you agree to these terms. If you do not agree, please do not use the site.</p>
<h2>Using the site</h2><p>The site is free for personal use. Please do not misuse it, try to break or overload it, or copy large amounts of its content automatically.</p>
<h2>Information, not advice</h2><p>Football data, news summaries, prices and coupon codes are provided for general information. They are collected automatically from third parties and can be late, incomplete or wrong. Always check prices and codes on the retailer's website before buying.</p>
<h2>Downloads</h2><p>Scripts and files from our Downloads pages are provided as is, without any warranty. You use them at your own risk. Read what a tool does before you run it, and back up important files first. Third-party apps belong to their developers and are covered by their own licences. You are responsible for following the law and the terms of any service you use a tool with.</p>
<h2>External links and ads</h2><p>The site contains links, affiliate links and ads from third parties. We do not control and are not responsible for those sites, products or services.</p>
<h2>Content and ownership</h2><p>Headlines and short summaries link to their original publishers, who own their content. The design, text and scripts that we wrote belong to ZER0 Updates. Logos and names of other companies belong to their owners. If you believe something on the site infringes your rights, please <a href="/contact/">contact us</a> and we will look into it promptly.</p>
<h2>Limits of liability</h2><p>To the extent the law allows, ZER0 Updates is not liable for any loss or damage that comes from using the site or its downloads.</p>
<h2>Changes</h2><p>We may change these terms or the site at any time. Continuing to use the site means you accept the updated terms.</p>"""
    pages = [("/about/", "About ZER0 Updates | Who We Are and How the Site Works", "ZER0 Updates is an independent site for football tables, news and free tools. Learn how content is made and how the site is funded.", about, "/about/"),
             ("/contact/", "Contact ZER0 Updates", "Contact ZER0 Updates on Telegram or by email for corrections, bug reports and tool requests.", contact, None),
             ("/privacy/", "Privacy Policy | ZER0 Updates", "How ZER0 Updates handles analytics, advertising cookies, affiliate links and your data.", privacy, None),
             ("/terms/", "Terms of Use | ZER0 Updates", "The terms for using ZER0 Updates and downloading its scripts and tools.", terms, None)]
    for path, title, desc, body, cur in pages:
        write(path, shell(path, title, desc, body, None, cur))
    return [p[0] for p in pages]

def build():
    ALIAS_DIRS.clear()
    os.makedirs("assets", exist_ok=True)
    open("assets/site.css", "w", encoding="utf-8").write(CSS)
    links, paths = {}, []
    norm_ = lambda x: re.sub(r"[^a-z0-9]", "", str(x).lower())
    built = [tool_page(t, TOOLS) for t in TOOLS]
    for t, p in zip(TOOLS, built):
        paths.append(p)
        if p != f"/downloads/{t['slug']}/":
            redirect_stub(f"downloads/{t['slug']}", p, t["name"], t["short"])
        for k in (norm_(t["name"]), norm_(t.get("src", ""))):
            if k: links[k] = p
    json.dump({"tools": [{"slug": t["slug"], "name": t["name"], "short": t["short"], "kind": t["kind"].split(" (")[0], "os": t["os"], "path": tool_path(t)} for t in TOOLS]},
              open("assets/vault.json", "w", encoding="utf-8"), ensure_ascii=False)
    for slug, x in app_entries():
        p = app_page(slug, x, None)
        if p != f"/downloads/{slug}/":
            redirect_stub(f"downloads/{slug}", p, x["title"], first_sentence(clean_desc(x.get("description")), 150))
        k = norm_(x["title"])
        links[k + "|" + str(x.get("category", "")).upper()] = p
        links.setdefault(k, p)
    json.dump(links, open("assets/vault-links.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    sh = selfhosted_page()
    if sh:
        redirect_stub("selfhosted", sh, "Self-Hosted Apps Directory", "The Self-Hosted apps directory now lives inside the ZER0 Vault.")
        ALIAS_DIRS.append("selfhosted")
    open("alias_dirs.txt", "w", encoding="utf-8").write("\n".join(sorted(set(ALIAS_DIRS))) + "\n")
    return ["downloads/"] + ([sh.strip("/") + "/"] if sh else []) + [p.strip("/") + "/" for p in paths] + [p.strip("/") + "/" for p in trust_pages()]


if __name__ == "__main__":
    print("[ok] built", len(build()), "pages")
