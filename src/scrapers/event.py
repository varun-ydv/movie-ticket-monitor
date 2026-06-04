"""Event Cinemas scraper (Sydney IMAX).

Event Cinemas is the hardest site — heavily JS-dependent with a cinema
selector. We need to select the right cinema and wait for content to load.
"""

from playwright.async_api import Page

from src.scrapers.base import BaseScraper, MovieListing


class EventScraper(BaseScraper):
    """Scrape Event Cinemas Coming Soon page for Sydney IMAX."""

    async def scrape(self, page: Page) -> list[MovieListing]:
        results = []

        # --- Coming Soon page ---
        await page.goto(self.config["coming_soon_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        # Try to select Sydney IMAX cinema if a selector exists
        await self._select_cinema(page)

        # Wait for movie content to load after cinema selection
        await page.wait_for_timeout(3000)

        # Extract movie listings
        results.extend(await self._extract_movies(page, "coming_soon"))

        # --- Now Showing page ---
        await page.goto(self.config["now_showing_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        await self._select_cinema(page)
        await page.wait_for_timeout(3000)

        results.extend(await self._extract_movies(page, "tickets_available"))

        # Deduplicate by title
        seen_titles = set()
        deduped = []
        for r in results:
            key = r.title.lower().strip()
            if key not in seen_titles:
                seen_titles.add(key)
                # If we have a coming_soon and tickets_available for the same movie,
                # keep the tickets_available one
                deduped.append(r)

        # Now do a second pass to prefer tickets_available over coming_soon
        final = {}
        for r in deduped:
            key = r.title.lower().strip()
            if key not in final or r.status == "tickets_available":
                final[key] = r

        print(f"[event] Found {len(final)} unique listings")
        return list(final.values())

    async def _select_cinema(self, page: Page):
        """Try to select Sydney IMAX from cinema dropdown/selector."""
        # Try common dropdown selectors
        selectors = [
            "select[name*='cinema']",
            "select[id*='cinema']",
            "[class*='cinema-selector']",
            "[class*='CinemaSelector']",
            "button[class*='cinema']",
        ]

        for selector in selectors:
            el = await page.query_selector(selector)
            if el:
                try:
                    tag = await el.evaluate("el => el.tagName.toLowerCase()")
                    if tag == "select":
                        # Try to find Sydney IMAX option
                        options = await el.query_selector_all("option")
                        for opt in options:
                            text = (await opt.inner_text()).strip().lower()
                            if "imax" in text or "sydney" in text:
                                value = await opt.get_attribute("value")
                                if value:
                                    await el.select_option(value)
                                    print(f"[event] Selected cinema option: {text}")
                                    return
                    else:
                        # Click-based selector
                        await el.click()
                        await page.wait_for_timeout(1000)
                        # Look for Sydney IMAX in the dropdown
                        imax_option = await page.query_selector("text=/sydney.*imax/i")
                        if imax_option:
                            await imax_option.click()
                            print(f"[event] Selected Sydney IMAX from dropdown")
                            return
                except Exception as e:
                    print(f"[event] Cinema selection attempt failed: {e}")
                    continue

        print("[event] Could not find cinema selector, proceeding with default")

    async def _extract_movies(self, page: Page, default_status: str) -> list[MovieListing]:
        """Extract movie listings from the current page."""
        results = []

        # Try multiple selectors
        selectors_to_try = [
            "a[href*='/Movies/']",
            "article a",
            ".movie-card a",
            ".movie-item a",
            "[class*='movie'] a",
            "[class*='Movie'] a",
            ".movie-list a",
        ]

        links = []
        for selector in selectors_to_try:
            found = await page.query_selector_all(selector)
            if found:
                links = found
                print(f"[event] Found {len(found)} links with selector: {selector}")
                break

        if not links:
            print("[event] No movie links found on page")
            return results

        for link in links:
            try:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""

                # Get the movie title — usually the first meaningful line
                title = text.split("\n")[0].strip()
                if not title or len(title) < 3:
                    continue

                if href.startswith("/"):
                    href = "https://www.eventcinemas.com.au" + href

                # Check for ticket availability indicators
                status = default_status
                card_text = text.lower()
                if any(kw in card_text for kw in ["buy tickets", "book now", "session times", "tickets available"]):
                    status = "tickets_available"

                results.append(MovieListing(
                    title=title,
                    status=status,
                    url=href or self.config["coming_soon_url"],
                    cinema_id=self.cinema_id,
                ))
            except Exception as e:
                print(f"[event] Error extracting movie from link: {e}")
                continue

        return results
