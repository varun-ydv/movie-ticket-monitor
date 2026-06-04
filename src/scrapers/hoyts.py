"""Hoyts scraper — the easiest cinema to scrape.

Hoyts has well-structured HTML with movie cards that include titles,
release dates, and "Tickets On Sale" / "Times & Tickets" labels.
"""

from playwright.async_api import Page

from src.scrapers.base import BaseScraper, MovieListing


class HoytsScraper(BaseScraper):
    """Scrape Hoyts Coming Soon and Now Showing pages."""

    async def scrape(self, page: Page) -> list[MovieListing]:
        results = []

        # --- Coming Soon page ---
        await page.goto(self.config["coming_soon_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)  # let JS render

        # Movie cards on the Coming Soon page
        cards = await page.query_selector_all("article, .movie-card, .movie-item, [class*='movie'], [class*='Movie']")
        if not cards:
            # Fallback: try broader selectors
            cards = await page.query_selector_all("a[href*='/Movies/']")

        for card in cards:
            title_el = await card.query_selector("h2, h3, .title, [class*='title']")
            if not title_el:
                continue
            title = (await title_el.inner_text()).strip()
            if not title:
                continue

            # Get the link to the movie page
            link_el = await card.query_selector("a[href*='/Movies/']")
            href = ""
            if link_el:
                href = await link_el.get_attribute("href") or ""
                if href.startswith("/"):
                    href = "https://www.hoyts.com.au" + href

            # Check if tickets are available
            card_text = (await card.inner_text()).lower()
            status = "coming_soon"
            if any(kw in card_text for kw in ["tickets on sale", "times & tickets", "buy tickets", "book now"]):
                status = "tickets_available"

            results.append(MovieListing(
                title=title,
                status=status,
                url=href or self.config["coming_soon_url"],
                cinema_id=self.cinema_id,
            ))

        # --- Now Showing page (tickets already live) ---
        await page.goto(self.config["now_showing_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        cards = await page.query_selector_all("article, .movie-card, .movie-item, [class*='movie'], [class*='Movie']")
        if not cards:
            cards = await page.query_selector_all("a[href*='/Movies/']")

        for card in cards:
            title_el = await card.query_selector("h2, h3, .title, [class*='title']")
            if not title_el:
                continue
            title = (await title_el.inner_text()).strip()
            if not title:
                continue

            link_el = await card.query_selector("a[href*='/Movies/']")
            href = ""
            if link_el:
                href = await link_el.get_attribute("href") or ""
                if href.startswith("/"):
                    href = "https://www.hoyts.com.au" + href

            # If it's on Now Showing, tickets are available
            results.append(MovieListing(
                title=title,
                status="tickets_available",
                url=href or self.config["now_showing_url"],
                cinema_id=self.cinema_id,
            ))

        print(f"[hoyts] Found {len(results)} listings")
        return results
