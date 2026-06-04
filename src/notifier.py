"""Telegram notification sender."""

import json
import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(text: str, parse_mode: str = "Markdown", reply_markup: dict | None = None):
    """Send a message via the Telegram Bot API.

    Returns True on success, False on failure.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[notifier] WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping notification")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[notifier] Sent Telegram message OK")
        return True
    except requests.RequestException as e:
        print(f"[notifier] Failed to send Telegram message: {e}")
        return False


def notify_tickets_live(cinema_name: str, movie_title: str, release: str, booking_url: str):
    """Send a TICKETS LIVE alert — the urgent notification."""

    text = (
        f"🎫 *TICKETS LIVE: {movie_title}*\n"
        f"📍 {cinema_name}\n"
        f"📅 Release: {release}\n"
        f"🔗 [Book Now]({booking_url})"
    )

    # Inline keyboard with direct booking link
    reply_markup = {
        "inline_keyboard": [
            [{"text": "🎟️ Book Tickets Now", "url": booking_url}]
        ]
    }

    send_telegram(text, reply_markup=reply_markup)


def notify_coming_soon(cinema_name: str, movie_title: str, release: str, page_url: str):
    """Send a COMING SOON notification — lower urgency."""
    text = (
        f"📋 *Coming Soon: {movie_title}*\n"
        f"📍 {cinema_name}\n"
        f"📅 Release: {release}\n"
        f"🔗 [View]({page_url})"
    )
    send_telegram(text)


def notify_error(cinema_name: str, error: str):
    """Send an error alert so you know a scraper is broken."""
    text = f"⚠️ *Scraper Error: {cinema_name}*\n`{error}`"
    send_telegram(text)
