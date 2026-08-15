(function () {
  const GEMINI_API_KEY = "AQ.Ab8RN6LVGMH-kNBGBQIHHLXyXAmhhJwcHSlXv9XfU7Z1Xm9Wnw";
  const GEMINI_MODEL = "gemini-flash-latest";

  const style = document.createElement("style");
  style.textContent = `
    #zer0-chat-bubble {
      position: fixed; bottom: 20px; right: 20px; width: 56px; height: 56px;
      border-radius: 50%; background: #1d9bf0; color: white; font-size: 26px;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; z-index: 9999; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    #zer0-chat-window {
      position: fixed; bottom: 88px; right: 20px; width: 300px; max-width: 90vw;
      height: 400px; background: #15202b; border: 1px solid #2f3336;
      border-radius: 12px; display: none; flex-direction: column;
      z-index: 9999; overflow: hidden; font-family: sans-serif;
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
  `;
  document.head.appendChild(style);

  const bubble = document.createElement("div");
  bubble.id = "zer0-chat-bubble";
  bubble.textContent = "💬";
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
    win.style.display = win.style.display === "flex" ? "none" : "flex";
  };
  document.getElementById("zer0-chat-close").onclick = () => {
    win.style.display = "none";
  };

  function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = "zer0-msg " + sender;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    addMessage(text, "user");
    inputEl.value = "";
    addMessage("...", "bot");
    const thinkingEl = messagesEl.lastChild;

    try {
      const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY },
          body: JSON.stringify({
            contents: [{ role: "user", parts: [{ text: text }] }],
            systemInstruction: {
              parts: [{ text: "You are a friendly assistant for ZER0 Updates, a site with deals, football news/scores, coupons, and memes. Keep answers short and helpful." }]
            }
          }),
        }
      );
      const data = await resp.json();
      const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || "Sorry, I couldn't get a response.";
      thinkingEl.textContent = reply;
    } catch (e) {
      thinkingEl.textContent = "Something went wrong. Try again.";
    }
  }

  document.getElementById("zer0-chat-send").onclick = sendMessage;
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
})();
