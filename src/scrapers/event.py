"""Event Cinemas scraper (Sydney IMAX).

Event Cinemas renders movies as text elements (not links) in a structured
pattern: "ON SALE" marker, movie title, date, "Times & Tickets" / "More Info".
After clicking "IMAX Sydney", movies load via JavaScript.
We parse the page text to extract this structured data.
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

        # Select IMAX Sydney
        await self._select_imax_sydney(page)
        await page.wait_for_timeout(5000)  # Extra time for data load

        results.extend(await self._parse_movie_list(page))

        # --- Now Showing page ---
        try:
            await page.goto(self.config["now_showing_url"], wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            await self._select_imax_sydney(page)
            await page.wait_for_timeout(5000)

            listings = await self._parse_movie_list(page)
            # If found on Now Showing, mark as tickets_available
            for l in listings:
                l.status = "tickets_available"
            results.extend(listings)
        except Exception as e:
            print(f"[event] Error scraping now showing: {e}")

        # Deduplicate: prefer tickets_available over coming_soon
        final = {}
        for r in results:
            key = r.title.lower().strip()
            if key not in final or r.status == "tickets_available":
                final[key] = r

        print(f"[event] Found {len(final)} unique listings")
        return list(final.values())

    async def _select_imax_sydney(self, page: Page) -> bool:
        """Click IMAX Sydney in the cinema selector via JS click."""
        try:
            clicked = await page.evaluate('''() => {
                const labels = document.querySelectorAll('label, span, div, a');
                for (const el of labels) {
                    if (el.textContent.trim() === 'IMAX Sydney') {
                        el.click();
                        return true;
                    }
                }
                return false;
            }''')
            if clicked:
                print("[event] Selected IMAX Sydney cinema")
            return clicked
        except Exception as e:
            print(f"[event] Cinema selection error: {e}")
            return False

    async def _parse_movie_list(self, page: Page) -> list[MovieListing]:
        """Extract movie listings with real URLs from Event Cinemas.

        Uses JavaScript to find <a href="/Movie/..."> links which have the
        actual movie slugs. Determines status from whether "Times & Tickets"
        text appears near the movie card.
        """
        raw = await page.evaluate('''() => {
            const movies = {};
            const links = document.querySelectorAll('a[href^="/Movie/"]');
            links.forEach(a => {
                const href = a.getAttribute('href');
                // Get the raw text and split into lines
                const lines = a.textContent.split(/\\n/).map(l => l.trim()).filter(l => l.length > 0);

                // Find the movie title line: not a date, not "ON SALE", not "Trailer", not "More Info"
                let title = '';
                for (const line of lines) {
                    if (line.length >= 3 && line.length <= 60 &&
                        !/^(ON SALE|Times|More Info|Trailer|\\d{1,2}\\s)/.test(line)) {
                        title = line;
                        break;
                    }
                }
                if (!title) return;

                // Strip any remaining noise: "CTC" rating, dates, "Trailer"
                title = title.replace(/\\s*CTC\\s*/g, ' ').trim();

                // Check if the parent card has "Times & Tickets" (means tickets are on sale)
                const card = a.closest('[class*="movie"]') || a.parentElement?.parentElement;
                const cardText = card ? card.textContent.toLowerCase() : '';
                const status = cardText.includes('times & tickets') ? 'tickets_available' : 'coming_soon';

                // Deduplicate by href
                if (!movies[href]) {
                    movies[href] = { title, status, href };
                }
            });
            return Object.values(movies);
        }''')

        results = []
        for m in raw:
            url = "https://www.eventcinemas.com.au" + m["href"]
            results.append(MovieListing(
                title=m["title"],
                status=m["status"],
                url=url,
                cinema_id=self.cinema_id,
            ))

        print(f"[event] Extracted {len(results)} movies with real URLs")
        return results
