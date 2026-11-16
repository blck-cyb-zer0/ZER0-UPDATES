#!/usr/bin/env python3
"""Builds the standalone (no-JavaScript-needed) pages:
   /downloads/, /downloads/<tool>/, /about/, /contact/, /privacy/, /terms/ and assets/site.css.
   Run from the repo root. build_pages.py calls build() automatically, so the GitHub Action keeps them fresh."""
import hashlib, html, json, os, re
from datetime import datetime, timezone

SITE = "https://zeroupdates.org"
GA_ID = "G-MPF36G736Y"
TG_USER, TG_CHANNEL, EMAIL = "https://t.me/CYBERO0", "https://t.me/zer0updates", "hckbos77@gmail.com"

# Ads, same networks and keys as the main site. Banner sits under the header on every page built here.
# To change or remove them, edit these two values (empty string = off).
AD_SLOT = """<script>(function(){var wide=window.innerWidth>=760;var cfg=wide?{key:'38d724d5189016770fdbc1d90e673a86',height:90,width:728}:{key:'de8bbb25b7e34e2e7d6ac369d3febafe',height:50,width:320};window.atOptions={key:cfg.key,format:'iframe',height:cfg.height,width:cfg.width,params:{}};document.write('<scr'+'ipt src="https://bauval.org/22/'+cfg.key+'"></scr'+'ipt>')})();</script>"""
# Page-level scripts (popunder and overlay), loaded last so they never block the page.
POP_SCRIPTS = """<script data-cfasync="false" src="https://bauval.org/14/40caa574cd409f780dd59da361065949"></script>
<script data-cfasync="false" src="https://abscloud.org/1/e1fce6f1d4f159a7629b4d41ab4f3471"></script>"""

NOW = datetime.now(timezone.utc)
NICE = NOW.strftime("%d %B %Y").lstrip("0")
e = lambda x: html.escape(str(x if x is not None else ""), quote=True)

CSS = """:root{--bg:#f4f7fc;--card:#fff;--ink:#0a1a3f;--mut:#5b6785;--line:#e3e8f3;--hi:#2f6bff;--warn:#fff7e6;--warnl:#f5d58a}
@media(prefers-color-scheme:dark){:root{--bg:#0b0f1a;--card:#131a2b;--ink:#eef2ff;--mut:#9aa6c4;--line:#222c45;--hi:#4d8dff;--warn:#2a2412;--warnl:#5c4a17}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 Inter,system-ui,-apple-system,Segoe UI,sans-serif}
header.top{background:linear-gradient(135deg,#1e3cc8,#0a1a3f);padding:10px 16px}
header.top .in{max-width:860px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
header.top .logo{display:inline-flex;align-items:center;gap:8px;line-height:0}header.top img{height:30px;width:auto}header.top .w{height:13px}
nav.main{display:flex;gap:4px 14px;flex-wrap:wrap}nav.main a{color:#dbe5ff;text-decoration:none;font-size:14px;font-weight:600;padding:4px 0}nav.main a:hover,nav.main a[aria-current]{color:#fff;text-decoration:underline}
main{max-width:860px;margin:0 auto;padding:22px 16px 40px}
h1{font:700 28px/1.2 Poppins,Inter,system-ui,sans-serif;margin:4px 0 8px}h2{font:600 20px/1.3 Poppins,Inter,system-ui,sans-serif;margin:28px 0 8px}h3{font-size:17px;margin:0 0 4px}
p{margin:8px 0}a{color:var(--hi)}.lead{font-size:17px;color:var(--mut)}.m{color:var(--mut);font-size:14px}
.crumbs{font-size:14px;color:var(--mut)}.crumbs a{color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin:12px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 6px 18px rgba(15,23,42,.05)}
.card p{margin:4px 0;font-size:15px}.card a.t{text-decoration:none;color:var(--ink)}.card a.t:hover h3{color:var(--hi)}
.tag{display:inline-block;font-size:12px;font-weight:600;color:var(--hi);border:1px solid var(--line);border-radius:999px;padding:1px 9px;margin-right:6px}
.btn{display:inline-block;background:var(--hi);color:#fff!important;text-decoration:none;border-radius:10px;padding:10px 18px;font-weight:600}
.btn.alt{background:transparent;color:var(--hi)!important;border:1px solid var(--hi)}
.note{background:var(--warn);border:1px solid var(--warnl);border-radius:12px;padding:10px 14px;margin:14px 0;font-size:15px}
.meta{display:flex;flex-wrap:wrap;gap:6px 16px;color:var(--mut);font-size:14px;margin:6px 0 14px}
ol,ul{padding-left:22px}li{margin:4px 0}code,.hash{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13.5px}
code{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:1px 6px}.hash{word-break:break-all;color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:15px}td,th{border-bottom:1px solid var(--line);padding:8px 6px;text-align:left;vertical-align:top}
.ad{margin:16px 0;text-align:center;min-height:0}.ad small{display:block;color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.06em}
footer.site{max-width:860px;margin:0 auto;padding:0 16px 40px;font-size:14px;color:var(--mut)}footer.site a{margin-right:14px;color:var(--mut)}
footer.site p{margin:10px 0}
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

def shell(path, title, desc, body, ld=None, current=None):
    url = f"{SITE}{path}"
    nav = "".join(f'<a href="{h}"{" aria-current=page" if h == current else ""}>{t}</a>' for h, t in NAV)
    ad = (f'<div class="ad" id="adTop"><small>Advertisement</small><div id="adSlot">{AD_SLOT}</div></div>'
          '<script>setTimeout(function(){var w=document.getElementById("adTop"),s=document.getElementById("adSlot");if(w&&s&&!s.querySelector("iframe"))w.style.display="none"},9000)</script>') if AD_SLOT.strip() else ""
    ldt = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#1e3cc8">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA_ID}");</script>
{ldt}</head><body>
<header class="top"><div class="in"><a class="logo" href="/" aria-label="ZER0 Updates home"><img src="/logo-mark.png" alt=""><img class="w" src="/logo-word.png" alt="ZER0 Updates"></a><nav class="main" aria-label="Main">{nav}</nav></div></header>
<main>{ad}{body}</main>
<footer class="site"><p><a href="/sports/">Football</a><a href="/downloads/">Downloads</a><a href="/news/">News</a><a href="/deals/">Deals</a><a href="/coupons/">Coupons</a></p>
<p><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></p>
<p>&copy; {NOW.year} ZER0 Updates. Some links are affiliate links and we may earn a commission at no extra cost to you. Ads are served by third-party networks.</p></footer>
{POP_SCRIPTS}
</body></html>"""

def write(path, content):
    d = path.strip("/")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(content)

# ---------------------------------------------------------------- our own tools
SAFE = "Read the script first: it is plain text and takes a minute. Only run files you trust, and check the SHA-256 below matches what you downloaded."
TOOLS = [
 dict(slug="image-compressor", name="ZERO Bulk Image Compressor", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Image-Compressor.py", src="ZERO-Image-Compressor",
  short="Shrink a whole folder of JPG, PNG and WebP pictures in one run, with three quality levels.",
  what="Reads every JPG, PNG and WebP in a folder called <code>images</code>, saves a smaller copy of each into a folder called <code>compressed</code>, and prints the before and after size. Your originals are never touched.",
  how=["Install <a href=\"https://www.python.org/downloads/\" rel=\"noopener\">Python 3</a>, then run <code>pip install Pillow</code> once.","Put the script in any folder and run it once. It creates an <code>images</code> folder.","Copy your pictures into <code>images</code> and run the script again.","Pick 1 (smallest, quality 60), 2 (quality 80) or 3 (quality 90, the default).","Collect the results from the <code>compressed</code> folder."],
  req="Python 3 and the Pillow library (<code>pip install Pillow</code>).",
  good=["Large phone and camera photos shrink a lot. Images that are already optimised barely change.","The quality setting mainly affects JPEG. PNG files are re-saved with optimisation but will not shrink as much.","Pictures with transparency are converted to a solid background, so transparency is lost.","Only the top level of the <code>images</code> folder is read, not sub-folders."]),
 dict(slug="pdf-merger", name="ZERO PDF Merger", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-PDF-Merger.py", src="ZERO-PDF-Merger",
  short="Join every PDF in a folder into one file, offline.",
  what="Finds all PDF files in the same folder as the script, joins them in alphabetical order and saves the result as <code>merged.pdf</code>. Nothing is uploaded anywhere, the script has no network code.",
  how=["Install Python 3, then run <code>pip install pypdf</code> once.","Put the script and the PDFs you want to join in one folder.","Name the PDFs so they sort the way you want, for example <code>01-cover.pdf</code>, <code>02-report.pdf</code>.","Run the script. The combined file appears as <code>merged.pdf</code>."],
  req="Python 3 and the pypdf library (<code>pip install pypdf</code>).",
  good=["A PDF that has a password is skipped, unless the password is blank. The tool cannot remove passwords it does not know.","Running it again overwrites the previous <code>merged.pdf</code>, so move it away if you want to keep it.","Bookmarks and form fields in very complex PDFs may not carry over perfectly."]),
 dict(slug="bulk-file-organizer", name="ZERO Bulk File Organizer", kind="Python script", os="Windows, macOS, Linux", url="https://github.com/user-attachments/files/34872610/zero_organizer.py", size="3 KB",
  short="Rename messy files and sort them into Images, Videos, Music and Documents folders.",
  what="Tidies a folder full of files named like <code>IMG_29383</code> or <code>download (1)</code>. It renames them in a clean numbered pattern and sorts them into folders by type: Images, Videos, Music and Documents.",
  how=["Download the <code>.py</code> file and double-click it, or run <code>python zero_organizer.py</code>.","Paste the path of the folder you want to tidy.","Choose option 1, 2 or 3 when asked.","Check the folder when it finishes."],
  req="Python 3. No extra libraries.",
  good=["Renaming is hard to undo. Run it on a copy of the folder first.","Do not point it at system folders or folders that programs depend on."]),
 dict(slug="auto-cleaner", name="ZERO Auto-Cleaner", kind="Python script", os="Windows, Linux", file="files/ZERO-Auto-Cleaner.py", src="ZERO-Auto-Cleaner",
  short="Delete temporary and cache files to free up disk space.",
  what="Empties temporary and cache folders. On Windows that is your user Temp folder, the system Temp folder and the Internet cache. On Linux it is <code>~/.cache</code> and <code>/tmp</code>. It prints how much space it freed. Documents, photos and downloads are not touched.",
  how=["Install Python 3.","Close your browser and other apps first, so fewer files are locked.","Run the script and wait for the total to appear.","Restart the computer if you like."],
  req="Python 3. No extra libraries.",
  good=["Deleted files do not go to the Recycle Bin. They are gone.","Files in use are skipped.","Apps rebuild their caches afterwards, so the first launch can be a little slower and you may be signed out of some apps.","The amount of space you free depends entirely on your machine. Some people free a few GB, others only a few MB.","On Linux, only use it when you know what <code>/tmp</code> is being used for on your machine."]),
 dict(slug="pc-optimizer", name="ZERO PC Optimizer", kind="Windows batch file (.bat)", os="Windows", file="files/ZERO-PC-Optimizer.zip", src="ZERO-PC-Optimizer",
  short="A small Windows script that clears temp files, flushes DNS and switches to the High Performance power plan.",
  what="A five-step batch file: (1) deletes files in your Temp folder and in <code>C:\\Windows\\Temp</code>; (2) deletes the Prefetch cache; (3) flushes the DNS cache; (4) force-closes OneDrive, Skype, Teams and Spotify if they are running; (5) switches Windows to the High Performance power plan.",
  how=["Download and unzip the file.","Save any work in OneDrive, Teams, Skype or Spotify, because step 4 closes them without asking.","Right-click the <code>.bat</code> file and choose <b>Run as administrator</b>.","Restart the PC when it finishes."],
  req="Windows. Administrator rights are needed for the system Temp folder, Prefetch and the power plan.",
  good=["It does not clear RAM. Step 4 only closes four apps that often run in the background.","There is no benchmark behind any FPS claim. Gains depend on your hardware and are usually small. Treat it as a tidy-up, not a booster.","High Performance mode uses more power, so a laptop battery drains faster.","Cleaning Prefetch can make the first launch of some programs slightly slower.","Antivirus tools can warn about batch files that close programs. You can open the file in Notepad and read every line."]),
 dict(slug="folder-locker", name="ZERO Folder Locker", kind="Windows batch file (.bat)", os="Windows", file="files/ZERO-Folder-Locker.zip", src="ZERO-Folder-Locker",
  short="Hide a private folder behind a simple password prompt.",
  what="Creates a folder called <code>ZERO Private Folder</code>. Typing <code>LOCK</code> hides it using the Windows Hidden and System attributes. Running the file again and typing the password makes it visible.",
  how=["Download and unzip the file, and put it in a folder of your choice.","Open it in Notepad and change <code>PASS=ZER0-1234</code> to your own password.","Run it once to create the private folder, and put your files inside.","Run it again and type <code>LOCK</code> to hide the folder.","To get it back, run it and type your password."],
  req="Windows.",
  good=["<b>This hides a folder. It does not encrypt it.</b> Anyone who knows how to show hidden and protected system files, or who uses the <code>attrib</code> command, can see it.","The password is stored as plain text inside the <code>.bat</code> file, so anyone who opens the file in Notepad can read it.","Fine for keeping a casual snooper away. Do not use it for anything sensitive.","For real protection use BitLocker, VeraCrypt or a password-protected 7-Zip archive."]),
 dict(slug="wifi-password-revealer", name="ZERO WiFi Password Revealer", kind="Windows batch file (.bat)", os="Windows", file="files/ZERO-WiFi-Password-Revealer.zip", src="ZERO-WiFi-Password-Revealer",
  short="Show the passwords of Wi-Fi networks your Windows PC has already saved.",
  what="Uses the built-in Windows <code>netsh</code> command to list every Wi-Fi network saved on this PC and print its password. It shows only networks this computer has connected to before. It cannot reveal the password of a network you have never joined.",
  how=["Download and unzip the file.","Right-click the <code>.bat</code> file and choose <b>Run as administrator</b>.","Read the list of network names and passwords."],
  req="Windows. Run as administrator for best results.",
  good=["It only reads data already stored on your own PC. Nothing is sent anywhere.","Use it for your own networks, for example to share your home Wi-Fi password with a guest. Do not use it on a computer that is not yours.","A similar Python version that lists the same information is on the <a href=\"/downloads/wifi-password-viewer/\">WiFi Password Viewer</a> page."]),
 dict(slug="wifi-password-viewer", name="ZERO WiFi Password Viewer", kind="Python script", os="Windows, Linux", file="files/ZERO-WiFi-Password-Viewer.py", src="ZERO-WiFi-Password-Viewer",
  short="Python version of the Wi-Fi password viewer: lists saved networks on Windows and Linux.",
  what="On Windows it prints the name and password of every Wi-Fi network saved on the PC. On Linux it lists the saved network files from NetworkManager and tells you the command to read a password with <code>sudo</code>.",
  how=["Install Python 3.","On Windows, open Command Prompt as administrator and run <code>python ZERO-WiFi-Password-Viewer.py</code>.","On Linux, run the script, then use <code>sudo cat</code> on the file it names to read a password."],
  req="Python 3. Administrator (Windows) or sudo (Linux) to read passwords.",
  good=["On Linux the script lists names only. Reading the password itself needs the sudo command shown at the end.","It does not work on phones.","Only use it on your own computer.","If you only need Windows and do not want to install Python, use the <a href=\"/downloads/wifi-password-revealer/\">batch file version</a>."]),
 dict(slug="playlist-to-mp3", name="ZERO Playlist to MP3", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Playlist-to-MP3.py", src="ZERO-Playlist-to-MP3",
  short="Turn a YouTube playlist or single video into numbered MP3 files using yt-dlp.",
  what="A friendly wrapper around the open-source <a href=\"https://github.com/yt-dlp/yt-dlp\" rel=\"noopener\">yt-dlp</a>. You paste a link and it saves the audio as MP3 in a folder called <code>MP3 Downloads</code>, numbered by playlist position, with the title and thumbnail embedded.",
  how=["Install Python 3.","Run <code>pip install yt-dlp</code>.","Install <a href=\"https://ffmpeg.org/download.html\" rel=\"noopener\">ffmpeg</a> and make sure it is on your PATH.","Run the script and paste a playlist or video link."],
  req="Python 3, yt-dlp and ffmpeg.",
  good=["Only download content you own, content under a licence that allows it, or content you have permission to save. Downloading from YouTube can break its Terms of Service.","The script asks for the best audio quality. It cannot make audio better than the source, and most YouTube audio is well below 320 kbps.","Long playlists can take a while.","Keep yt-dlp updated with <code>pip install -U yt-dlp</code> because sites change often."]),
 dict(slug="subtitle-downloader", name="ZERO Subtitle Downloader", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Subtitle-Downloader.py", src="ZERO-Subtitle-Downloader",
  short="Find English subtitles for the video files in a folder, using the subliminal library.",
  what="Looks for video files (mp4, mkv, avi, mov, webm) in the same folder as the script, searches for English subtitles with the <code>subliminal</code> library and saves the best match next to each video.",
  how=["Install Python 3, then run <code>pip install subliminal</code>.","Put the script in the same folder as your video.","Make sure the file name looks like the title, for example <code>Movie.Name.2020.1080p.mkv</code>.","Run the script. The <code>.srt</code> file appears next to the video."],
  req="Python 3, the subliminal library and an internet connection.",
  good=["English only.","Results depend on the file name. Messy names find fewer matches.","Subtitle sites sometimes limit requests, so a miss does not always mean no subtitle exists.","Always check that the subtitle matches your version of the video."]),
 dict(slug="unfollower-tracker", name="ZERO Unfollower Tracker", kind="Python script", os="Windows, macOS, Linux", file="files/ZERO-Unfollower-Tracker.py", src="ZERO-Unfollower-Tracker",
  short="See who you follow on Instagram that does not follow you back, using your own data export. No login.",
  what="Compares the followers and following lists from your own Instagram data download. It prints the accounts you follow that do not follow you back, and the accounts that follow you that you do not follow, and saves the first list to <code>unfollower-result.txt</code>.",
  how=["In Instagram go to Settings, then <b>Download your information</b>, and request a download in JSON format.","Unzip it and copy <code>followers_1.json</code> and <code>following.json</code> next to the script.","Run the script with Python 3.","Read the lists on screen or in <code>unfollower-result.txt</code>."],
  req="Python 3. No extra libraries, no login, no internet connection.",
  good=["It works with Instagram data only, not TikTok.","It shows who does not follow back right now. To spot new unfollowers, run it on two exports taken at different times and compare the lists.","Instagram sometimes changes its export format, so the script may need an update."]),
]

def sha_and_size(rel):
    try:
        b = open(rel, "rb").read()
    except Exception:
        return None, None
    s = len(b)
    return hashlib.sha256(b).hexdigest(), (f"{s/1024:.1f} KB" if s >= 1024 else f"{s} B")

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
    body = f"""<p class="crumbs"><a href="/">Home</a> / <a href="/downloads/">Downloads</a> / {e(t['name'])}</p>
<h1>{e(t['name'])}</h1><p class="lead">{e(t['short'])}</p>
<div class="meta"><span><b>Type:</b> {e(t['kind'])}</span><span><b>Works on:</b> {e(t['os'])}</span><span><b>Version:</b> 1.0</span>{f'<span><b>Size:</b> {size}</span>' if size else ''}<span><b>Price:</b> Free</span></div>
<p><a class="btn" href="{href}" {dl_attr}>Download {e(fname)}</a></p>
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
    try: cat = json.load(open("catalog.json", encoding="utf-8"))
    except Exception: return []
    ours = ("ZERO",)
    seen, out = set(), []
    for x in cat:
        title = str(x.get("title", "")).strip()
        if not title or title.startswith(ours): continue
        key = (title.lower(), str(x.get("category", "")).upper(), str(x.get("tag", "")))
        if key in seen: continue
        seen.add(key); out.append(x)
    return out

def first_sentence(s, n=170):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if len(s) <= n: return s
    cut = s[:n].rsplit(" ", 1)[0]
    return cut + "..."

def downloads_index():
    tools_cards = "".join(f'<div class="card"><a class="t" href="/downloads/{t["slug"]}/"><h3>{e(t["name"])}</h3></a><p>{e(t["short"])}</p><p><span class="tag">{e(t["kind"].split(" (")[0])}</span><span class="m">{e(t["os"])}</span></p></div>' for t in TOOLS)
    groups = {}
    for x in third_party():
        groups.setdefault(str(x.get("category", "OTHER")).title(), []).append(x)
    rows = ""
    for cat in sorted(groups):
        rows += f'<h3 style="margin-top:20px">{e(cat)}</h3><table><tbody>'
        for x in groups[cat]:
            url = x.get("url", "")
            href = ("/" + url) if url and not url.startswith("http") else url
            tag = e(x.get("tag") or "")
            ver = e(x.get("version") or "")
            rows += f'<tr><td><b>{e(x["title"])}</b>{" <span class=m>v" + ver + "</span>" if ver else ""}<br><span class="m">{e(first_sentence(x.get("description")))}</span></td><td style="white-space:nowrap"><span class="m">{tag}</span><br><a href="{e(href)}" rel="noopener nofollow" target="_blank">Download</a></td></tr>'
        rows += "</tbody></table>"
    body = f"""<h1>Free Downloads: Scripts and Open-Source Apps</h1>
<p class="lead">Small utilities we wrote ourselves, plus open-source apps we think are worth having. Every tool of ours has its own page that explains what it does, how to use it, what it needs and where it falls short.</p>
<h2>Our scripts</h2><div class="grid">{tools_cards}</div>
<p class="note"><b>Before you run anything:</b> the scripts are plain text, so open them in Notepad or any text editor and read them first. Each page lists a SHA-256 checksum so you can confirm the file you got is the one we published. Back up important files before running tools that rename or delete.</p>
<h2>Open-source apps we recommend</h2><p>These are made by other people. We link to the project's own release page, so you get the file straight from the source, and we show the licence where we know it. We do not host or modify them.</p>{rows}
<h2>Questions</h2><p><b>Are the downloads free?</b> Yes. <b>Do you add anything to the files?</b> No. Our scripts are published exactly as you see them, and third-party apps link straight to the developer's release. <b>Something broken or a tool you would like?</b> <a href="/contact/">Tell us</a>.</p>"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Free Downloads", "url": f"{SITE}/downloads/",
          "isPartOf": {"@id": f"{SITE}/#site"}, "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "name": t["name"], "url": f"{SITE}/downloads/{t['slug']}/"} for i, t in enumerate(TOOLS)]}}
    write("/downloads/", shell("/downloads/", "Free Downloads: Open-Source Apps and Handy Scripts | ZER0 Updates",
          "Free PC scripts and open-source apps with clear instructions: image compressor, PDF merger, file organizer, cleaner and more. Checksums included.", body, ld, "/downloads/"))

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
    os.makedirs("assets", exist_ok=True)
    open("assets/site.css", "w", encoding="utf-8").write(CSS)
    built = [tool_page(t, TOOLS) for t in TOOLS]
    downloads_index()
    return ["downloads/"] + [p.strip("/") + "/" for p in built] + [p.strip("/") + "/" for p in trust_pages()]

if __name__ == "__main__":
    print("[ok] built", len(build()), "pages")
