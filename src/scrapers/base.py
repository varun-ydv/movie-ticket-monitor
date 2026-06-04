"""Base scraper class — shared Playwright setup and retry logic."""

from dataclasses import dataclass
from abc import ABC, abstractmethod
import asyncio
import random
import time

from playwright.async_api import async_playwright, Browser, Page


@dataclass
class MovieListing:
    """A movie found on a cinema website."""
    title: str           # Raw title from the website
    status: str          # "coming_soon" or "tickets_available"
    url: str             # Direct link to the movie/booking page
    cinema_id: str       # Key from CINEMAS config


class BaseScraper(ABC):
    """Abstract base for cinema scrapers."""

    def __init__(self, cinema_id: str, cinema_config: dict):
        self.cinema_id = cinema_id
        self.cinema_name = cinema_config["name"]
        self.config = cinema_config

    @abstractmethod
    async def scrape(self, page: Page) -> list[MovieListing]:
        """Scrape the cinema site. Receives a ready-to-use Playwright Page."""
        ...

    async def run(self) -> list[MovieListing]:
        """Launch browser, run scraper, return results. Handles lifecycle."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = await browser.new_context(
                user_agent=self._random_user_agent(),
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            try:
                results = await self._retry_scrape(page)
                return results
            finally:
                await browser.close()

    async def _retry_scrape(self, page: Page, max_retries: int = 3) -> list[MovieListing]:
        """Retry scraping with exponential backoff."""
        for attempt in range(max_retries):
            try:
                # Random delay to avoid looking like a bot
                await asyncio.sleep(random.uniform(1.0, 3.0))
                results = await self.scrape(page)
                return results
            except Exception as e:
                wait = 2 ** attempt + random.uniform(0, 1)
                print(f"[{self.cinema_id}] Attempt {attempt + 1} failed: {e}. Waiting {wait:.1f}s")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait)
                else:
                    raise

    @staticmethod
    def _random_user_agent() -> str:
        agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        ]
        return random.choice(agents)
