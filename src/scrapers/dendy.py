"""Dendy Canberra scraper.

Dendy's site is JS-heavy with a simple movie list. We load the Coming Soon
page and extract movie titles from the rendered content.
"""

from playwright.async_api import Page

from src.scrapers.base import BaseScraper, MovieListing


class DendyScraper(BaseScraper):
    """Scrape Dendy Canberra Coming Soon page."""

    async def scrape(self, page: Page) -> list[MovieListing]:
        results = []

        # --- Coming Soon page ---
        await page.goto(self.config["coming_soon_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)  # Dendy is JS-heavy, give it time

        # Try multiple selectors for movie entries
        selectors_to_try = [
            "a[href*='movie']",
            "a[href*='Movie']",
            ".movie-item",
            ".movie-card",
            "[class*='coming-soon'] a",
            "[class*='ComingSoon'] a",
            "article a",
            ".film a",
        ]

        links = []
        for selector in selectors_to_try:
            found = await page.query_selector_all(selector)
            if found:
                links = found
                print(f"[dendy] Found {len(found)} links with selector: {selector}")
                break

        if not links:
            # Last resort: grab all links with meaningful text
            all_links = await page.query_selector_all("a")
            for link in all_links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()
                if text and len(text) > 3 and ("/movie" in href.lower() or "session" in href.lower()):
                    links.append(link)

        for link in links:
            text = (await link.inner_text()).strip()
            href = await link.get_attribute("href") or ""

            # Clean up multi-line titles (take first line)
            title = text.split("\n")[0].strip()
            if not title or len(title) < 3:
                continue

            if href.startswith("/"):
                href = "https://canberra.dendy.com.au" + href

            # Determine status — check if the link/page mentions sessions/tickets
            status = "coming_soon"
            page_text = (await link.inner_text()).lower()
            if any(kw in page_text for kw in ["session", "book", "buy", "ticket"]):
                status = "tickets_available"

            results.append(MovieListing(
                title=title,
                status=status,
                url=href or self.config["coming_soon_url"],
                cinema_id=self.cinema_id,
            ))

        # --- Also check Now Showing / home page ---
        await page.goto(self.config["now_showing_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        for selector in selectors_to_try:
            found = await page.query_selector_all(selector)
            if found:
                for link in found:
                    text = (await link.inner_text()).strip()
                    href = await link.get_attribute("href") or ""
                    title = text.split("\n")[0].strip()
                    if not title or len(title) < 3:
                        continue
                    if href.startswith("/"):
                        href = "https://canberra.dendy.com.au" + href
                    results.append(MovieListing(
                        title=title,
                        status="tickets_available",
                        url=href or self.config["now_showing_url"],
                        cinema_id=self.cinema_id,
                    ))
                break

        # Deduplicate by title
        seen_titles = set()
        deduped = []
        for r in results:
            key = r.title.lower().strip()
            if key not in seen_titles:
                seen_titles.add(key)
                deduped.append(r)

        print(f"[dendy] Found {len(deduped)} unique listings")
        return deduped
