#!/usr/bin/env python3
"""Daily football scores/fixtures + informational predictions for ZER0 Sports."""

import json, os, sys, time
from datetime import datetime, timezone, timedelta
import requests

FOOTBALL_API_BASE = "https://api.football-data.org/v4"
COMPETITIONS = ["PL", "CL"]  # Premier League, Champions League
OUTPUT_PATH = "scores.json"
GEMINI_MODEL = "gemini-flash-latest"


def fetch_matches():
    api_key = os.environ.get("FOOTBALL_API_KEY")
    if not api_key:
        raise RuntimeError("FOOTBALL_API_KEY is not set")

    headers = {"X-Auth-Token": api_key}
    today = datetime.now(timezone.utc).date()
    date_from = today.isoformat()
    date_to = (today + timedelta(days=3)).isoformat()

    all_matches = []
    for comp in COMPETITIONS:
        url = f"{FOOTBALL_API_BASE}/competitions/{comp}/matches"
        params = {"dateFrom": date_from, "dateTo": date_to}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for m in data.get("matches", []):
                all_matches.append({
                    "competition": comp,
                    "home": m["homeTeam"]["name"],
                    "away": m["awayTeam"]["name"],
                    "status": m["status"],
                    "utc_date": m["utcDate"],
                    "home_score": m["score"]["fullTime"].get("home"),
                    "away_score": m["score"]["fullTime"].get("away"),
                })
        except Exception as e:
            print(f"[warn] failed to fetch {comp}: {e}", file=sys.stderr)

    return all_matches


PREDICTION_INSTRUCTIONS = """You are given a list of upcoming/recent football matches.
For each match that has NOT been played yet (status is not FINISHED), write a short,
informational one-sentence prediction based on general team reputation/form
(max 25 words). This is for entertainment/analysis only, not betting advice -
do not mention odds, stakes, or betting.

Return ONLY a JSON array (no prose, no markdown fences) with objects:
{ "home": "...", "away": "...", "prediction": "..." }

Only include matches with status other than FINISHED. If none qualify, return []."""


def call_gemini_with_retry(url, headers, payload, timeout, max_retries=4, base_delay=5):
    """Call the Gemini API, retrying on transient server errors (503 etc.)
    with exponential backoff before giving up."""
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.exceptions.HTTPError(f"{resp.status_code} server error", response=resp)
            resp.raise_for_status()
            return resp
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_exc = e
            if attempt == max_retries:
                break
            delay = base_delay * (2 ** (attempt - 1))
            print(f"[warn] Gemini call failed (attempt {attempt}/{max_retries}): {e}. Retrying in {delay}s...", file=sys.stderr)
            time.sleep(delay)
    raise last_exc


def build_predictions(matches):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[warn] GEMINI_API_KEY not set, skipping predictions", file=sys.stderr)
        return []

    upcoming = [m for m in matches if m["status"] != "FINISHED"]
    if not upcoming:
        return []

    prompt = PREDICTION_INSTRUCTIONS + "\n\nMATCHES:\n" + json.dumps(upcoming, indent=2)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    resp = call_gemini_with_retry(
        url,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        payload={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
        timeout=60,
    )
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except Exception as e:
        print(f"[warn] failed to parse predictions: {e}", file=sys.stderr)
        return []


def main():
    matches = fetch_matches()
    try:
        predictions = build_predictions(matches)
    except Exception as e:
        print(f"[warn] predictions failed after retries, saving matches without them: {e}", file=sys.stderr)
        predictions = []

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "matches": matches,
        "predictions": predictions,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[ok] wrote {len(matches)} matches and {len(predictions)} predictions to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

