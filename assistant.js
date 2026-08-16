(function () {
  const WORKER_URL = "https://zer0-updates.hckbos77.workers.dev";

  const style = document.createElement("style");
  style.textContent = `
    #zer0-chat-bubble {
      position: fixed; bottom: 20px; right: 20px; height: 56px;
      border-radius: 28px; background: linear-gradient(135deg, #1e3cc8, #1d9bf0);
      color: white; display: flex; align-items: center; gap: 10px;
      padding: 4px 6px 4px 18px; cursor: pointer; z-index: 9999;
      box-shadow: 0 4px 14px rgba(30,60,200,0.4);
      -webkit-tap-highlight-color: transparent; outline: none; user-select: none;
    }
    #zer0-chat-bubble-label { font-weight: bold; font-size: 15px; font-family: 'Space Grotesk', sans-serif; white-space: nowrap; }
    #zer0-chat-bubble-avatar {
      width: 46px; height: 46px; border-radius: 50%; background: white;
      display: flex; align-items: center; justify-content: center; font-size: 24px;
      flex-shrink: 0;
    }
    .zer0-glitch-tap { animation: zer0-glitch-tap 0.3s ease; }
    @keyframes zer0-glitch-tap {
      0% { clip-path: inset(0 0 0 0); transform: translate(0,0); }
      20% { clip-path: inset(20% 0 40% 0); transform: translate(-2px,1px); }
      40% { clip-path: inset(60% 0 10% 0); transform: translate(2px,-1px); }
      60% { clip-path: inset(10% 0 70% 0); transform: translate(-1px,0); }
      100% { clip-path: inset(0 0 0 0); transform: translate(0,0); }
    }
    .zer0-bounce { animation: zer0-bounce 0.4s ease; }
    @keyframes zer0-bounce {
      0% { transform: scale(1); }
      30% { transform: scale(0.85); }
      55% { transform: scale(1.15); }
      80% { transform: scale(0.95); }
      100% { transform: scale(1); }
    }
    #zer0-chat-window {
      position: fixed; bottom: 88px; right: 20px; width: 300px; max-width: 90vw;
      height: 400px; background: #15202b; border: 1px solid #2f3336;
      border-radius: 12px; display: flex; flex-direction: column;
      z-index: 9999; overflow: hidden; font-family: sans-serif;
      opacity: 0; transform: scale(0.85) translateY(20px);
      transform-origin: bottom right; pointer-events: none;
      transition: opacity 0.25s ease, transform 0.25s ease;
    }
    #zer0-chat-window.zer0-open {
      opacity: 1; transform: scale(1) translateY(0); pointer-events: auto;
    }
    #zer0-chat-header {
      background: #1d9bf0; color: white; padding: 10px 14px;
      font-weight: bold; display: flex; justify-content: space-between; align-items: center;
    }
    #zer0-chat-close { cursor: pointer; font-size: 18px; }
    #zer0-chat-messages {
      flex: 1; overflow-y: auto; padding: 10px; color: #e7e9ea; font-size: 14px;
    }
    .zer0-msg { margin-bottom: 10px; line-height: 1.4; }
    .zer0-msg.user { text-align: right; color: #1d9bf0; }
    #zer0-chat-input-row { display: flex; border-top: 1px solid #2f3336; }
    #zer0-chat-input {
      flex: 1; padding: 10px; background: #15202b; color: white;
      border: none; outline: none; font-size: 14px;
    }
    #zer0-chat-send {
      padding: 10px 14px; background: #1d9bf0; color: white; border: none; cursor: pointer;
    }
    .zer0-typing { display: flex; gap: 4px; padding: 4px 0; }
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
  bubble.innerHTML = `<span id="zer0-chat-bubble-label">ZER0 Assistant</span><span id="zer0-chat-bubble-avatar">🤖</span>`;
  document.body.appendChild(bubble);

  const win = document.createElement("div");
  win.id = "zer0-chat-window";
  win.innerHTML = `
    <div id="zer0-chat-header">
      ZER0 Assistant
      <span id="zer0-chat-close">✕</span>
    </div>
    <div id="zer0-chat-messages"></div>
    <div id="zer0-chat-input-row">
      <input id="zer0-chat-input" type="text" placeholder="Ask me anything..." />
      <button id="zer0-chat-send">➤</button>
    </div>
  `;
  document.body.appendChild(win);

  const messagesEl = document.getElementById("zer0-chat-messages");
  const inputEl = document.getElementById("zer0-chat-input");

  bubble.onclick = () => {
    win.classList.toggle("zer0-open");
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

  function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = "zer0-msg " + sender;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function addTyping() {
    const div = document.createElement("div");
    div.className = "zer0-msg bot";
    div.innerHTML = '<div class="zer0-typing"><span></span><span></span><span></span></div>';
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
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
      thinkingEl.textContent = data.reply || "Sorry, I couldn't get a response.";
    } catch (e) {
      thinkingEl.textContent = "Error: " + e.message;
    }
  }

  document.getElementById("zer0-chat-send").onclick = sendMessage;
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
})();
