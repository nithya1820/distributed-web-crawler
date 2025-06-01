# Distributed Web Crawler with Adaptive Bloom Filter

A high-performance distributed web crawler that uses an adaptive Bloom Filter for efficient duplicate URL detection. The system automatically adjusts the Bloom Filter size based on the false positive rate to maintain optimal performance.

## Features

- **Distributed Architecture**: Scale horizontally with multiple crawler instances
- **Adaptive Bloom Filter**: Automatically adjusts size to maintain low false positive rates
- **Redis Integration**: Distributed task queue and storage
- **Resilient Design**: Falls back to in-memory queue if Redis is unavailable
- **Detailed Statistics**: Tracks crawl metrics and Bloom Filter performance

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (recommended) or Redis server installed locally

## Quick Start with Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd project
```

2. Build and start the services:
```bash
docker-compose up -d
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Run the crawler:
```bash
python -m crawler.crawler --start-url https://example.com --max-pages 100
```

## Manual Setup

1. Install Redis on your system:
   - **Windows**: Download and install from [Microsoft's Redis port](https://github.com/microsoftarchive/redis/releases)
   - **macOS**: `brew install redis`
   - **Linux**: `sudo apt-get install redis-server`

   **Alternatively, you can run Redis using Docker (recommended if you cannot install Redis locally):**
   ```bash
   docker pull redis:latest
   docker run -d -p 6379:6379 --name redis-server redis:latest
   ```
   This will start a Redis server accessible at `localhost:6379`.

2. Clone the repository and install dependencies:
```bash
git clone <repository-url>
cd project
pip install -r requirements.txt
```

3. Start Redis server:
```bash
# Linux/macOS
redis-server --daemonize yes

# Windows (if installed via installer, it might be running as a service)
# Or run: redis-server
```

## Running the Crawler

Basic usage:
```bash
python -m crawler.crawler --start-url https://example.com --max-pages 100
```

### Command Line Arguments

- `--start-url`: Initial URL to start crawling from (required)
- `--max-pages`: Maximum number of pages to crawl (default: 100)
- `--workers`: Number of concurrent workers (default: 4)
- `--bloom-capacity`: Initial Bloom Filter capacity (default: 1000)
- `--bloom-error-rate`: Target false positive rate (default: 0.01)
- `--redis-host`: Redis host (default: localhost)
- `--redis-port`: Redis port (default: 6379)

## Project Structure

```
project/
├── crawler/              # Core crawler implementation
│   ├── __init__.py
│   ├── crawler.py       # Main crawler logic
│   ├── queue.py         # Queue implementations
│   └── utils.py         # Utility functions
├── bloom_filter/        # Adaptive Bloom Filter implementation
│   ├── __init__.py
│   ├── adaptive_bloom.py  # Adaptive Bloom Filter implementation
│   └── stats.py         # Statistics tracking
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Configuration

Environment variables can be set in a `.env` file or directly in your environment:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
BLOOM_CAPACITY=1000
BLOOM_ERROR_RATE=0.01
MAX_WORKERS=4
```

## Monitoring

The crawler outputs detailed logs about:
- Pages crawled per second
- Bloom Filter statistics (size, false positive rate, etc.)
- Queue depth
- Error rates

## Troubleshooting

### Redis Connection Issues
If you see Redis connection errors:
1. Ensure Redis server is running
2. Check that the host and port in your configuration match the Redis server
3. The crawler will automatically fall back to an in-memory queue if Redis is unavailable

### Memory Usage
If experiencing high memory usage:
- Reduce the number of concurrent workers
- Decrease the Bloom Filter's initial capacity
- Increase the target error rate (at the cost of more false positives)

## License

MIT
- Real-time statistics tracking
- Fault tolerance and recovery
- Parallel processing capabilities
- Configurable crawling parameters

## Technology Stack

- Python 3.8+
- Redis for distributed storage
- Memcached for caching
- Asyncio for asynchronous processing
- Bloom Filter for duplicate detection

## Usage

The crawler can be configured through the `config/crawler_config.py` file. Key parameters include:
- Number of concurrent workers
- Crawl depth
- Bloom Filter parameters
- Storage configuration
- Rate limiting settings

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

