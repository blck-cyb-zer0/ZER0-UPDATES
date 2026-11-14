#!/usr/bin/env python3
"""
Builds the Downloads catalog automatically.

Reads apps.txt (one app per line) and, for each one, looks up the app's latest OFFICIAL release
(GitHub Releases, F-Droid or IzzyOnDroid), then writes the name, description, size, version,
icon and a direct download link into catalog.json. Nothing is downloaded or re-hosted: the
visitor's download starts straight from the official source.

Entries you add by hand to catalog.json are kept. Generated ones are marked  "auto": true.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

import requests

CATALOG = os.environ.get('CATALOG_PATH', 'catalog.json')
APPS = os.environ.get('APPS_PATH', 'apps.txt')
GH_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'User-Agent': 'zer0-updates-catalog/1.0'}
FDROID_REPOS = {
    'fdroid': 'https://f-droid.org/repo',
    'izzy': 'https://apt.izzysoft.de/fdroid/repo',
}
MAX_DESC = 1800
_index_cache = {}


# ---------------------------------------------------------------- helpers
def human_size(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return ''
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return ('%d %s' % (round(n), unit)) if unit == 'B' else ('%.1f %s' % (n, unit)).replace('.0 ', ' ')
        n /= 1024
    return ''


def cut(text, limit):
    """Shorten at a sentence or word boundary."""
    text = text.strip()
    if len(text) <= limit:
        return text
    chunk = text[:limit]
    end = max(chunk.rfind('. '), chunk.rfind('! '), chunk.rfind('? '))
    if end > limit * 0.5:
        return chunk[:end + 1].strip()
    return chunk.rsplit(' ', 1)[0].strip() + '\u2026'


def strip_markup(text):
    """Markdown / HTML -> plain text lines worth keeping."""
    text = re.sub(r'<!--.*?-->', '', text or '', flags=re.S)
    text = re.sub(r'\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)', '', text)      # [![badge](img)](link)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)                    # ![image](url)
    text = re.sub(r'(?i)<br\s*/?>|</?(p|li|div|h[1-6]|ul|ol)(\s[^>]*)?>', '\n', text)   # block tags -> line breaks
    text = re.sub(r'<[^>]+>', '', text)                                 # any other html tag
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)                # [text](url) -> text
    text = re.sub(r'`{1,3}', '', text)
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r':[a-z0-9_+-]+:', '', text)                          # :emoji: shortcodes
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text


def readme_intro(md, limit=600):
    out = []
    total = 0
    for line in strip_markup(md).splitlines():
        s = re.sub(r'\s+', ' ', line).strip()
        if not s or s[0] in '#|>-=*' or s.startswith('http'):
            continue
        if len(s) < 40:
            continue
        out.append(s)
        total += len(s)
        if total >= limit:
            break
    return cut(' '.join(out), limit)


def release_notes(body, limit=500):
    bullets = []
    for line in strip_markup(body).splitlines():
        s = line.strip()
        if s[:1] in '-*\u2022' and len(s) > 3:
            s = re.sub(r'\s+', ' ', s.lstrip('-*\u2022 ')).strip()
            if s and 'full changelog' not in s.lower():
                bullets.append('\u2022 ' + cut(s, 140))
        if len(bullets) >= 5:
            break
    if bullets:
        return '\n'.join(bullets)
    plain = [re.sub(r'\s+', ' ', l).strip() for l in strip_markup(body).splitlines()]
    plain = [l for l in plain if l and not l.startswith('#') and 'full changelog' not in l.lower()]
    return cut(' '.join(plain), limit) if plain else ''


def parse_apps(path):
    entries = []
    if not os.path.exists(path):
        print('[error] %s not found' % path, file=sys.stderr)
        return entries
    for raw in open(path, encoding='utf-8'):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if ':' not in parts[0]:
            print('[warn] skipped (use source:name): %s' % line, file=sys.stderr)
            continue
        source, ident = parts[0].split(':', 1)
        source = source.lower()
        if source not in ('github',) and source not in FDROID_REPOS:
            print('[warn] unknown source "%s" in: %s' % (source, line), file=sys.stderr)
            continue
        opts = {}
        for p in parts[1:]:
            if '=' in p:
                k, v = p.split('=', 1)
                opts[k.lower()] = v
        entries.append({'source': source, 'id': ident, 'opts': opts, 'key': '%s:%s' % (source, ident)})
    return entries


# ---------------------------------------------------------------- GitHub
def gh_get(path, accept='application/vnd.github+json', allow_404=False):
    headers = dict(HEADERS, Accept=accept)
    if GH_TOKEN:
        headers['Authorization'] = 'Bearer ' + GH_TOKEN
    r = requests.get('https://api.github.com' + path, headers=headers, timeout=60)
    if r.status_code == 404 and allow_404:
        return None
    r.raise_for_status()
    return r.text if accept.endswith('raw') else r.json()


def pick_apk(assets, match=None):
    apks = [a for a in assets if a.get('name', '').lower().endswith('.apk')]
    if match:
        apks = [a for a in apks if re.search(match, a['name'], re.I)]
    if not apks:
        return None

    def score(a):
        n = a['name'].lower()
        s = 0
        if 'universal' in n:
            s += 100
        if 'arm64' in n or 'aarch64' in n:
            s += 60
        if 'release' in n:
            s += 10
        if 'debug' in n:
            s -= 80
        if 'x86' in n:
            s -= 50
        if 'armeabi' in n or 'v7a' in n:
            s -= 20
        return (s, a.get('size', 0))
    return max(apks, key=score)


def build_github(repo, opts):
    info = gh_get('/repos/' + repo)
    match = opts.get('match')
    release = gh_get('/repos/%s/releases/latest' % repo, allow_404=True)
    apk = pick_apk(release.get('assets', []), match) if release else None
    if not apk:
        for r in gh_get('/repos/%s/releases?per_page=15' % repo) or []:
            if r.get('draft'):
                continue
            apk = pick_apk(r.get('assets', []), match)
            if apk:
                release = r
                break
    if not apk:
        raise ValueError('no .apk file found in the latest releases')

    version = (release.get('tag_name') or release.get('name') or '').lstrip('vV')
    try:
        readme = gh_get('/repos/%s/readme' % repo, accept='application/vnd.github.raw', allow_404=True) or ''
    except requests.RequestException:
        readme = ''

    short = re.sub(r':[a-z0-9_+-]+:', '', info.get('description') or '').strip()
    parts = [short] if short else []
    intro = readme_intro(readme)
    if intro and intro[:60].lower() not in short.lower():
        parts.append(intro)
    notes = release_notes(release.get('body') or '')
    if notes:
        parts.append("What's new in %s:\n%s" % (version or 'this release', notes))

    lic = (info.get('license') or {}).get('spdx_id') or ''
    if lic in ('NOASSERTION', 'Other'):
        lic = ''
    topics = ' '.join(info.get('topics') or []).lower()
    if re.search(r'video|music|player|media|youtube|stream', topics):
        category = 'MEDIA'
    else:
        category = 'TOOLS'
    return {
        'title': opts.get('title', '').replace('_', ' ') or info.get('name') or repo.split('/')[-1],
        'category': (opts.get('category') or category).upper(),
        'tag': 'APK \u2022 ' + (lic or 'OFFICIAL'),
        'description': cut('\n\n'.join(parts) or 'Open-source Android app.', MAX_DESC),
        'url': apk['browser_download_url'],
        'size': human_size(apk.get('size')),
        'version': version,
        'image': (info.get('owner') or {}).get('avatar_url', ''),
        'license': lic,
        'updated': (release.get('published_at') or '')[:10],
        'homepage': info.get('homepage') or info.get('html_url') or '',
    }


# ---------------------------------------------------------------- F-Droid style repos
def fdroid_index(base):
    if base not in _index_cache:
        r = requests.get(base + '/index-v2.json', headers=HEADERS, timeout=240)
        r.raise_for_status()
        _index_cache[base] = r.json()
    return _index_cache[base]


def loc(value):
    """Pick an English text from a {locale: text} dict (or return a plain string)."""
    if isinstance(value, dict) and value:
        for k in ('en-US', 'en', 'en-GB'):
            if k in value:
                return value[k]
        return next(iter(value.values()))
    return value if isinstance(value, (str, dict)) else ''


def build_fdroid(kind, package, opts):
    base = FDROID_REPOS[kind]
    entry = (fdroid_index(base).get('packages') or {}).get(package)
    if not entry:
        raise ValueError('package not found in the %s repository index' % kind)
    meta = entry.get('metadata') or {}
    versions = list((entry.get('versions') or {}).values())
    if not versions:
        raise ValueError('no versions listed')

    def code(v):
        try:
            return int((v.get('manifest') or {}).get('versionCode') or 0)
        except (TypeError, ValueError):
            return 0
    best = max(versions, key=lambda v: (code(v), v.get('added') or 0))
    fileinfo = best.get('file') or {}
    if not fileinfo.get('name'):
        raise ValueError('version has no file name (index format changed?). Keys seen: %s' % sorted(best.keys()))

    name = loc(meta.get('name')) or package
    summary = loc(meta.get('summary')) or ''
    desc = strip_markup(loc(meta.get('description')) or '')
    desc = re.sub(r'\n{3,}', '\n\n', desc).strip()
    parts = [p for p in (summary, desc) if p]
    icon = loc(meta.get('icon'))
    icon_name = icon.get('name') if isinstance(icon, dict) else icon
    cats = meta.get('categories') or []
    added = best.get('added')
    updated = ''
    if isinstance(added, (int, float)) and added > 0:
        updated = datetime.fromtimestamp(added / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
    lic = meta.get('license') or ''
    return {
        'title': opts.get('title', '').replace('_', ' ') or name,
        'category': (opts.get('category') or (cats[0] if cats else 'TOOLS')).upper(),
        'tag': 'APK \u2022 ' + (lic or 'F-DROID'),
        'description': cut('\n\n'.join(parts) or 'Open-source Android app.', MAX_DESC),
        'url': base + '/' + fileinfo['name'].lstrip('/'),
        'size': human_size(fileinfo.get('size')),
        'version': str((best.get('manifest') or {}).get('versionName') or ''),
        'image': (base + '/' + icon_name.lstrip('/')) if icon_name else '',
        'license': lic,
        'updated': updated,
        'homepage': meta.get('webSite') or meta.get('sourceCode') or '',
    }


def build(entry):
    if entry['source'] == 'github':
        return build_github(entry['id'], entry['opts'])
    return build_fdroid(entry['source'], entry['id'], entry['opts'])


# ---------------------------------------------------------------- main
def main():
    old = []
    if os.path.exists(CATALOG):
        with open(CATALOG, encoding='utf-8') as f:
            old = json.load(f)
    manual = [x for x in old if not x.get('auto')]
    previous = {x.get('source'): x for x in old if x.get('auto')}
    entries = parse_apps(APPS)

    auto = []
    for e in entries:
        try:
            item = build(e)
            item['auto'] = True
            item['source'] = e['key']
            auto.append(item)
            print('[ok]   %-40s %s  %s' % (e['key'], item.get('version', ''), item.get('size', '')))
        except Exception as ex:
            print('[warn] %s failed: %s' % (e['key'], ex), file=sys.stderr)
            if e['key'] in previous:
                auto.append(previous[e['key']])
                print('       kept the previous entry for it')

    with open(CATALOG, 'w', encoding='utf-8') as f:
        json.dump(manual + auto, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('[done] %d manual + %d automatic items written to %s' % (len(manual), len(auto), CATALOG))
    if entries and not auto:
        sys.exit(1)


if __name__ == '__main__':
    main()
