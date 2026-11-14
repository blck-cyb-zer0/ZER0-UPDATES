#!/usr/bin/env python3
"""
Builds the Downloads catalog automatically from apps.txt.

Supported lines (one per line):
  github:owner/repo              latest official GitHub release (APK, Windows, Linux, Mac, zip ... anything)
  fdroid:package.id              F-Droid repository (Android, open source)
  izzy:package.id                IzzyOnDroid repository (Android, open source)
  pypi:package-name              latest Python package from PyPI
  script:owner/repo/path/file.sh a single file from a repo, copied into files/scripts/ on this site
  direct:https://host/file.iso   any direct file link (size is looked up for you)

Extras after the name (quote values with spaces):
  os=windows|linux|mac|android   pick the file for that system
  ext=appimage  match=regex      pick a specific file
  title="..." desc="..." category=LINUX version=... license=... homepage=... image=... size=...

Entries you add by hand to catalog.json are kept. Generated ones are marked "auto": true.
"""

import base64
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from urllib.parse import quote, unquote, urlparse

import requests

CATALOG = os.environ.get('CATALOG_PATH', 'catalog.json')
APPS = os.environ.get('APPS_PATH', 'apps.txt')
FILES_DIR = os.environ.get('FILES_DIR', 'files/scripts')
GH_TOKEN = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'User-Agent': 'zer0-updates-catalog/1.1'}
FDROID_REPOS = {'fdroid': 'https://f-droid.org/repo', 'izzy': 'https://apt.izzysoft.de/fdroid/repo'}
SOURCES = ('github', 'pypi', 'script', 'direct') + tuple(FDROID_REPOS)
MAX_DESC = 1800
MAX_MIRROR = 10 * 1024 * 1024        # script files copied into the repo must be smaller than this
_index_cache = {}


# ---------------------------------------------------------------- file types
EXT_KINDS = [
    (('.apk', '.apks', '.xapk'), 'APK', 'ANDROID'),
    (('.exe', '.msi', '.msix', '.msixbundle'), 'WINDOWS', 'WINDOWS'),
    (('.appimage', '.deb', '.rpm', '.snap', '.flatpak'), 'LINUX', 'LINUX'),
    (('.dmg', '.pkg'), 'MAC', 'MAC'),
    (('.iso',), 'ISO', 'LINUX'),
    (('.whl',), 'PYTHON', 'PYTHON'),
    (('.py',), 'SCRIPT', 'PYTHON'),
    (('.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd', '.js', '.pl', '.rb', '.lua'), 'SCRIPT', 'SCRIPTS'),
]
ARCHIVES = ('.zip', '.7z', '.rar', '.tar.gz', '.tgz', '.tar.xz', '.tar.bz2', '.tar.zst', '.gz', '.xz')
JUNK_EXT = ('.sha256', '.sha512', '.sha1', '.md5', '.asc', '.sig', '.minisig', '.pem', '.pub', '.sbom', '.sum',
            '.json', '.yml', '.yaml', '.txt', '.blockmap', '.spdx', '.jsonl', '.cdx', '.torrent')
OS_ALIASES = {'android': 'ANDROID', 'apk': 'ANDROID', 'windows': 'WINDOWS', 'win': 'WINDOWS', 'linux': 'LINUX',
              'mac': 'MAC', 'macos': 'MAC', 'osx': 'MAC', 'script': 'SCRIPTS', 'scripts': 'SCRIPTS', 'python': 'PYTHON'}
PLATFORM_RANK = {'ANDROID': 0, 'WINDOWS': 1, 'LINUX': 2, 'MAC': 3, 'PYTHON': 4, 'SCRIPTS': 5, 'OTHER': 6}
EXT_BONUS = {'.exe': 3, '.msi': 2, '.appimage': 4, '.deb': 3, '.rpm': 2, '.dmg': 2, '.apk': 1}


def classify(filename):
    """-> (label shown on the card, platform used as the filter category)"""
    n = (filename or '').lower()
    for exts, label, platform in EXT_KINDS:
        if n.endswith(exts):
            return label, platform
    if n.endswith(ARCHIVES):
        label = 'ZIP' if n.endswith('.zip') else 'ARCHIVE'
        if re.search(r'android', n):
            return label, 'ANDROID'
        if re.search(r'win(dows|32|64)?[-_.]|[-_.]win(dows|32|64)?', n):
            return label, 'WINDOWS'
        if re.search(r'linux|ubuntu|debian|appimage', n):
            return label, 'LINUX'
        if re.search(r'mac|darwin|osx|apple', n):
            return label, 'MAC'
        return label, 'OTHER'
    return 'FILE', 'OTHER'


def is_junk(name):
    n = (name or '').lower()
    return n.endswith(JUNK_EXT) or 'checksum' in n or 'sha256sum' in n or 'sha512sum' in n


def arch_score(name, platform):
    n = name.lower()
    s = 0
    if 'universal' in n:
        s += 100
    if platform == 'ANDROID':
        if 'arm64' in n or 'aarch64' in n:
            s += 60
        if 'x86' in n:
            s -= 50
        if 'armeabi' in n or 'v7a' in n:
            s -= 20
    else:
        if re.search(r'arm|aarch', n):
            s -= 40
        if re.search(r'i386|i686|ia32|win32|x86(?![_-]?64)', n):
            s -= 50
    if 'release' in n:
        s += 10
    if 'debug' in n:
        s -= 80
    return s


def pick_asset(assets, opts):
    """Choose the best downloadable file in a release. Returns (asset, label, platform) or None."""
    cands = []
    for a in assets or []:
        name = a.get('name', '')
        if is_junk(name):
            continue
        label, platform = classify(name)
        cands.append((a, label, platform))
    if opts.get('match'):
        cands = [c for c in cands if re.search(opts['match'], c[0]['name'], re.I)]
    if opts.get('ext'):
        e = '.' + opts['ext'].lstrip('.').lower()
        cands = [c for c in cands if c[0]['name'].lower().endswith(e)]
    if opts.get('os'):
        want = OS_ALIASES.get(opts['os'].lower(), opts['os'].upper())
        cands = [c for c in cands if c[2] == want]
    if not cands:
        return None

    def score(c):
        a, _label, platform = c
        n = a['name'].lower()
        bonus = max([v for k, v in EXT_BONUS.items() if n.endswith(k)] or [0])
        return (-PLATFORM_RANK.get(platform, 6), arch_score(n, platform) + 3 * bonus, a.get('size', 0))
    return max(cands, key=score)


# ---------------------------------------------------------------- text helpers
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
    text = text.strip()
    if len(text) <= limit:
        return text
    chunk = text[:limit]
    end = max(chunk.rfind('. '), chunk.rfind('! '), chunk.rfind('? '))
    if end > limit * 0.5:
        return chunk[:end + 1].strip()
    return chunk.rsplit(' ', 1)[0].strip() + '\u2026'


def strip_markup(text):
    text = re.sub(r'<!--.*?-->', '', text or '', flags=re.S)
    text = re.sub(r'\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)', '', text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'(?i)<br\s*/?>|</?(p|li|div|h[1-6]|ul|ol)(\s[^>]*)?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'`{1,3}', '', text)
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r':[a-z0-9_+-]+:', '', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text


def readme_intro(md, limit=600):
    out, total = [], 0
    for line in strip_markup(md).splitlines():
        s = re.sub(r'\s+', ' ', line).strip()
        if not s or s[0] in '#|>-=*~.' or s.startswith('http') or len(s) < 40:
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
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        try:
            parts = shlex.split(line)
        except ValueError as e:
            print('[warn] could not read line (%s): %s' % (e, line), file=sys.stderr)
            continue
        if not parts or ':' not in parts[0]:
            print('[warn] skipped (use source:name): %s' % line, file=sys.stderr)
            continue
        source, ident = parts[0].split(':', 1)
        source = source.lower()
        if source not in SOURCES:
            print('[warn] unknown source "%s" in: %s' % (source, line), file=sys.stderr)
            continue
        opts = {}
        for p in parts[1:]:
            if '=' in p:
                k, v = p.split('=', 1)
                opts[k.lower()] = v
        entries.append({'source': source, 'id': ident, 'opts': opts, 'key': '%s:%s' % (source, ident)})
    return entries


# ---------------------------------------------------------------- GitHub releases
def gh_get(path, accept='application/vnd.github+json', allow_404=False):
    headers = dict(HEADERS, Accept=accept)
    if GH_TOKEN:
        headers['Authorization'] = 'Bearer ' + GH_TOKEN
    r = requests.get('https://api.github.com' + path, headers=headers, timeout=60)
    if r.status_code == 404 and allow_404:
        return None
    r.raise_for_status()
    return r.text if accept.endswith('raw') else r.json()


def clean_license(lic):
    return '' if (lic or '') in ('NOASSERTION', 'Other', 'None') else (lic or '')


def build_github(repo, opts):
    info = gh_get('/repos/' + repo)
    release = gh_get('/repos/%s/releases/latest' % repo, allow_404=True)
    chosen = pick_asset(release.get('assets', []), opts) if release else None
    if not chosen:
        for r in gh_get('/repos/%s/releases?per_page=15' % repo) or []:
            if r.get('draft'):
                continue
            chosen = pick_asset(r.get('assets', []), opts)
            if chosen:
                release = r
                break
    if not chosen:
        raise ValueError('no matching downloadable file found in the latest releases')
    asset, label, platform = chosen

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

    return {
        'title': info.get('name') or repo.split('/')[-1],
        'category': platform,
        'description': cut('\n\n'.join(parts) or 'Open-source software.', MAX_DESC),
        'url': asset['browser_download_url'],
        'size': human_size(asset.get('size')),
        'version': version,
        'image': (info.get('owner') or {}).get('avatar_url', ''),
        'license': clean_license((info.get('license') or {}).get('spdx_id')),
        'updated': (release.get('published_at') or '')[:10],
        'homepage': info.get('homepage') or info.get('html_url') or '',
        '_label': label,
    }


# ---------------------------------------------------------------- F-Droid style repos (Android)
def fdroid_index(base):
    if base not in _index_cache:
        r = requests.get(base + '/index-v2.json', headers=HEADERS, timeout=240)
        r.raise_for_status()
        _index_cache[base] = r.json()
    return _index_cache[base]


def loc(value):
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

    summary = loc(meta.get('summary')) or ''
    desc = re.sub(r'\n{3,}', '\n\n', strip_markup(loc(meta.get('description')) or '')).strip()
    icon = loc(meta.get('icon'))
    icon_name = icon.get('name') if isinstance(icon, dict) else icon
    added = best.get('added')
    updated = ''
    if isinstance(added, (int, float)) and added > 0:
        updated = datetime.fromtimestamp(added / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
    return {
        'title': loc(meta.get('name')) or package,
        'category': 'ANDROID',
        'description': cut('\n\n'.join(p for p in (summary, desc) if p) or 'Open-source Android app.', MAX_DESC),
        'url': base + '/' + fileinfo['name'].lstrip('/'),
        'size': human_size(fileinfo.get('size')),
        'version': str((best.get('manifest') or {}).get('versionName') or ''),
        'image': (base + '/' + icon_name.lstrip('/')) if icon_name else '',
        'license': meta.get('license') or '',
        'updated': updated,
        'homepage': meta.get('webSite') or meta.get('sourceCode') or '',
        '_label': 'APK',
    }


# ---------------------------------------------------------------- PyPI (Python packages)
def build_pypi(package, opts):
    r = requests.get('https://pypi.org/pypi/%s/json' % quote(package), headers=HEADERS, timeout=60)
    r.raise_for_status()
    data = r.json()
    info = data.get('info') or {}
    files = data.get('urls') or []
    if not files:
        raise ValueError('no files published for this package')
    want_sdist = (opts.get('file') or '').lower() == 'sdist'

    def rank(f):
        wheel = f.get('packagetype') == 'bdist_wheel'
        universal = wheel and f.get('filename', '').endswith('-none-any.whl')
        if want_sdist:
            return (f.get('packagetype') == 'sdist', 0, 0)
        return (wheel, universal, f.get('size', 0))
    best = max(files, key=rank)

    summary = (info.get('summary') or '').strip()
    intro = readme_intro(info.get('description') or '')
    parts = [summary] if summary else []
    if intro and intro[:60].lower() not in summary.lower():
        parts.append(intro)
    parts.append('Install with:  pip install %s' % info.get('name', package))
    lic = (info.get('license_expression') or '').strip()
    if not lic:
        for c in info.get('classifiers') or []:
            if c.startswith('License :: OSI Approved ::'):
                lic = c.split('::')[-1].replace(' License', '').strip()
                break
    if not lic or len(lic) > 40:
        lic = lic if lic and len(lic) <= 40 else ''
    urls = info.get('project_urls') or {}
    home = info.get('home_page') or urls.get('Homepage') or urls.get('Source') or urls.get('Repository') or \
        'https://pypi.org/project/%s/' % package
    return {
        'title': info.get('name') or package,
        'category': 'PYTHON',
        'description': cut('\n\n'.join(parts), MAX_DESC),
        'url': best['url'],
        'size': human_size(best.get('size')),
        'version': info.get('version') or '',
        'image': '',
        'license': lic,
        'updated': (best.get('upload_time_iso_8601') or best.get('upload_time') or '')[:10],
        'homepage': home,
        '_label': 'PYTHON',
    }


# ---------------------------------------------------------------- direct links
def probe(url):
    """Look up a file link without downloading it. Returns (status, headers)."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=60, allow_redirects=True)
        if r.status_code < 400 and r.headers.get('Content-Length'):
            return r.status_code, r.headers
    except requests.RequestException:
        pass
    r = requests.get(url, headers=HEADERS, timeout=60, stream=True, allow_redirects=True)
    try:
        return r.status_code, r.headers
    finally:
        r.close()


def build_direct(url, opts):
    if not url.lower().startswith(('http://', 'https://')):
        raise ValueError('needs a full https:// link')
    status, headers = probe(url)
    if status >= 400:
        raise ValueError('the link returned HTTP %d' % status)
    name = unquote(urlparse(url).path.rstrip('/').split('/')[-1]) or 'download'
    label, platform = classify(name)
    return {
        'title': re.sub(r'\.[A-Za-z0-9]{1,6}$', '', name) or name,
        'category': platform,
        'description': 'Direct download from the official source.',
        'url': url,
        'size': human_size(headers.get('Content-Length')),
        'version': '',
        'image': '',
        'license': '',
        'updated': '',
        'homepage': '',
        '_label': label,
        'file': name,
    }


# ---------------------------------------------------------------- scripts copied into this site
def build_script(spec, opts):
    parts = spec.split('/', 2)
    if len(parts) < 3 or not parts[2]:
        raise ValueError('use script:owner/repo/path/to/file')
    owner, repo, path = parts
    info = gh_get('/repos/%s/%s' % (owner, repo))
    ref = opts.get('ref') or info.get('default_branch') or 'main'
    meta = gh_get('/repos/%s/%s/contents/%s?ref=%s' % (owner, repo, quote(path), quote(ref)))
    if not isinstance(meta, dict) or meta.get('type') != 'file':
        raise ValueError('that path is not a single file')
    if meta.get('size', 0) > MAX_MIRROR:
        raise ValueError('file is %s, larger than the %s copy limit' % (human_size(meta.get('size')), human_size(MAX_MIRROR)))
    if meta.get('encoding') == 'base64' and meta.get('content'):
        data = base64.b64decode(meta['content'])
    else:
        rr = requests.get(meta['download_url'], headers=HEADERS, timeout=60)
        rr.raise_for_status()
        data = rr.content
    name = meta.get('name') or path.split('/')[-1]
    local = re.sub(r'[^A-Za-z0-9._-]', '_', '%s_%s__%s' % (owner, repo, name))
    os.makedirs(FILES_DIR, exist_ok=True)
    with open(os.path.join(FILES_DIR, local), 'wb') as f:
        f.write(data)
    label, platform = classify(name)
    short = re.sub(r':[a-z0-9_+-]+:', '', info.get('description') or '').strip()
    return {
        'title': name,
        'category': platform,
        'description': cut(short or 'Script from an open-source project.', MAX_DESC),
        'url': FILES_DIR.replace(os.sep, '/') + '/' + local,
        'size': human_size(len(data)),
        'version': '',
        'image': (info.get('owner') or {}).get('avatar_url', ''),
        'license': clean_license((info.get('license') or {}).get('spdx_id')),
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'homepage': info.get('html_url') or '',
        '_label': label,
        'file': name,
    }


# ---------------------------------------------------------------- assemble
def build(entry):
    s = entry['source']
    if s == 'github':
        return build_github(entry['id'], entry['opts'])
    if s == 'pypi':
        return build_pypi(entry['id'], entry['opts'])
    if s == 'script':
        return build_script(entry['id'], entry['opts'])
    if s == 'direct':
        return build_direct(entry['id'], entry['opts'])
    return build_fdroid(s, entry['id'], entry['opts'])


def finalize(item, opts):
    """Apply the user's overrides from apps.txt and build the card tag."""
    for key, target in (('title', 'title'), ('desc', 'description'), ('description', 'description'), ('version', 'version'),
                        ('license', 'license'), ('homepage', 'homepage'), ('image', 'image'), ('size', 'size')):
        if opts.get(key):
            v = opts[key]
            if key == 'title' and ' ' not in v:
                v = v.replace('_', ' ')
            item[target] = v
    if opts.get('category'):
        item['category'] = opts['category'].upper()
    label = item.pop('_label', 'FILE')
    item['tag'] = opts.get('tag') or '%s \u2022 %s' % (label, item.get('license') or 'OFFICIAL')
    return item


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
            item = finalize(build(e), e['opts'])
            item['auto'] = True
            item['source'] = e['key']
            auto.append(item)
            print('[ok]   %-44s %-9s %s  %s' % (e['key'][:44], item['category'], item.get('version', ''), item.get('size', '')))
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
