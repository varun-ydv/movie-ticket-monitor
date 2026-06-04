"""Movie Ticket Monitor — main entry point.

Runs all cinema scrapers, matches results against target movies,
and sends Telegram notifications for new state changes.
"""

import asyncio
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import CINEMAS, MOVIES
from src.matcher import match_movie
from src.state import load_state, save_state, make_key, is_new, mark_seen
from src.notifier import notify_tickets_live, notify_coming_soon, notify_error
from src.scrapers.hoyts import HoytsScraper
from src.scrapers.dendy import DendyScraper
from src.scrapers.event import EventScraper


SCRAPER_CLASSES = {
    "hoyts": HoytsScraper,
    "dendy": DendyScraper,
    "event": EventScraper,
}


async def scrape_cinema(cinema_id: str) -> list:
    """Run a single cinema scraper. Returns list of MovieListing or empty on error."""
    config = CINEMAS[cinema_id]
    scraper_cls = SCRAPER_CLASSES[cinema_id]
    scraper = scraper_cls(cinema_id, config)

    print(f"\n{'='*50}")
    print(f"Scraping: {config['name']}")
    print(f"{'='*50}")

    try:
        listings = await scraper.run()
        return listings
    except Exception as e:
        print(f"ERROR scraping {cinema_id}: {e}")
        notify_error(config["name"], str(e))
        return []


async def main():
    print("🎬 Movie Ticket Monitor")
    print(f"Watching for: {', '.join(m['title'] for m in MOVIES)}")
    print(f"Cinemas: {', '.join(c['name'] for c in CINEMAS.values())}")
    print()

    # Load previous state
    state = load_state()

    # Run all scrapers concurrently
    tasks = [scrape_cinema(cinema_id) for cinema_id in CINEMAS]
    all_results = await asyncio.gather(*tasks)

    # Process results
    notifications_sent = 0

    for cinema_id, listings in zip(CINEMAS.keys(), all_results):
        cinema_name = CINEMAS[cinema_id]["name"]
        print(f"\n[{cinema_id}] Processing {len(listings)} listings...")

        for listing in listings:
            movie = match_movie(listing.title)
            if not movie:
                continue  # Not one of our target movies

            print(f"  ✅ Matched: '{listing.title}' → {movie['title']} ({listing.status})")

            # Build state key and check if this is new
            key = make_key(cinema_id, movie["title"], listing.status)

            if is_new(state, key):
                print(f"  📢 NEW! Sending notification for {movie['title']} at {cinema_name}")
                mark_seen(state, key)

                if listing.status == "tickets_available":
                    notify_tickets_live(
                        cinema_name=cinema_name,
                        movie_title=movie["title"],
                        release=movie["release"],
                        booking_url=listing.url,
                    )
                else:
                    notify_coming_soon(
                        cinema_name=cinema_name,
                        movie_title=movie["title"],
                        release=movie["release"],
                        page_url=listing.url,
                    )
                notifications_sent += 1
            else:
                print(f"  ⏭️  Already seen: {key}")

    # Save updated state
    save_state(state)

    print(f"\n{'='*50}")
    print(f"Done. Notifications sent: {notifications_sent}")
    print(f"State entries: {len(state)}")


if __name__ == "__main__":
    asyncio.run(main())
