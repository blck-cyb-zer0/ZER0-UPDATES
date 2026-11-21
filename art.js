/* ZER0 generated artwork: a unique, colourful banner for any app or tool that has no picture of its own.
   ZeroArt.svg(name, category) returns an SVG string. Same name = same picture, every time. */
(function (w) {
  var BASE = { android: 142, windows: 212, linux: 28, tools: 268, scripts: 268, script: 268, python: 48, media: 330, files: 190 };
  var uid = 0;
  function hash(s) { var h = 2166136261; s = String(s || ''); for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rnd(seed) { return function () { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; }; }
  function initials(name) {
    var t = String(name || '?').replace(/^zero[-_ ]*/i, '').replace(/([a-z])([A-Z])/g, '$1 $2').split(/[^A-Za-z0-9]+/).filter(Boolean);
    if (t.length > 1) return (t[0].charAt(0) + t[1].charAt(0)).toUpperCase();
    return (t[0] || '?').slice(0, 2).toUpperCase();
  }
  function hsl(h, s, l, a) { return 'hsl(' + Math.round(((h % 360) + 360) % 360) + ',' + s + '%,' + l + '%' + (a == null ? '' : ',' + a) + ')'; }
  function svg(name, cat, left) {
    var key = String(cat || '').toLowerCase(), r = rnd(hash(name) ^ 0x9e3779b9);
    var hue = BASE[key] != null ? BASE[key] + (r() * 56 - 28) : (hash(key || name) % 360) + (r() * 30 - 15);
    var h2 = hue + 38 + r() * 46, id = 'za' + (++uid);
    var out = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 120" preserveAspectRatio="' + (left ? 'xMinYMid' : 'xMidYMid') + ' slice" role="img" aria-label="' + String(name || 'App').replace(/[<>&"]/g, '') + ' artwork">';
    out += '<defs><linearGradient id="' + id + 'g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="' + hsl(hue, 68, 30) + '"/><stop offset="1" stop-color="' + hsl(h2, 72, 13) + '"/></linearGradient>';
    out += '<radialGradient id="' + id + 'r"><stop offset="0" stop-color="' + hsl(hue + 18, 92, 62, 0.65) + '"/><stop offset="1" stop-color="' + hsl(hue + 18, 92, 62, 0) + '"/></radialGradient>';
    out += '<pattern id="' + id + 'p" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="#fff" stroke-opacity=".06"/></pattern>';
    out += '<filter id="' + id + 'b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="12"/></filter></defs>';
    out += '<rect width="320" height="120" fill="url(#' + id + 'g)"/><rect width="320" height="120" fill="url(#' + id + 'p)"/>';
    out += '<circle cx="' + Math.round(180 + r() * 120) + '" cy="' + Math.round(10 + r() * 70) + '" r="' + Math.round(70 + r() * 40) + '" fill="url(#' + id + 'r)"/>';
    for (var i = 0; i < 3; i++) {
      out += '<circle cx="' + Math.round(r() * 320) + '" cy="' + Math.round(r() * 120) + '" r="' + Math.round(22 + r() * 34) + '" fill="' + hsl(hue + r() * 90, 85, 58, 0.30) + '" filter="url(#' + id + 'b)"/>';
    }
    for (var j = 0; j < 3; j++) {
      var s = Math.round(34 + r() * 56), x = Math.round(150 + r() * 150), y = Math.round(r() * 90), rot = Math.round(r() * 80 - 40);
      out += '<rect x="' + x + '" y="' + y + '" width="' + s + '" height="' + s + '" rx="' + Math.round(s * 0.22) + '" transform="rotate(' + rot + ' ' + (x + s / 2) + ' ' + (y + s / 2) + ')" fill="none" stroke="#fff" stroke-opacity="' + (0.10 + r() * 0.12).toFixed(2) + '" stroke-width="1.6"/>';
    }
    for (var k = 0; k < 9; k++) out += '<circle cx="' + Math.round(r() * 320) + '" cy="' + Math.round(r() * 120) + '" r="' + (1 + r() * 1.6).toFixed(1) + '" fill="#fff" fill-opacity="' + (0.25 + r() * 0.4).toFixed(2) + '"/>';
    out += '<text x="22" y="76" font-family="Poppins,Inter,system-ui,sans-serif" font-size="54" font-weight="800" letter-spacing="1" fill="#000" fill-opacity=".25" transform="translate(2 3)">' + initials(name) + '</text>';
    out += '<text x="22" y="76" font-family="Poppins,Inter,system-ui,sans-serif" font-size="54" font-weight="800" letter-spacing="1" fill="#fff" fill-opacity=".95">' + initials(name) + '</text></svg>';
    return out;
  }
  w.ZeroArt = { svg: svg, initials: initials };
})(window);
