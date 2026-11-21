(function () {
  const WORKER_URL = "https://zer0-updates.hckbos77.workers.dev";

  const style = document.createElement("style");
  style.textContent = `
    #zer0-chat-bubble {
      position: fixed; bottom: 90px; right: 20px; height: 56px;
      border-radius: 28px; background: linear-gradient(135deg, #2f6bff, #1e3cc8);
      color: white; display: flex; align-items: center; gap: 10px;
      padding: 4px 6px 4px 18px; cursor: pointer; z-index: 9999;
      box-shadow: 0 4px 14px rgba(30,60,200,0.4);
      -webkit-tap-highlight-color: transparent; outline: none; user-select: none;
    }
    #zer0-chat-bubble-label { font-weight: bold; font-size: 15px; font-family: 'JetBrains Mono', monospace; white-space: nowrap; }
    #zer0-chat-bubble-avatar {
      position: relative;
      width: 46px; height: 46px; border-radius: 50%; background: white;
      display: flex; align-items: center; justify-content: center; font-size: 24px;
      flex-shrink: 0;
    }
    .zer0-glitch-tap { animation: zer0-glitch-tap 0.4s steps(2, jump-none); }
    @keyframes zer0-glitch-tap {
      0% { clip-path: inset(0 0 0 0); transform: translate(0,0) scale(1); filter: none; }
      15% { clip-path: inset(30% 0 40% 0); transform: translate(-5px,3px) scale(1.03); filter: hue-rotate(90deg) brightness(1.6); }
      30% { clip-path: inset(60% 0 5% 0); transform: translate(5px,-4px) scale(0.97); filter: hue-rotate(180deg) brightness(1.9); }
      45% { clip-path: inset(5% 0 65% 0); transform: translate(-4px,0) scale(1.02); filter: hue-rotate(270deg) brightness(1.4); }
      60% { clip-path: inset(0 0 0 0); transform: translate(4px,-3px) scale(0.98); filter: brightness(2.2); }
      75% { clip-path: inset(0 0 0 0); transform: translate(-3px,2px) scale(1.01); filter: none; }
      100% { clip-path: inset(0 0 0 0); transform: translate(0,0) scale(1); filter: none; }
    }
    .zer0-bounce { animation: zer0-bounce 0.4s ease; }
    @keyframes zer0-bounce {
      0% { transform: scale(1); }
      30% { transform: scale(0.85); }
      55% { transform: scale(1.15); }
      80% { transform: scale(0.95); }
      100% { transform: scale(1); }
    }

    /* ---- Periodic idle glitch (emoji cycle + RGB split), every 1.5s ---- */
    #zer0-chat-bubble-avatar::before,
    #zer0-chat-bubble-avatar::after {
      content: attr(data-emoji);
      position: absolute;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      opacity: 0;
      pointer-events: none;
    }
    #zer0-chat-bubble-avatar.zer0-idle-glitch {
      animation: zer0-idle-shake 0.5s steps(2, end);
    }
    #zer0-chat-bubble-avatar.zer0-idle-glitch::before {
      animation: zer0-idle-red 0.5s steps(2, end);
      color: #ff2b4d;
      text-shadow: 0 0 4px #ff2b4d;
    }
    #zer0-chat-bubble-avatar.zer0-idle-glitch::after {
      animation: zer0-idle-cyan 0.5s steps(2, end);
      color: #2be5ff;
      text-shadow: 0 0 4px #2be5ff;
    }
    @keyframes zer0-idle-shake {
      0%   { transform: translate(0,0); }
      15%  { transform: translate(-3px, 2px); }
      30%  { transform: translate(3px, -2px); }
      45%  { transform: translate(-2px, -2px); }
      60%  { transform: translate(2px, 2px); }
      75%  { transform: translate(-1px, 1px); }
      100% { transform: translate(0,0); }
    }
    @keyframes zer0-idle-red {
      0%   { opacity: 0; transform: translate(-50%, -50%); }
      15%  { opacity: 0.85; transform: translate(calc(-50% - 4px), calc(-50% - 1px)); }
      35%  { opacity: 0.6;  transform: translate(calc(-50% + 3px), calc(-50% + 1px)); }
      55%  { opacity: 0.85; transform: translate(calc(-50% - 2px), calc(-50% + 2px)); }
      75%  { opacity: 0.4;  transform: translate(calc(-50% + 4px), calc(-50% - 1px)); }
      100% { opacity: 0; transform: translate(-50%, -50%); }
    }
    @keyframes zer0-idle-cyan {
      0%   { opacity: 0; transform: translate(-50%, -50%); }
      15%  { opacity: 0.85; transform: translate(calc(-50% + 4px), calc(-50% + 1px)); }
      35%  { opacity: 0.6;  transform: translate(calc(-50% - 3px), calc(-50% - 1px)); }
      55%  { opacity: 0.85; transform: translate(calc(-50% + 2px), calc(-50% - 2px)); }
      75%  { opacity: 0.4;  transform: translate(calc(-50% - 4px), calc(-50% + 1px)); }
      100% { opacity: 0; transform: translate(-50%, -50%); }
    }

    #zer0-chat-window {
      position: fixed; bottom: 158px; right: 20px; width: 320px; max-width: 90vw;
      height: 440px; background: #ffffff; border: 1px solid #e9eaee;
      border-radius: 20px; display: flex; flex-direction: column;
      z-index: 9999; overflow: hidden; font-family: 'Inter', 'JetBrains Mono', monospace;
      opacity: 0; transform: scale(0.85) translateY(20px);
      transform-origin: bottom right; pointer-events: none;
      transition: opacity 0.25s ease, transform 0.25s ease;
      box-shadow: 0 20px 50px rgba(0,0,0,0.25);
    }
    #zer0-chat-window.zer0-open {
      opacity: 1; transform: scale(1) translateY(0); pointer-events: auto;
    }
    #zer0-chat-header {
      background: linear-gradient(135deg, #2f6bff, #1e3cc8);
      color: white; padding: 12px 16px;
      font-weight: bold; font-size: 14px;
      display: flex; justify-content: space-between; align-items: center;
      flex-shrink: 0;
    }
    #zer0-chat-close {
      cursor: pointer; font-size: 16px; opacity: 0.85;
      width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
      border-radius: 50%; transition: background 0.15s ease;
    }
    #zer0-chat-close:hover { background: rgba(255,255,255,0.15); opacity: 1; }

    #zer0-chat-messages {
      flex: 1; overflow-y: auto; padding: 16px 14px; color: #1a1a1a; font-size: 13.5px;
      display: flex; flex-direction: column; gap: 14px;
      background: #ffffff;
    }
    #zer0-chat-messages::-webkit-scrollbar { width: 0; }

    .zer0-msg-row { display: flex; flex-direction: column; max-width: 88%; }
    .zer0-msg-row.user { align-self: flex-end; align-items: flex-end; }
    .zer0-msg-row.bot { align-self: flex-start; align-items: flex-start; }

    .zer0-msg-with-avatar { display: flex; gap: 8px; align-items: flex-start; }
    .zer0-avatar {
      flex: 0 0 auto; width: 28px; height: 28px; border-radius: 50%;
      background: #fff; border: 1px solid #ececef;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 2px 5px rgba(0,0,0,0.08); font-size: 14px;
    }

    .zer0-msg {
      line-height: 1.5; padding: 10px 13px; font-size: 13.5px; white-space: pre-line;
      word-wrap: break-word;
    }
    .zer0-msg.bot {
      background: linear-gradient(180deg, #1c2333, #0c0f18);
      color: #e9eaee;
      border-radius: 4px 16px 16px 16px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .zer0-msg.user {
      background: linear-gradient(135deg, #2f6bff, #1e4fe0);
      color: #fff;
      border-radius: 16px 16px 4px 16px;
      box-shadow: 0 4px 12px rgba(47,107,255,0.3);
    }

    #zer0-chat-input-row {
      display: flex; align-items: center; gap: 8px;
      padding: 10px 12px; border-top: 1px solid #f0f1f3; background: #fff;
      flex-shrink: 0;
    }
    #zer0-chat-input {
      flex: 1; padding: 10px 14px; background: #f4f5f7; color: #1a1a1a;
      border: none; outline: none; font-size: 13.5px; border-radius: 18px;
      font-family: 'Inter', sans-serif;
    }
    #zer0-chat-input::placeholder { color: #a7abb3; }
    #zer0-chat-send {
      flex: 0 0 auto; width: 36px; height: 36px; border-radius: 12px;
      background: linear-gradient(135deg, #6d86ff, #1e4fe0);
      color: white; border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 10px rgba(47,107,255,0.35);
      transition: transform 0.12s ease, box-shadow 0.12s ease;
      padding: 0;
    }
    #zer0-chat-send svg { width: 16px; height: 16px; transform: translateX(-1px); }
    #zer0-chat-send:hover { box-shadow: 0 6px 14px rgba(47,107,255,0.45); transform: translateY(-1px); }
    #zer0-chat-send:active { transform: translateY(0) scale(0.9); box-shadow: 0 2px 8px rgba(47,107,255,0.3); }

    .zer0-typing { display: flex; gap: 4px; padding: 2px 0; }
    .zer0-typing span {
      width: 6px; height: 6px; border-radius: 50%; background: #8899a6;
      animation: zer0-typing-bounce 1.4s infinite ease-in-out both;
    }
    .zer0-typing span:nth-child(1) { animation-delay: -0.32s; }
    .zer0-typing span:nth-child(2) { animation-delay: -0.16s; }
    @keyframes zer0-typing-bounce {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
      40% { transform: scale(1); opacity: 1; }
    }
  `;
  document.head.appendChild(style);

  const bubble = document.createElement("div");
  bubble.id = "zer0-chat-bubble";
  bubble.innerHTML = `<span id="zer0-chat-bubble-label">ZERO AI</span><span id="zer0-chat-bubble-avatar" data-emoji=""><img src="icon-192.png" alt="ZERO Assistant" width="40" height="40" draggable="false"></span>`;
  document.body.appendChild(bubble);

  const win = document.createElement("div");
  win.id = "zer0-chat-window";
  win.innerHTML = `
    <div id="zer0-chat-header">
      ZERO AI
      <span id="zer0-chat-close">✕</span>
    </div>
    <div id="zer0-chat-messages"></div>
    <div id="zer0-chat-input-row">
      <input id="zer0-chat-input" type="text" placeholder="Ask ZERO AI anything..." />
      <button id="zer0-chat-send" aria-label="Send message">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M3 11.5L20.5 3L13 20.5L10.5 13.5L3 11.5Z" stroke="white" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" fill="white" fill-opacity="0.15"/>
        </svg>
      </button>
    </div>
  `;
  document.body.appendChild(win);

  const messagesEl = document.getElementById("zer0-chat-messages");
  const inputEl = document.getElementById("zer0-chat-input");
  const avatarEl = document.getElementById("zer0-chat-bubble-avatar");

  // ---- Periodic idle glitch loop: cycles 🤖 -> 👾 -> 👽 every 1.5s ----
  const ZER0_IDLE_EMOJIS = ["LOGO", "🤖", "👾", "👽"];
  let zer0IdleEmojiIndex = 0;
  const ZER0_IDLE_INTERVAL_MS = 1500;
  const ZER0_IDLE_BURST_MS = 500;

  setInterval(() => {
    zer0IdleEmojiIndex = (zer0IdleEmojiIndex + 1) % ZER0_IDLE_EMOJIS.length;
    const nextEmoji = ZER0_IDLE_EMOJIS[zer0IdleEmojiIndex];

    avatarEl.setAttribute("data-emoji", nextEmoji === "LOGO" ? "" : nextEmoji);
    avatarEl.classList.remove("zer0-idle-glitch");
    void avatarEl.offsetWidth;
    avatarEl.classList.add("zer0-idle-glitch");

    setTimeout(() => {
      if (nextEmoji === "LOGO") { avatarEl.innerHTML = '<img src="icon-192.png" alt="ZERO Assistant" width="40" height="40" draggable="false">'; } else { avatarEl.textContent = nextEmoji; }
    }, ZER0_IDLE_BURST_MS * 0.4);

    setTimeout(() => {
      avatarEl.classList.remove("zer0-idle-glitch");
    }, ZER0_IDLE_BURST_MS);
  }, ZER0_IDLE_INTERVAL_MS);

  bubble.onclick = () => {
    const opening = !win.classList.contains("zer0-open");
    win.classList.toggle("zer0-open");
    if (opening && typeof gtag === "function") { gtag("event", "ai_assistant_opened"); }
    bubble.classList.remove("zer0-bounce");
    void bubble.offsetWidth;
    bubble.classList.remove("zer0-glitch-tap");
    void bubble.offsetWidth;
    bubble.classList.add("zer0-glitch-tap");
    bubble.classList.add("zer0-bounce");
  };
  document.getElementById("zer0-chat-close").onclick = () => {
    win.classList.remove("zer0-open");
  };

  const BOT_AVATAR = `<div class="zer0-avatar">🤖</div>`;

  function addMessage(text, sender) {
    const row = document.createElement("div");
    row.className = "zer0-msg-row " + sender;

    if (sender === "bot") {
      row.innerHTML = `
        <div class="zer0-msg-with-avatar">
          ${BOT_AVATAR}
          <div class="zer0-msg bot"></div>
        </div>
      `;
      row.querySelector(".zer0-msg").textContent = text;
    } else {
      row.innerHTML = `<div class="zer0-msg user"></div>`;
      row.querySelector(".zer0-msg").textContent = text;
    }

    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return row.querySelector(".zer0-msg");
  }

  function addTyping() {
    const row = document.createElement("div");
    row.className = "zer0-msg-row bot";
    row.innerHTML = `
      <div class="zer0-msg-with-avatar">
        ${BOT_AVATAR}
        <div class="zer0-msg bot">
          <div class="zer0-typing"><span></span><span></span><span></span></div>
        </div>
      </div>
    `;
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return row.querySelector(".zer0-msg");
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    addMessage(text, "user");
    inputEl.value = "";
    const thinkingEl = addTyping();

    try {
      const resp = await fetch(WORKER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await resp.json();
      const safeReply = (data.reply || "Sorry, I couldn't get a response.").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      thinkingEl.innerHTML = safeReply.replace(/\n/g, "<br>") + "<br><br>Kindly join our <a href=\"https://t.me/zer0updates\" target=\"_blank\" style=\"color:#1d9bf0; text-decoration:underline;\">Telegram channel</a> to get the most out of our services.";
    } catch (e) {
      thinkingEl.textContent = "Error: " + e.message;
    }
  }

  document.getElementById("zer0-chat-send").onclick = sendMessage;
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
})();



/* ZERO AI: stays out of the way (compact, docks to the edge, hides while scrolling, draggable) */
(function () {
  var b = document.getElementById('zer0-chat-bubble'), win = document.getElementById('zer0-chat-window');
  if (!b) return;
  var css = document.createElement('style');
  css.textContent =
    '#zer0-chat-bubble{bottom:calc(76px + env(safe-area-inset-bottom,0px));right:12px;height:48px;border-radius:24px;padding:3px 3px 3px 14px;gap:8px;touch-action:none;transition:transform .35s ease,opacity .3s ease,padding .3s ease,gap .3s ease}' +
    '#zer0-chat-bubble-label{font-size:13px;letter-spacing:.08em;max-width:120px;overflow:hidden;transition:max-width .35s ease,opacity .3s ease}' +
    '#zer0-chat-bubble.zer0-compact{padding:3px;gap:0}#zer0-chat-bubble.zer0-compact #zer0-chat-bubble-label{max-width:0;opacity:0}' +
    '#zer0-chat-bubble-avatar{width:42px;height:42px;background:#07070f;border:1px solid rgba(255,255,255,.28);overflow:hidden}' +
    '#zer0-chat-bubble-avatar img{width:100%;height:100%;object-fit:cover;display:block;border-radius:50%;pointer-events:none}' +
    '#zer0-chat-bubble-avatar.zer0-idle-glitch img{filter:drop-shadow(2px 0 #ff2b4d) drop-shadow(-2px 0 #2be5ff)}' +
    '#zer0-chat-bubble.zer0-dock{transform:translateX(62%);opacity:.8}#zer0-chat-bubble.zer0-away{transform:translateX(130%);opacity:0;pointer-events:none}' +
    '#zer0-chat-bubble.zer0-gone{opacity:0;pointer-events:none;transform:scale(.7)}' +
    '#zer0-chat-window{bottom:calc(136px + env(safe-area-inset-bottom,0px));right:12px;width:min(340px,92vw)}';
  document.head.appendChild(css);

  function isOpen() { return win && win.classList.contains('zer0-open'); }
  var tIdle, tScroll, lastY = window.scrollY || 0, justDragged = false;
  function wake() { b.classList.remove('zer0-dock', 'zer0-away'); clearTimeout(tIdle); tIdle = setTimeout(function () { if (!isOpen()) b.classList.add('zer0-dock'); }, 6000); }
  setTimeout(function () { b.classList.add('zer0-compact'); }, 4000);
  wake();
  window.addEventListener('scroll', function () {
    var y = window.scrollY || 0;
    if (y > lastY + 4 && !isOpen()) b.classList.add('zer0-away');
    lastY = y; clearTimeout(tScroll);
    tScroll = setTimeout(function () { b.classList.remove('zer0-away'); if (!isOpen()) b.classList.add('zer0-dock'); }, 1200);
  }, { passive: true });
  setInterval(function () { var m = document.getElementById('dlModal'); b.classList.toggle('zer0-gone', !!(m && !m.hidden)); }, 500);

  // drag it anywhere; remembers the spot
  function place(x, y) {
    x = Math.min(Math.max(0, x), window.innerWidth - b.offsetWidth); y = Math.min(Math.max(0, y), window.innerHeight - b.offsetHeight);
    b.style.left = x + 'px'; b.style.top = y + 'px'; b.style.right = 'auto'; b.style.bottom = 'auto';
  }
  try { var p = JSON.parse(localStorage.getItem('zer0-ai-pos') || 'null'); if (p) place(p[0], p[1]); } catch (e) {}
  var sx = null, sy, ox, oy, drag = false;
  b.addEventListener('pointerdown', function (e) { wake(); sx = e.clientX; sy = e.clientY; var r = b.getBoundingClientRect(); ox = r.left; oy = r.top; drag = false; });
  window.addEventListener('pointermove', function (e) {
    if (sx === null) return;
    var dx = e.clientX - sx, dy = e.clientY - sy;
    if (!drag && Math.sqrt(dx * dx + dy * dy) < 8) return;
    drag = true; place(ox + dx, oy + dy);
  });
  window.addEventListener('pointerup', function () {
    if (sx === null) return;
    if (drag) { justDragged = true; setTimeout(function () { justDragged = false; }, 80); try { localStorage.setItem('zer0-ai-pos', JSON.stringify([parseFloat(b.style.left), parseFloat(b.style.top)])); } catch (e) {} }
    sx = null;
  });
  b.addEventListener('click', function (e) { if (justDragged) { e.stopImmediatePropagation(); e.preventDefault(); } }, true);
  b.addEventListener('mouseenter', wake);
})();
