import json, os, sys, requests, time

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL = "@zer0updates"
SITE_BASE = "https://blck-cyb-zer0.github.io/ZER0-UPDATES/"
MAX_POSTS_PER_RUN = 5

CONFIGS = {
    "deals": {
        "file": "deals.json",
        "list_key": "deals",
        "tracked_file": ".posted_deals.json",
    },
    "coupons": {
        "file": "coupons.json",
        "list_key": "coupons",
        "tracked_file": ".posted_coupons.json",
    },
    "news": {
        "file": "football_news.json",
        "list_key": "articles",
        "tracked_file": ".posted_news.json",
    },
}


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={
        "chat_id": CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    })
    resp.raise_for_status()


def format_deal(item):
    title = item.get("title", "")
    desc = item.get("desc", "")
    now = item.get("now")
    was = item.get("was")
    price = f"\U0001F4B0 ${now} (was ${was})\n" if now else ""
    link = item.get("link", "")
    return f"\U0001F525 <b>{title}</b>\n{desc}\n{price}{link}".strip()


def format_coupon(item):
    store = item.get("store", "")
    discount = item.get("discount", "")
    desc = item.get("desc", "")
    code = item.get("code", "")
    link = item.get("link", "")
    return f"\U0001F3F7\uFE0F <b>{store}</b> \u2014 {discount}\n{desc}\nCode: <code>{code}</code>\n{link}".strip()


def format_news(item):
    title = item.get("title", "")
    summary = item.get("summary", "")
    link = item.get("link", "")
    return f"\U0001F4F0 <b>{title}</b>\n{summary}\n{link}".strip()


FORMATTERS = {
    "deals": format_deal,
    "coupons": format_coupon,
    "news": format_news,
}


def main():
    kind = sys.argv[1]
    seed_only = "--seed" in sys.argv
    cfg = CONFIGS[kind]

    data = load_json(cfg["file"], {})
    items = data.get(cfg["list_key"], [])

    posted = load_json(cfg["tracked_file"], [])
    posted_set = set(posted)

    new_items = [it for it in items if it.get("link") and it["link"] not in posted_set]

    if seed_only:
        # First-time setup: mark everything currently on the site as
        # already posted, without sending anything to Telegram.
        for item in new_items:
            posted.append(item["link"])
        save_json(cfg["tracked_file"], posted[-500:])
        print(f"Seeded {len(new_items)} existing {kind} items as already-posted.")
        return

    to_post = new_items[:MAX_POSTS_PER_RUN]
    formatter = FORMATTERS[kind]

    for item in to_post:
        send_message(formatter(item))
        posted.append(item["link"])
        time.sleep(1)  # be gentle with Telegram's rate limits

    if to_post:
        save_json(cfg["tracked_file"], posted[-500:])
        print(f"Posted {len(to_post)} new {kind} item(s) to Telegram.")
    else:
        print(f"No new {kind} items to post.")


if __name__ == "__main__":
    main()
