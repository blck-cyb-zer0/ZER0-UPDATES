#!/usr/bin/env python3
"""Builds the standalone (no-JavaScript-needed) pages:
   /downloads/, /downloads/<tool>/, /about/, /contact/, /privacy/, /terms/ and assets/site.css.
   Run from the repo root. build_pages.py calls build() automatically, so the GitHub Action keeps them fresh."""
import hashlib, html, json, os, re
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
.ad{margin:16px 0;text-align:center;min-height:0}.ad small{display:block;color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.06em}
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
@media(max-width:560px){.opt{display:none}}"""

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
DRAWER = BOTTOM + [("/downloads/", "Vault", "downloads")]
DRAWER2 = [("/about/", "About", "help"), ("/contact/", "Contact", "mail"), ("/privacy/", "Privacy Policy", "privacy"), ("/terms/", "Terms of Use", "help")]
THEME_JS = """<script>(function(){var h=document.documentElement,b=document.getElementById('themeBtn'),m=document.getElementById('menuBtn'),d=document.getElementById('drawer'),s=document.getElementById('scrim'),mo=document.getElementById('moreBtn');
var SUN='<svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',MOON='<svg class="i" viewBox="0 0 24 24"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z"/></svg>';
function paint(){b.innerHTML=h.getAttribute('data-theme')==='dark'?SUN:MOON}paint();
b.onclick=function(){var t=h.getAttribute('data-theme')==='dark'?'light':'dark';if(t==='dark')h.setAttribute('data-theme','dark');else h.removeAttribute('data-theme');try{localStorage.setItem('theme',t)}catch(e){}paint()};
function open(o){d.classList.toggle('open',o);s.classList.toggle('open',o)}m.onclick=function(){open(true)};if(mo)mo.onclick=function(){open(true)};s.onclick=function(){open(false)};document.getElementById('closeBtn').onclick=function(){open(false)}})();</script>"""

def shell(path, title, desc, body, ld=None, current=None, robots="index,follow,max-image-preview:large"):
    url = f"{SITE}{path}"
    active = next((h for h, _, _ in BOTTOM if h != "/" and (current or path).startswith(h)), None)
    tabs = "".join(f'<a href="{h}"{" aria-current=page" if h == active or (h == "/downloads/" and (current or path).startswith("/downloads/")) else ""}>{t}</a>' for h, t, _ in DRAWER)
    bn = "".join(f'<a href="{h}"{" class=active" if h == active else ""}>{ic(i)}<span>{t}</span></a>' for h, t, i in BOTTOM)
    bn += f'<button type="button" id="moreBtn"{" class=active" if not active else ""} aria-label="More">{ic("more")}<span>More</span></button>'
    dr = "".join(f'<a href="{h}"{" class=active" if h == (current or path) else ""}>{ic(i)}{t}</a>' for h, t, i in DRAWER) + "<h4>More</h4>" + "".join(f'<a href="{h}">{ic(i)}{t}</a>' for h, t, i in DRAWER2)
    ad = (f'<div class="ad" id="adTop"><small>Advertisement</small><div id="adSlot">{AD_SLOT}</div></div>'
          '<script>setTimeout(function(){var w=document.getElementById("adTop"),s=document.getElementById("adSlot");if(w&&s&&!s.querySelector("iframe"))w.style.display="none"},9000)</script>') if AD_SLOT.strip() else ""
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
<link rel="stylesheet" href="/assets/site.css?v=5">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA_ID}");</script>
{ldt}</head><body>
<header class="topbar"><div class="bar"><a class="brandlogo" href="/" aria-label="ZER0 Updates home"><img class="lm" src="/logo-mark.png" alt="ZER0 Updates logo" width="46" height="30"><img class="lw" src="/logo-word.png" alt="ZER0 Updates" width="154" height="13"></a>
<nav class="tabs" aria-label="Sections">{tabs}</nav>
<div class="actions-r"><button class="icon-btn" id="themeBtn" type="button" aria-label="Toggle light and dark theme"></button><button class="icon-btn" id="menuBtn" type="button" aria-label="Open menu" aria-controls="drawer">{ic("menu")}</button></div></div></header>
<main>{ad}{body}</main>
<footer class="site"><p><a href="/downloads/">ZER0 Vault</a><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></p>
<p>&copy; {NOW.year} ZER0 Updates. Some links are affiliate links and we may earn a commission at no extra cost to you. Ads are served by third-party networks.</p></footer>
<nav class="bottom-nav" aria-label="Main">{bn}</nav>
<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer" aria-label="Menu"><div class="dh"><strong>Menu</strong><button class="icon-btn" id="closeBtn" type="button" aria-label="Close menu">{ic("close")}</button></div>{dr}</aside>
{THEME_JS}
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
  good=["It only reads data already stored on your own PC. Nothing is sent anywhere.","Use it for your own networks, for example to share your home Wi-Fi password with a guest. Do not use it on a computer that is not yours.","A similar Python version that lists the same information is on the <a href=\"/downloads/wifi-password-viewer/\">WiFi Password Viewer</a> page."]),
 dict(slug="wifi-password-viewer", alias="wifiviewer", name="ZERO WiFi Password Viewer", kind="Python script", os="Windows, Linux", file="files/ZERO-WiFi-Password-Viewer.py", src="ZERO-WiFi-Password-Viewer",
  short="Python version of the Wi-Fi password viewer: lists saved networks on Windows and Linux.",
  what="On Windows it prints the name and password of every Wi-Fi network saved on the PC. On Linux it lists the saved network files from NetworkManager and tells you the command to read a password with <code>sudo</code>.",
  how=["Install Python 3.","On Windows, open Command Prompt as administrator and run <code>python ZERO-WiFi-Password-Viewer.py</code>.","On Linux, run the script, then use <code>sudo cat</code> on the file it names to read a password."],
  req="Python 3. Administrator (Windows) or sudo (Linux) to read passwords.",
  good=["On Linux the script lists names only. Reading the password itself needs the sudo command shown at the end.","It does not work on phones.","Only use it on your own computer.","If you only need Windows and do not want to install Python, use the <a href=\"/downloads/wifi-password-revealer/\">batch file version</a>."]),
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
    path = f"/downloads/{t['slug']}/"
    href = "/" + t["file"] if t.get("file") else t["url"]
    dl_attr = f'download rel="noopener"' if t.get("file") else 'rel="noopener nofollow" target="_blank"'
    sha, size = sha_and_size(t["file"]) if t.get("file") else (None, t.get("size"))
    fname = os.path.basename(t["file"]) if t.get("file") else t["url"].rsplit("/", 1)[-1]
    how = "".join(f"<li>{x}</li>" for x in t["how"])
    good = "".join(f"<li>{x}</li>" for x in t["good"])
    rel = "".join(f'<li><a href="/downloads/{o["slug"]}/">{e(o["name"])}</a> <span class="m">&ndash; {e(o["short"])}</span></li>' for o in others if o["slug"] != t["slug"])
    hashblock = f'<p class="m">SHA-256 of <code>{e(fname)}</code>:</p><p class="hash">{sha}</p><p class="m">On Windows: <code>certutil -hashfile {e(fname)} SHA256</code>. On macOS or Linux: <code>shasum -a 256 {e(fname)}</code>.</p>' if sha else '<p class="m">This file is hosted on GitHub. We could not publish a checksum for it here, so open it in a text editor and read it before running.</p>'
    body = f"""<p class="crumbs"><a href="/">Home</a> / <a href="/downloads/">ZER0 Vault</a> / {e(t['name'])}</p>
<h1>{e(H1S.get(t['slug'], t['name']))}</h1><p class="lead">{e(t['short'])}</p>
<div class="meta"><span><b>Type:</b> {e(t['kind'])}</span><span><b>Works on:</b> {e(t['os'])}</span><span><b>Version:</b> 1.0</span>{f'<span><b>Size:</b> {size}</span>' if size else ''}<span><b>Price:</b> Free</span></div>
<p><a class="btn" href="{href}" {dl_attr}>Download {e(fname)}</a></p>
<p class="m">Short link to share: <b>zeroupdates.org/{e(t.get("alias", t["slug"]))}</b></p>
<h2>What it does</h2><p>{t['what']}</p>
<h2>How to use it</h2><ol>{how}</ol>
<h2>Requirements</h2><p>{t['req']}</p>
<h2>Good to know</h2><ul>{good}</ul>
<h2>Is it safe?</h2><p>{SAFE}</p>{hashblock}
<p class="note">Made by ZER0 Updates and provided as is, with no warranty. You are responsible for how you use it. Back up anything important before running a tool that changes or deletes files.</p>
<h2>More tools</h2><ul>{rel}</ul>"""
    ld = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": t["name"], "description": t["short"],
          "applicationCategory": "UtilitiesApplication", "operatingSystem": t["os"], "softwareVersion": "1.0", "url": f"{SITE}{path}",
          "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "publisher": {"@type": "Organization", "name": "ZER0 Updates", "url": SITE}}
    write(path, shell(path, f"{t['name']} - Free Download | ZER0 Updates", t["short"], body, ld, "/downloads/"))
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
            "assets", "football", "index", "scripts", "images", "fonts", "static", "api"}
ALIAS_MARK = "<!-- zer0-alias -->"
ALIAS_DIRS = []


def kebab(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "app"


def alias_stub(alias, target, title, desc):
    """/organizer -> /downloads/bulk-file-organizer/ : a tiny page that sends people (and link previews) to the real page."""
    alias = kebab(alias)
    if alias in RESERVED: return False
    path = os.path.join(alias, "index.html")
    if os.path.exists(path) and ALIAS_MARK not in open(path, encoding="utf-8", errors="ignore").read(): return False
    full = SITE + target
    page = f"""<!DOCTYPE html>{ALIAS_MARK}
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | ZER0 Vault</title><meta name="description" content="{e(desc)}"><meta name="robots" content="noindex,follow">
<link rel="canonical" href="{full}"><meta http-equiv="refresh" content="0;url={target}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{full}"><meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image"><script>location.replace("{target}")</script></head>
<body><p><a href="{target}">Continue to {e(title)}</a></p></body></html>"""
    os.makedirs(alias, exist_ok=True)
    open(path, "w", encoding="utf-8").write(page)
    ALIAS_DIRS.append(alias)
    return True


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
    related = "".join(f'<li><a href="/downloads/{kebab(o["slug"])}/">{e(o["name"])}</a> <span class="m">&ndash; {e(o["short"])}</span></li>' for o in TOOLS[:6])
    body = f"""<p class="crumbs"><a href="/">Home</a> / <a href="/downloads/">ZER0 Vault</a> / {e(title)}</p>
<h1>{e(title)}: {e(short)}</h1>
<div class="meta">{meta}</div>
<p><a class="btn" href="{e(href)}" rel="noopener nofollow" target="_blank">Download {e(title)}</a></p>
<p class="m">Short link to share: <b>zeroupdates.org/{e(slug)}</b></p>
<h2>What it is</h2><p>{e(desc)}</p>
<h2>How to install</h2><ol>{how}</ol>
<h2>Before you download</h2><p>{who} Check that the version and publisher look right, keep the app updated, and only install software from sources you trust.</p>
<p class="note">Listings are refreshed automatically, so version numbers and links can change. If something looks wrong, <a href="/contact/">tell us</a>.</p>
<h2>More from the Vault</h2><ul>{related}</ul>"""
    path = f"/downloads/{slug}/"
    write(path, shell(path, f"{title} Download | ZER0 Vault", short or desc[:150], body, None, "/downloads/", robots="noindex,follow"))
    return slug if alias_stub(slug, path, title, short or desc[:150]) else None


def vault_page():
    """Content for /downloads/ (the Vault). build_pages.py opens it inside the app so it keeps the app's look,
    with this plain list underneath for search engines. Returns (title, description, h1, intro, body, items)."""
    mine = "".join(f'<li><a href="/downloads/{t["slug"]}/">{e(t["name"])}</a>: {e(t["short"])} ({e(t["kind"].split(" (")[0])}, {e(t["os"])})</li>' for t in TOOLS)
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
            "<p>Before you run anything: the scripts are plain text, so open them in a text editor and read them first. Each tool page lists a SHA-256 checksum so you can confirm the file is the one we published, and says plainly what the tool cannot do.</p>"
            f"<h2>Open-source apps we recommend</h2><p>Made by other developers. We link to each project's own release page.</p>{other}")
    title = "ZER0 Vault: Free PC Scripts and Open-Source App Downloads | ZER0 Updates"
    desc = "The ZER0 Vault: free PC scripts and open-source apps with clear how-to pages. Image compressor, PDF merger, file organizer, cleaner and more, with checksums."
    h1 = "ZER0 Vault: Free PC Scripts and Open-Source App Downloads"
    intro = ("The Vault is our library of free tools: small PC scripts we wrote ourselves, plus open-source apps we think are worth having. "
             "Every script has its own page that explains what it does, how to use it, what it needs and where it falls short, so you know what you are running before you run it.")
    items = [(t["name"], f"{SITE}/downloads/{t['slug']}/") for t in TOOLS]
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
    built = [tool_page(t, TOOLS) for t in TOOLS]
    links = {}
    norm_ = lambda x: re.sub(r"[^a-z0-9]", "", str(x).lower())
    for t in TOOLS:
        al = t.get("alias", t["slug"])
        if alias_stub(al, f"/downloads/{t['slug']}/", t["name"], t["short"]):
            for k in (norm_(t["name"]), norm_(t.get("src", ""))):
                if k: links[k] = kebab(al)
    json.dump({"tools": [{"slug": t["slug"], "name": t["name"], "short": t["short"], "kind": t["kind"].split(" (")[0], "os": t["os"]} for t in TOOLS]},
              open("assets/vault.json", "w", encoding="utf-8"), ensure_ascii=False)
    apps = app_entries()
    for slug, x in apps:
        al = app_page(slug, x, apps)
        if al:
            k = norm_(x["title"])
            links[k + "|" + str(x.get("category", "")).upper()] = al
            links.setdefault(k, al)
    json.dump(links, open("assets/vault-links.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    open("alias_dirs.txt", "w", encoding="utf-8").write("\n".join(sorted(set(ALIAS_DIRS))) + "\n")
    return ["downloads/"] + [p.strip("/") + "/" for p in built] + [p.strip("/") + "/" for p in trust_pages()]


if __name__ == "__main__":
    print("[ok] built", len(build()), "pages")
