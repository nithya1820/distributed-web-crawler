import asyncio
import random
from datetime import datetime, timedelta
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrawlScheduler:
    def __init__(self, config: Dict):
        self.config = config
        self.url_queue = asyncio.Queue()
        self.pending_urls = set()
        self.last_crawled = {}  # URL -> timestamp
        self.rate_limit = config.get('crawl_delay', 1.0)
        self.max_depth = config.get('max_depth', 5)

    def is_rate_limited(self, url: str) -> bool:
        """Check if URL is rate limited."""
        if url not in self.last_crawled:
            return False
        
        elapsed = datetime.now() - self.last_crawled[url]
        return elapsed.total_seconds() < self.rate_limit

    def schedule_url(self, url: str, depth: int = 0) -> bool:
        """Schedule a URL for crawling."""
        if depth > self.max_depth:
            return False

        if url in self.pending_urls:
            return False

        if self.is_rate_limited(url):
            return False

        self.pending_urls.add(url)
        self.url_queue.put_nowait((url, depth))
        return True

    async def get_next_url(self) -> str:
        """Get next URL to crawl."""
        while True:
            try:
                url, depth = await self.url_queue.get()
                self.url_queue.task_done()
                self.pending_urls.remove(url)
                return url, depth
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)

    def update_last_crawled(self, url: str):
        """Update last crawled timestamp for URL."""
        self.last_crawled[url] = datetime.now()

    def get_stats(self) -> Dict:
        """Get scheduler statistics."""
        return {
            'pending_urls': len(self.pending_urls),
            'url_queue_size': self.url_queue.qsize(),
            'last_crawled_count': len(self.last_crawled)
        }

async def main():
    # Example usage
    config = {
        'crawl_delay': 1.0,
        'max_depth': 5
    }
    scheduler = CrawlScheduler(config)

    # Schedule some URLs
    start_urls = ['https://example.com']
    for url in start_urls:
        scheduler.schedule_url(url)

    # Get next URL
    while True:
        try:
            url, depth = await scheduler.get_next_url()
            print(f"Processing URL: {url} (depth: {depth})")
            scheduler.update_last_crawled(url)
        except asyncio.QueueEmpty:
            break

if __name__ == "__main__":
    asyncio.run(main())
