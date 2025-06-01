import asyncio
import aiohttp
from bs4 import BeautifulSoup
from bloom_filter.adaptive_bloom import AdaptiveBloomFilter
from storage.redis_storage import RedisStorage
import redis
import logging
import random
from urllib.parse import urljoin, urlparse
import time
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Queue:
    """Base Queue interface"""
    def push(self, item):
        pass
    
    def pop(self):
        pass

class RedisQueue(Queue):
    """Redis-backed distributed queue"""
    def __init__(self, name, host='localhost', port=6379):
        try:
            self.db = redis.StrictRedis(host=host, port=port, db=0, socket_timeout=2)
            # Test connection
            self.db.ping()
            self.key = name
            self.is_connected = True
            print("Successfully connected to Redis. Using distributed queue.")
        except Exception as e:
            print(f"Redis connection failed: {e}. Falling back to local queue.")
            self.is_connected = False
            self.local_queue = LocalQueue(name)

    def push(self, item):
        if self.is_connected:
            self.db.lpush(self.key, item)
        else:
            self.local_queue.push(item)

    def pop(self):
        if self.is_connected:
            return self.db.rpop(self.key)
        else:
            return self.local_queue.pop()

class LocalQueue(Queue):
    """In-memory queue for local operation"""
    def __init__(self, name):
        self.queue = deque()
        self.name = name
        print(f"Using local in-memory queue: {name}")

    def push(self, item):
        self.queue.append(item)

    def pop(self):
        try:
            return self.queue.popleft()
        except IndexError:
            return None

class WebCrawler:
    def __init__(self, config):
        self.config = config
        self.allowed_domains = config.get('allowed_domains', [])
        self.bloom_filter = AdaptiveBloomFilter()
        self.storage = RedisStorage()
        self.queue = RedisQueue('url_queue', host=config['redis']['host'], port=config['redis']['port'])
        self.max_urls = 50
        self.crawled = 0
        self.duplicates = 0
        self.errors = 0
        self.unique = 0
        self.empty_pops = 0
        self.invalid_urls = 0
        self.session = None

    async def initialize_session(self):
        self.session = aiohttp.ClientSession()

    async def fetch(self, url):
        try:
            async with self.session.get(url, timeout=self.config['timeout']) as response:
                if response.status == 200 and 'text/html' in response.headers.get('content-type', ''):
                    return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            self.errors += 1
        return None

    async def extract_and_enqueue_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('http')]
        random.shuffle(links)
        count = 0
        for link in links:
            if count >= 10:
                break
            if not self.bloom_filter.contains(link):
                self.queue.push(link)
                count += 1

    async def crawl(self, start_urls):
        await self.initialize_session()
        # Seed the queue
        for url in start_urls:
            self.queue.push(url)
        attempts = 0
        while self.crawled < self.max_urls:
            raw_url = self.queue.pop()
            if not raw_url:
                self.empty_pops += 1
                await asyncio.sleep(1)
                continue
            url = raw_url.decode('utf-8') if isinstance(raw_url, bytes) else raw_url
            attempts += 1
            # Check if URL is valid
            if not self.is_valid_url(url):
                self.invalid_urls += 1
                continue
                
            if self.bloom_filter.contains(url):
                self.duplicates += 1
                # Don't adapt during crawl
                continue
            html = await self.fetch(url)
            if html:
                self.bloom_filter.add(url)
                self.storage.save_page(url, html)
                self.crawled += 1
                self.unique += 1
                print(f"[{self.crawled}] ✓ Crawled: {url[:80]}...")
                await self.extract_and_enqueue_links(html)
                # Don't adapt during crawl
        await self.session.close()
        
        # Now adapt the Bloom filter at the end
        print("\nAdapting Bloom filter size at the end of crawling...")
        print(f"Initial capacity: {self.bloom_filter.bloom_filter.capacity}")
        print(f"Initial error rate: {self.bloom_filter.bloom_filter.error_rate}")
        
        # Sample current FPR before adaptation
        initial_fpr = self.bloom_filter.sample_fpr(200) * 100
        print(f"Current False Positive Rate: {initial_fpr:.2f}%")
        
        # Force adaptation with a very low threshold
        old_threshold = self.bloom_filter.adaptation_threshold
        self.bloom_filter.adaptation_threshold = 0.01  # 1% threshold to force resize
        
        # Try to adapt up to 3 times
        for i in range(3):
            print(f"Adaptation attempt {i+1}...")
            result = self.bloom_filter.adapt()
            new_fpr = self.bloom_filter.sample_fpr(200) * 100
            print(f"  New capacity: {self.bloom_filter.bloom_filter.capacity}")
            print(f"  New error rate: {self.bloom_filter.bloom_filter.error_rate}")
            print(f"  New FPR: {new_fpr:.2f}%")
            if new_fpr < 1.0:  # Stop if FPR is below 1%
                break
        
        # Restore original threshold
        self.bloom_filter.adaptation_threshold = old_threshold
        
        print(f"Final capacity after adaptation: {self.bloom_filter.bloom_filter.capacity}")
        print(f"Final error rate: {self.bloom_filter.bloom_filter.error_rate}")
        self.print_stats(attempts)

    def is_valid_url(self, url):
        parsed = urlparse(url)
        # If no allowed_domains are specified, accept all domains
        if not self.allowed_domains:
            return parsed.scheme in ['http', 'https']
        return (parsed.scheme in ['http', 'https'] and parsed.netloc in self.allowed_domains)

    # Worker logic is now in crawl()

    def print_stats(self, attempts):
        bloom_stats = self.bloom_filter.get_stats()
        print("\n=== Crawl Statistics ===")
        print(f"Total queue pops (attempted): {attempts}")
        print(f"Total pages crawled (unique fetches): {self.crawled}")
        print(f"Unique pages found: {self.unique}")
        print(f"Duplicate pages detected: {self.duplicates}")
        print(f"Errors encountered: {self.errors}")
        print(f"Empty queue pops: {self.empty_pops}")
        print(f"Invalid URLs skipped: {self.invalid_urls}")
        
        # Verify all attempts are accounted for
        accounted = self.crawled + self.duplicates + self.errors + self.empty_pops + self.invalid_urls
        print(f"Total accounted for: {accounted} of {attempts} attempts")
        if accounted != attempts:
            print(f"WARNING: {attempts - accounted} attempts unaccounted for!")
        print("\n=== Bloom Filter Statistics ===")
        print(f"Total checks performed: {bloom_stats['total_checks']}")
        print(f"Sampled False Positive Rate: {bloom_stats['last_fpr']*100:.2f}% (samples: {bloom_stats['fpr_samples']})")
        print(f"Sampled False Negative Rate: {bloom_stats['last_fnr']*100:.2f}% (samples: {bloom_stats['fnr_samples']})")
        print(f"Bloom Filter capacity: {bloom_stats['capacity']}")
        print(f"Bloom Filter error rate: {bloom_stats['error_rate']}")
        print(f"Bloom Filter inserted count: {bloom_stats['inserted_count']}")
        print("Crawling completed.")

if __name__ == "__main__":
    import config.crawler_config as config
    
    async def main():
        crawler = WebCrawler(config.CONFIG)
        start_urls = config.START_URLS
        
        try:
            await crawler.crawl(start_urls)
        except KeyboardInterrupt:
            logger.info("Crawler interrupted by user")

    asyncio.run(main())
