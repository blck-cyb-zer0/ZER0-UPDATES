/* ZER0 football view. Usage: ZeroFootball.mount(element, leagueData)
   Also auto-mounts on any element with [data-fb-league] using the JSON in #fb-data (the league pages). */
(function (root) {
  'use strict';
  var FB = {};

  /* ---------- helpers ---------- */
  function esc(x) {
    return String(x == null ? '' : x).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function ord(n) { n = Number(n); var s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); }
  function shortDate(iso) {
    var d = new Date(String(iso) + 'T12:00:00Z');
    return isNaN(d) ? esc(iso) : d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: '2-digit', timeZone: 'UTC' });
  }
  function relDay(d) {
    var n = new Date(), a = new Date(n.getFullYear(), n.getMonth(), n.getDate()), b = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var diff = Math.round((b - a) / 86400000);
    return diff === 0 ? 'Today' : diff === 1 ? 'Tomorrow' : diff === -1 ? 'Yesterday' : '';
  }
  function dayKey(m) {
    var d = m.utc ? new Date(m.utc) : null;
    if (d && !isNaN(d)) return { key: d.getFullYear() + '-' + d.getMonth() + '-' + d.getDate(), label: d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' }), rel: relDay(d), time: d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) };
    return { key: m.when || '', label: (m.when || '').split(',')[0] || 'Fixtures', rel: '', time: (m.when || '').split(',')[1] || '' };
  }

  /* ---------- data: accept the new format and the older one ---------- */
  function norm(L) {
    if (L && L._n) return L;
    L = L || {};
    L.tm = L.tm || {}; L.teams = L.teams || {}; L.next = L.next || []; L.done = L.done || []; L.zones = L.zones || []; L.blocks = L.blocks || [];
    L.blocks.forEach(function (b) {
      b.rows.forEach(function (r) {
        if (r.id == null) r.id = r.team;
        if (!L.tm[String(r.id)]) L.tm[String(r.id)] = { n: r.team, t: r.tla || '', c: r.crest || '' };
      });
    });
    function fix(m) {
      if (m.h == null && m.home != null) { m.h = m.home; m.a = m.away; L.tm[String(m.h)] = L.tm[String(m.h)] || { n: m.home, t: '', c: '' }; L.tm[String(m.a)] = L.tm[String(m.a)] || { n: m.away, t: '', c: '' }; }
      if (m.hs == null && typeof m.score === 'string' && m.score.indexOf('-') > -1) { var p = m.score.split('-'); m.hs = +p[0]; m.as = +p[1]; }
    }
    L.next.forEach(fix); L.done.forEach(fix);
    L._n = true;
    return L;
  }
  function tmOf(L, id) { var t = L.tm[String(id)] || {}; return { id: id, n: t.n || '', t: t.t || '', c: t.c || '' }; }
  function rowOf(L, id) {
    for (var i = 0; i < L.blocks.length; i++) for (var j = 0; j < L.blocks[i].rows.length; j++) if (String(L.blocks[i].rows[j].id) === String(id)) return L.blocks[i].rows[j];
    return null;
  }
  function zoneOf(L, p) { for (var i = 0; i < L.zones.length; i++) if (p >= L.zones[i].from && p <= L.zones[i].to) return L.zones[i].cls; return ''; }
  function formOf(L, id) { var s = L.teams[String(id)]; if (s && s.f) return s.f; var r = rowOf(L, id); return (r && r.form) || []; }

  /* ---------- small pieces ---------- */
  function crest(t, size) {
    var s = size || 24;
    if (t && t.c) return '<img class="fb-crest" src="' + esc(t.c) + '" alt="" width="' + s + '" height="' + s + '" loading="lazy" decoding="async" referrerpolicy="no-referrer" data-t="' + esc(t.t || (t.n || '?').slice(0, 3)) + '">';
    return '<span class="fb-crest fb-crest-ph" style="width:' + s + 'px;height:' + s + 'px">' + esc((t && t.t) || ((t && t.n) || '?').slice(0, 3).toUpperCase()) + '</span>';
  }
  function chips(arr) { return '<span class="fb-form">' + (arr || []).map(function (r) { return '<i class="fb-r fb-r-' + esc(r) + '">' + esc(r) + '</i>'; }).join('') + '</span>'; }

  /* ---------- table ---------- */
  function tableHtml(L) {
    return L.blocks.map(function (b) {
      var rows = b.rows.map(function (t) {
        var z = zoneOf(L, t.pos), gd = Number(t.gd) || 0, T = { n: t.team, t: t.tla, c: t.crest };
        return '<tr class="fb-row' + (z ? ' fb-z fb-z-' + z : '') + '" data-tid="' + esc(t.id) + '" tabindex="0" title="Tap for ' + esc(t.team) + ' details">' +
          '<td class="fb-pos"><span>' + esc(t.pos) + '</span></td><td class="fb-team"><div>' + crest(T, 24) + '<b class="fb-name">' + esc(t.team) + '</b></div></td>' +
          '<td>' + esc(t.p) + '</td><td>' + esc(t.w) + '</td><td>' + esc(t.d) + '</td><td>' + esc(t.l) + '</td>' +
          '<td class="fb-hide">' + esc(t.gf) + '</td><td class="fb-hide">' + esc(t.ga) + '</td>' +
          '<td class="' + (gd > 0 ? 'fb-up' : gd < 0 ? 'fb-down' : '') + '">' + (gd > 0 ? '+' : '') + esc(t.gd) + '</td>' +
          '<td><b class="fb-pts">' + esc(t.pts) + '</b></td><td class="fb-fm">' + chips(t.form) + '</td></tr>';
      }).join('');
      return (b.group ? '<h3 class="fb-group">' + esc(b.group) + '</h3>' : '') +
        '<div class="fb-tw"><table><tr><th class="fb-pos">#</th><th class="fb-team l">Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th class="fb-hide">GF</th><th class="fb-hide">GA</th><th>GD</th><th>Pts</th><th class="l">Form</th></tr>' + rows + '</table></div>';
    }).join('') + legendHtml(L);
  }
  function legendHtml(L) {
    var seen = {}, h = '';
    L.zones.forEach(function (z) { if (!seen[z.cls]) { seen[z.cls] = 1; h += '<span class="fb-z-' + esc(z.cls) + '"><i></i>' + esc(z.label) + '</span>'; } });
    return (h ? '<div class="fb-legend">' + h + '</div><p class="fb-note">Usual qualification and relegation places. They can change with cup winners and European results. Tap a team for its last 10 matches.</p>' : '<p class="fb-note">Tap a team for its last 10 matches.</p>');
  }

  /* ---------- head-to-head ---------- */
  function h2hHtml(L, f, title) {
    var h = f.h2h;
    if (!h || !h.m || !h.m.length) return '';
    var H = tmOf(L, f.h), A = tmOf(L, f.a), total = (h.hw || 0) + (h.d || 0) + (h.aw || 0);
    var list = h.m.map(function (m) {
      return '<li><span class="fb-md">' + shortDate(m[0]) + '</span><span class="fb-hm">' + esc(tmOf(L, m[1]).n) + ' <b>' + esc(m[3]) + ' - ' + esc(m[4]) + '</b> ' + esc(tmOf(L, m[2]).n) + '</span></li>';
    }).join('');
    return '<h4>' + esc(title || 'Head-to-head') + ' <small style="font-weight:500;opacity:.7">last ' + esc(h.n || h.m.length) + ' meetings</small></h4>' +
      (total ? '<div class="fb-bar"><i class="h" style="flex:' + (h.hw || 0) + '"></i><i class="d" style="flex:' + (h.d || 0) + '"></i><i class="a" style="flex:' + (h.aw || 0) + '"></i></div>' +
        '<div class="fb-bl"><span><b>' + (h.hw || 0) + '</b> ' + esc(H.n) + ' wins</span><span><b>' + (h.d || 0) + '</b> draws</span><span><b>' + (h.aw || 0) + '</b> ' + esc(A.n) + ' wins</span></div>' : '') +
      '<ul class="fb-ml">' + list + '</ul>';
  }

  /* ---------- fixtures and results ---------- */
  function teamBtn(L, id, side) {
    var t = tmOf(L, id);
    return '<button type="button" class="fb-tmb ' + side + '" data-tid="' + esc(id) + '">' + crest(t, 30) + '<span>' + esc(t.n) + '</span></button>';
  }
  function cards(L, list, scored) {
    if (!list.length) return '<div class="fb-empty">' + (scored ? 'No results yet.' : 'No upcoming fixtures right now.') + '</div>';
    var out = '', last = null;
    list.forEach(function (m, i) {
      var dk = dayKey(m);
      if (dk.key !== last) { last = dk.key; out += '<div class="fb-day">' + esc(dk.rel ? dk.rel + ' · ' + dk.label : dk.label) + '</div>'; }
      var hr = rowOf(L, m.h), ar = rowOf(L, m.a);
      var meta = '<span>' + (m.md ? 'Matchday ' + esc(m.md) : '') + '</span><span>' + (!scored && hr && ar && hr.pos && ar.pos ? esc(ord(hr.pos)) + ' vs ' + esc(ord(ar.pos)) : '') + '</span>';
      var hw = scored && m.hs > m.as, aw = scored && m.as > m.hs;
      var mid = scored && m.hs != null ? '<span class="fb-score">' + esc(m.hs) + ' - ' + esc(m.as) + '</span>' : '<span class="fb-time">' + esc(dk.time || 'TBC') + '</span>';
      var btn = teamBtn(L, m.h, 'h').replace('<span>', '<span' + (hw ? ' class="fb-win"' : '') + '>');
      var btn2 = teamBtn(L, m.a, 'a').replace('<span>', '<span' + (aw ? ' class="fb-win"' : '') + '>');
      var form = !scored ? '<div class="fb-fform"><span>Form ' + chips(formOf(L, m.h)) + '</span><span>' + chips(formOf(L, m.a)) + '</span></div>' : '';
      var h2h = !scored && m.h2h && m.h2h.m && m.h2h.m.length
        ? '<button type="button" class="fb-h2hb" data-h2h="' + i + '" aria-expanded="false">Head-to-head &#9662;</button><div class="fb-h2h" hidden>' + h2hHtml(L, m) + '</div>' : '';
      out += '<article class="fb-fx"><div class="fb-meta">' + meta + '</div><div class="fb-main">' + btn + '<div class="fb-mid">' + mid + '</div>' + btn2 + '</div>' + form + h2h + '</article>';
    });
    return out;
  }

  /* ---------- team pop-up ---------- */
  function sheetHtml(L, id) {
    var T = tmOf(L, id), r = rowOf(L, id), s = L.teams[String(id)], p = r ? Number(r.p) || 0 : 0;
    var sub = r ? esc(L.name) + ' &middot; ' + esc(ord(r.pos)) + ' &middot; ' + esc(r.pts) + ' pts' : esc(L.name);
    var out = '<button type="button" class="fb-x" data-close aria-label="Close">&times;</button><div class="fb-sh"><div class="fb-sh-in">' + crest(T, 60) +
      '<div><h3>' + esc(T.n) + '</h3><p>' + sub + '</p>' + chips(formOf(L, id)) + '</div></div></div><div class="fb-sb">';
    var cell = function (v, l) { return '<div class="fb-st"><b>' + esc(v) + '</b><span>' + esc(l) + '</span></div>'; };
    if (r) {
      var cs = s ? s.cs : null, ppg = p ? (r.pts / p).toFixed(2) : '-';
      var streak = s && s.st ? ({ W: ' win', D: ' draw', L: ' defeat' }[s.st[0]] ? s.st.slice(1) + ({ W: ' win', D: ' draw', L: ' defeat' }[s.st[0]]) + (+s.st.slice(1) > 1 ? 's' : '') : '') : '';
      out += '<div class="fb-stats">' + cell(r.p, 'Played') + cell(r.w + '-' + r.d + '-' + r.l, 'W-D-L') + cell(r.gf + ':' + r.ga, 'Goals') +
        cell(ppg, 'Pts / game') + (p ? cell((r.gf / p).toFixed(1) + ' / ' + (r.ga / p).toFixed(1), 'Goals for / against') : '') + (cs != null ? cell(cs, 'Clean sheets') : '') +
        (s && s.hm ? cell(s.hm[1] + '-' + s.hm[2] + '-' + s.hm[3], 'Home W-D-L') + cell(s.aw[1] + '-' + s.aw[2] + '-' + s.aw[3], 'Away W-D-L') : '') +
        (streak ? cell(streak, 'Current run') : '') + '</div>';
    }
    if (s && s.last && s.last.length) {
      out += '<h4>Last ' + s.last.length + ' matches</h4><div class="fb-strip">' + s.last.slice().reverse().map(function (m) { return '<i class="' + esc(m[5]) + '"></i>'; }).join('') + '</div><ul class="fb-ml">' +
        s.last.map(function (m) {
          var o = tmOf(L, m[2]);
          return '<li class="fb-m"><span class="fb-md">' + shortDate(m[0]) + '</span><span class="fb-ha">' + esc(m[1]) + '</span><span class="fb-opp">' + crest(o, 22) + '<span>' + esc(o.n) + '</span></span><b class="fb-sc">' + esc(m[3]) + ' - ' + esc(m[4]) + '</b><i class="fb-r fb-r-' + esc(m[5]) + '">' + esc(m[5]) + '</i></li>';
        }).join('') + '</ul>';
    } else {
      out += '<p class="fb-note">Detailed match history for this team appears after the next data refresh.</p>';
    }
    if (s && s.next) {
      var o2 = tmOf(L, s.next.o), d = s.next.utc ? new Date(s.next.utc) : null, ok = d && !isNaN(d);
      var fx = null;
      L.next.forEach(function (f) { if (f.id && f.id === s.next.id) fx = f; });
      out += '<h4 style="margin-top:16px">Next match</h4><div class="fb-nx"><div class="fb-nx-top"><span class="fb-opp">' + crest(o2, 22) + '<span>' + (s.next.h === 'H' ? 'vs ' : 'at ') + esc(o2.n) + '</span></span>' +
        '<span class="fb-time" style="font-size:12px">' + (ok ? esc(d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' }) + ' · ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })) : 'TBC') + '</span></div>' +
        (fx ? h2hHtml(L, fx, 'Head-to-head') : '') + '</div>';
    }
    return out + '</div>';
  }

  /* ---------- views ---------- */
  function viewHtml(L) {
    return '<div class="fb-head"><h2>' + esc(L.name) + '</h2><p>' + esc(L.season) + (L.updated ? ' &middot; updated ' + esc(L.updated) : '') + ' &middot; times shown in your local time</p></div>' +
      '<div class="fb-tabs" role="tablist"><button type="button" role="tab" class="on" data-tab="table">Table</button>' +
      '<button type="button" role="tab" data-tab="next">Fixtures<b>' + L.next.length + '</b></button><button type="button" role="tab" data-tab="done">Results<b>' + L.done.length + '</b></button></div>' +
      '<div class="fb-pane" data-pane="table">' + tableHtml(L) + '</div><div class="fb-pane" data-pane="next" hidden>' + cards(L, L.next, false) +
      '</div><div class="fb-pane" data-pane="done" hidden>' + cards(L, L.done, true) + '</div>';
  }

  var sheet = null, opener = null;
  function ensureSheet() {
    if (sheet) return sheet;
    sheet = document.createElement('div');
    sheet.className = 'fb-sheet'; sheet.id = 'fbSheet'; sheet.hidden = true;
    sheet.setAttribute('role', 'dialog'); sheet.setAttribute('aria-modal', 'true'); sheet.setAttribute('aria-label', 'Team details');
    sheet.innerHTML = '<div class="fb-sheet-card"></div>';
    sheet.addEventListener('click', function (e) { if (e.target === sheet || (e.target.closest && e.target.closest('[data-close]'))) FB.closeTeam(); });
    document.body.appendChild(sheet);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') FB.closeTeam(); });
    root.addEventListener('hashchange', function () { FB.closeTeam(); });
    return sheet;
  }
  FB.openTeam = function (L, id, from) {
    L = norm(L);
    var sh = ensureSheet(), card = sh.firstChild;
    card.innerHTML = sheetHtml(L, id);
    card.scrollTop = 0;
    sh.hidden = false; opener = from || null;
    document.body.style.overflow = 'hidden';
    var x = card.querySelector('.fb-x'); if (x && x.focus) x.focus();
  };
  FB.closeTeam = function () {
    if (!sheet || sheet.hidden) return;
    sheet.hidden = true; document.body.style.overflow = '';
    if (opener && opener.focus) opener.focus();
    opener = null;
  };

  /* ---------- mount ---------- */
  FB.mount = function (el, L) {
    L = norm(L);
    el.__L = L;
    el.innerHTML = viewHtml(L);
    el.classList.add('fb');
    if (el.__fb) return;
    el.__fb = true;
    el.addEventListener('click', function (e) {
      var t = e.target, c = t.closest ? t.closest.bind(t) : null;
      if (!c) return;
      var tab = c('[data-tab]');
      if (tab) {
        var k = tab.getAttribute('data-tab');
        [].forEach.call(el.querySelectorAll('[data-tab]'), function (b) { var on = b === tab; b.classList.toggle('on', on); b.setAttribute('aria-selected', on ? 'true' : 'false'); });
        [].forEach.call(el.querySelectorAll('[data-pane]'), function (p) { p.hidden = p.getAttribute('data-pane') !== k; });
        return;
      }
      var hb = c('[data-h2h]');
      if (hb) { var open = hb.getAttribute('aria-expanded') === 'true'; hb.setAttribute('aria-expanded', open ? 'false' : 'true'); hb.nextElementSibling.hidden = open; return; }
      var row = c('[data-tid]');
      if (row) FB.openTeam(el.__L, row.getAttribute('data-tid'), row);
    });
    el.addEventListener('keydown', function (e) {
      if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('tr[data-tid]')) { e.preventDefault(); FB.openTeam(el.__L, e.target.getAttribute('data-tid'), e.target); }
    });
  };

  /* broken badges fall back to the team's letters */
  document.addEventListener('error', function (e) {
    var t = e.target;
    if (t && t.tagName === 'IMG' && t.classList.contains('fb-crest')) {
      var sp = document.createElement('span');
      sp.className = 'fb-crest fb-crest-ph'; sp.style.width = t.width + 'px'; sp.style.height = t.height + 'px';
      sp.textContent = t.getAttribute('data-t') || '?';
      if (t.parentNode) t.parentNode.replaceChild(sp, t);
    }
  }, true);

  /* league pages: read the embedded data and take over the plain table */
  function auto() {
    [].forEach.call(document.querySelectorAll('[data-fb-league]'), function (el) {
      var d = document.getElementById('fb-data');
      if (!d) return;
      try { FB.mount(el, JSON.parse(d.textContent)); } catch (err) { /* keep the plain table */ }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', auto); else auto();

  FB._t = { norm: norm, table: tableHtml, cards: cards, sheet: sheetHtml, h2h: h2hHtml, view: viewHtml, ord: ord };
  root.ZeroFootball = FB;
})(typeof window !== 'undefined' ? window : this);
