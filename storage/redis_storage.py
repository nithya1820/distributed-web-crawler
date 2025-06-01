import redis
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class RedisStorage:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.page_key = 'pages'
        self.stats_key = 'stats'

    def save_page(self, url, content):
        """Save a webpage to Redis."""
        try:
            page_data = {
                'url': url,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            self.redis.rpush(self.page_key, json.dumps(page_data))
            return True
        except Exception as e:
            print(f"Error saving page: {str(e)}")
            return False

    def get_page(self, url):
        """Retrieve a webpage by URL."""
        try:
            pages = self.redis.lrange(self.page_key, 0, -1)
            for page in pages:
                page_data = json.loads(page)
                if page_data['url'] == url:
                    return page_data
            return None
        except Exception as e:
            print(f"Error getting page: {str(e)}")
            return None

    def save_stats(self, stats):
        """Save crawler statistics."""
        try:
            self.redis.set(self.stats_key, json.dumps(stats))
            return True
        except Exception as e:
            print(f"Error saving stats: {str(e)}")
            return False

    def get_stats(self):
        """Retrieve crawler statistics."""
        try:
            stats = self.redis.get(self.stats_key)
            return json.loads(stats) if stats else None
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return None

    def get_all_pages(self):
        """Retrieve all crawled pages."""
        try:
            pages = self.redis.lrange(self.page_key, 0, -1)
            return [json.loads(page) for page in pages]
        except Exception as e:
            print(f"Error getting all pages: {str(e)}")
            return []

    def close(self):
        """Close the Redis connection."""
        self.redis.close()
