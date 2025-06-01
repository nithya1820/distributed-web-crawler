import re
from urllib.parse import urlparse
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_url(url: str) -> str:
    """Normalize URL by removing fragments and query parameters."""
    parsed = urlparse(url)
    normalized = parsed._replace(fragment='')
    normalized = normalized._replace(query='')
    return normalized.geturl()

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc

def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme) and bool(parsed.netloc)
    except:
        return False

def extract_links(html: str, base_url: str) -> List[str]:
    """Extract all links from HTML content."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            full_url = urljoin(base_url, href)
            if is_valid_url(full_url):
                links.append(full_url)
    return links

def get_page_title(html: str) -> Optional[str]:
    """Extract page title from HTML."""
    from bs4 import BeautifulSoup
    try:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else None
        return title.strip() if title else None
    except:
        return None

def get_page_content(html: str) -> str:
    """Extract main content from HTML."""
    from bs4 import BeautifulSoup
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except:
        return ''
