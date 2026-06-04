# 🎬 Movie Ticket Monitor

Scrapes Dendy Canberra, Hoyts, and Event Cinemas Sydney IMAX every 10 minutes
and sends Telegram notifications when tickets go live for target movies.

## Target Movies

- The Odyssey (July 17, 2026)
- Supergirl: Woman of Tomorrow (June 26, 2026)
- Spider-Man: Brand New Day (July 31, 2026)
- Avengers: Doomsday (December 18, 2026)

## Setup

### 1. Create a Telegram bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** you receive

### 2. Get your Chat ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your **chat ID** number

### 3. Set up GitHub Secrets

In your GitHub repo → Settings → Secrets and variables → Actions:

- `TELEGRAM_BOT_TOKEN` — your bot token from step 1
- `TELEGRAM_CHAT_ID` — your chat ID from step 2

### 4. Push to GitHub

The workflow runs automatically every 10 minutes. Use "Run workflow" in the
Actions tab to test manually.

## Local Testing

```bash
pip install -r requirements.txt
playwright install chromium

TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_chat_id python src/main.py
```

## How It Works

1. Three scrapers (one per cinema) load the Coming Soon and Now Showing pages
2. Movie titles are fuzzy-matched against our target list
3. State is tracked in `state/seen.json` — only new detections trigger notifications
4. Telegram sends two types of alerts:
   - 🎫 **TICKETS LIVE** — when a movie has bookable sessions
   - 📋 **Coming Soon** — when a movie first appears on a cinema's list
