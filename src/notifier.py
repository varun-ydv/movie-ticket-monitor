"""Telegram notification sender."""

import json
from urllib.parse import urlparse
import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _validate_url(url: str) -> str:
    """Ensure URL has https scheme and a valid network location."""
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return url
    except Exception:
        pass
    return ""


def send_telegram(text: str, reply_markup: dict | None = None):
    """Send a message via the Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[notifier] WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print("[notifier] Sent OK")
        return True
    except requests.RequestException as e:
        print(f"[notifier] Failed: {e}")
        return False


def notify_tickets_live(cinema_name: str, movie_title: str, booking_url: str):
    """Tickets are live — include booking link."""
    safe_url = _validate_url(booking_url)
    text = f"TICKETS LIVE\n{movie_title}\n{cinema_name}"
    if safe_url:
        reply_markup = {
            "inline_keyboard": [[{"text": "Book Now", "url": safe_url}]]
        }
        send_telegram(text, reply_markup=reply_markup)
    else:
        send_telegram(text)


def notify_coming_soon(cinema_name: str, movie_title: str):
    """Movie listed as coming soon."""
    text = f"Coming Soon\n{movie_title}\n{cinema_name}"
    send_telegram(text)


def notify_error(cinema_name: str, error: str):
    """Scraper error alert."""
    text = f"Scraper Error\n{cinema_name}\nCheck GitHub Actions logs."
    send_telegram(text)
