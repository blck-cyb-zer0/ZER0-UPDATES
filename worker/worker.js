const ALLOWED = [
  "https://zeroupdates.org",
  "https://www.zeroupdates.org",
  "https://blck-cyb-zer0.github.io",
];

async function getDownloads() {
  try {
    const r = await fetch("https://zeroupdates.org/catalog.json", { cf: { cacheTtl: 600, cacheEverything: true } });
    const j = await r.json();
    const list = Array.isArray(j) ? j : (j.items || j.downloads || j.catalog || j.apps || []);
    return list.slice(0, 40).map((x) =>
      "- " + [x.title, x.cat && "(" + x.cat + ")", x.size, x.version && "v" + x.version, x.desc && "- " + String(x.desc).slice(0, 90)]
        .filter(Boolean).join(" ")
    ).join("\n");
  } catch (e) {
    return "";
  }
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const corsHeaders = {
      "Access-Control-Allow-Origin": ALLOWED.includes(origin) ? origin : ALLOWED[0],
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Vary": "Origin",
    };

    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders });
    if (request.method !== "POST") return new Response("Method not allowed", { status: 405, headers: corsHeaders });

    try {
      const body = await request.json();
      const userMessage = String(body.message || "").slice(0, 600);
      if (!userMessage) {
        return new Response(JSON.stringify({ reply: "Ask me about deals, football news, coupons or downloads." }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }

      const downloads = await getDownloads();
      const system =
        "You are the friendly assistant for ZER0 Updates (zeroupdates.org). The site has these sections: " +
        "Home, Football news, News, Deals, Coupons, and Downloads (free apps, APKs, tools and scripts). " +
        "People use the Get button on a download, wait a few seconds, then tap Download. " +
        "Keep answers short, plain text only (no markdown, no asterisks). " +
        "Point people to the right section by name. Never invent download names, links or prices." +
        (downloads ? "\n\nCurrent downloads on the site:\n" + downloads : "");

      const groqResp = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${env.GROQ_API_KEY.trim()}`,
        },
        body: JSON.stringify({
          model: "openai/gpt-oss-120b",
          messages: [
            { role: "system", content: system },
            { role: "user", content: userMessage },
          ],
        }),
      });

      const data = await groqResp.json();
      const reply = data.choices?.[0]?.message?.content || "Sorry, I couldn't get a response.";

      return new Response(JSON.stringify({ reply }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    } catch (e) {
      return new Response(JSON.stringify({ reply: "Error: " + e.message }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
  },
};
