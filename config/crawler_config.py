START_URLS = [
    'https://wikipedia.org',
    'https://python.org',
    'https://docs.python.org/3/'
]

ALLOWED_DOMAINS = [
    'wikipedia.org',
    'python.org',
    'docs.python.org'
]

CONFIG = {
    'num_workers': 3,  # Number of concurrent crawler workers
    'max_depth': 2,    # Maximum depth to crawl
    'crawl_delay': 2,  # Delay between requests (in seconds) to be polite
    'timeout': 30,     # Request timeout (in seconds)
    'bloom_filter': {
        'initial_capacity': 1000000,
        'error_rate': 0.001
    },
    'redis': {
        'host': 'localhost',
        'port': 6379
    },
    'memcached': {
        'host': 'localhost',
        'port': 11211
    }
}
