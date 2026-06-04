"""Dendy Canberra scraper.

Dendy uses the Quasar framework. Coming Soon movies are in
<div class="movie-info"> cards with titles in <div class="text-h6">.
We use JS evaluation for reliable extraction.
"""

from playwright.async_api import Page

from src.scrapers.base import BaseScraper, MovieListing


class DendyScraper(BaseScraper):
    """Scrape Dendy Canberra Coming Soon and Now Showing pages."""

    async def scrape(self, page: Page) -> list[MovieListing]:
        results = []

        # --- Coming Soon page ---
        await page.goto(self.config["coming_soon_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        movies = await self._extract_movies_js(page, "coming_soon")
        results.extend(movies)

        # --- Now Showing page ---
        try:
            await page.goto(self.config["now_showing_url"], wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)

            movies = await self._extract_movies_js(page, "tickets_available")
            results.extend(movies)
        except Exception as e:
            print(f"[dendy] Error scraping now showing: {e}")

        # Deduplicate: prefer tickets_available over coming_soon
        final = {}
        for r in results:
            key = r.title.lower().strip()
            if key not in final or r.status == "tickets_available":
                final[key] = r

        print(f"[dendy] Found {len(final)} unique listings")
        return list(final.values())

    async def _extract_movies_js(self, page: Page, default_status: str) -> list[MovieListing]:
        """Extract movie titles via JavaScript — more reliable than CSS selectors."""
        raw = await page.evaluate('''(defaultStatus) => {
            const movies = [];
            const infos = document.querySelectorAll('.movie-info');
            infos.forEach(info => {
                const titleEl = info.querySelector('.text-h6');
                if (titleEl) {
                    const title = titleEl.textContent.trim();
                    const fullText = info.textContent.toLowerCase();
                    let status = defaultStatus;
                    if (fullText.includes('session') || fullText.includes('book') || fullText.includes('buy tickets')) {
                        status = 'tickets_available';
                    }
                    movies.push({ title, status });
                }
            });
            return movies;
        }''', default_status)

        return [
            MovieListing(
                title=m["title"],
                status=m["status"],
                url=self.config["coming_soon_url"],
                cinema_id=self.cinema_id,
            )
            for m in raw
            if m["title"] and len(m["title"]) >= 3
        ]
