"""Dendy Canberra scraper.

Dendy uses the Quasar framework. Coming Soon movies are in
<div class="movie-info"> cards with titles in <div class="text-h6">.
Individual movie pages at /movie/{slug} show session times when tickets are live.
"""

from playwright.async_api import Page

from src.scrapers.base import BaseScraper, MovieListing
from src.matcher import match_movie


class DendyScraper(BaseScraper):
    """Scrape Dendy Canberra Coming Soon page and check individual movie pages."""

    async def scrape(self, page: Page) -> list[MovieListing]:
        results = []

        # --- Coming Soon page ---
        await page.goto(self.config["coming_soon_url"], wait_until="domcontentloaded", timeout=30000)

        # Wait for movie cards to render (Quasar JS framework is slow)
        try:
            await page.wait_for_selector(".movie-info", timeout=15000)
            print("[dendy] Movie cards loaded")
        except Exception:
            print("[dendy] WARNING: .movie-info not found, retrying with longer wait...")
            await page.wait_for_timeout(10000)

        movies = await self._extract_movies_js(page)
        results.extend(movies)

        # --- Deep-check TARGET movies for ticket availability ---
        # Only check movies that match our watchlist (not all 68!)
        for listing in results:
            matched = match_movie(listing.title)
            if matched and listing.status == "coming_soon":
                has_sessions = await self._check_movie_page(page, listing.title)
                if has_sessions:
                    listing.status = "tickets_available"
                    print(f"[dendy] 🎫 {listing.title} has sessions!")
                else:
                    print(f"[dendy] 📋 {listing.title} - no sessions yet")

        print(f"[dendy] Found {len(results)} listings")
        return results

    async def _extract_movies_js(self, page: Page) -> list[MovieListing]:
        """Extract movie titles from the Coming Soon page via JavaScript."""
        raw = await page.evaluate(r'''() => {
            const movies = [];
            const infos = document.querySelectorAll('.movie-info');
            infos.forEach(info => {
                const titleEl = info.querySelector('.text-h6');
                if (titleEl) {
                    movies.push(titleEl.textContent.trim());
                }
            });
            return movies;
        }''')

        return [
            MovieListing(
                title=title,
                status="coming_soon",
                url=f"https://canberra.dendy.com.au/movie/{self._slugify(title)}",
                cinema_id=self.cinema_id,
            )
            for title in raw
            if title and len(title) >= 3
        ]

    async def _check_movie_page(self, page: Page, title: str) -> bool:
        """Check if a movie's individual page has bookable sessions."""
        slug = self._slugify(title)
        url = f"https://canberra.dendy.com.au/movie/{slug}"

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)

            # Look for session time buttons (format: "3:20 PMEnds at 6:01 PM")
            has_sessions = await page.evaluate(r'''() => {
                const btns = document.querySelectorAll('.q-btn');
                return Array.from(btns).some(b => /\d{1,2}:\d{2}\s*(AM|PM)/.test(b.textContent));
            }''')

            return has_sessions
        except Exception as e:
            print(f"[dendy] Error checking {slug}: {e}")
            return False

    @staticmethod
    def _slugify(title: str) -> str:
        """Convert a movie title to a URL slug matching Dendy's pattern."""
        slug = title.lower()
        # Remove special characters, keep letters/numbers/spaces/hyphens
        slug = "".join(c if c.isalnum() or c in (" ", "-") else "" for c in slug)
        slug = slug.replace(" ", "-")
        # Collapse multiple hyphens
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug.strip("-")
