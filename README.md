# Web Crawler

A robust web crawler implementation using the `crawl4ai` library with comprehensive error handling and a clean, maintainable codebase.




## Features

- Single URL scraping with detailed error handling
- Multi-URL crawling with configurable parameters
- Standardized response formatting
- Customizable browser and crawler configurations
- Support for storage and processing callbacks
- Comprehensive logging

## Project Structure

- `routes/crawler.py`: Main crawling functionality
- `client/MafiaError.py`: Error handling utilities
- `client/ResponseGetData.py`: Response data standardization
- `crawler.py`: Command-line interface (optional)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- `crawl4ai` library

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install crawl4ai
   ```
3. Install browser dependencies (required by crawl4ai):
   ```bash
   npx playwright install
   crawl4ai-setup
   crawl4ai-doctor
   ```

### Usage Example

```python
import asyncio
from routes.crawler import scrape_url, crawl_urls
from crawl4ai.config import BrowserConfig, CrawlerRunConfig

async def main():
    # Single URL scraping
    result = await scrape_url(
        url="https://example.com",
        session_id="test-session",
    )
    print(f"Title: {result.title}")
    print(f"Content: {result.content[:100]}...")

    # Multi-URL crawling
    results = await crawl_urls(
        starting_url="https://example.com",
        session_id="test-session",
        output_folder="./output",
        delay_before_return_html=2,
    )
    print(f"Crawled {len(results)} pages")

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Configuration

### Browser Configuration

```python
from crawl4ai.config import BrowserConfig

browser_config = BrowserConfig(
    browser_type="chromium",  # or "firefox", "webkit"
    headless=True,
    timeout=30000,
    viewport={"width": 1280, "height": 720},
    extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
)
```

### Crawler Configuration

```python
from crawl4ai.config import CrawlerRunConfig, CacheMode

crawler_config = CrawlerRunConfig(
    max_pages=10,
    same_domain=True,
    include_regex="^https://example.com/blog/.*",
    exclude_regex="^https://example.com/blog/private/.*",
    cache_mode=CacheMode.BYPASS,
    delay=1.5,  # Delay between requests in seconds
)
```

## Error Handling

The crawler uses a custom error class `CrawlerRouteError` that inherits from `MafiaError` for consistent error handling. All exceptions are caught and properly formatted with detailed error messages.

## Response Format

Crawling results are standardized using the `ResponseGetDataCrawler` class, which provides a consistent interface for accessing crawled data:

```python
result = await scrape_url(url="https://example.com", session_id="test")
print(f"Success: {result.is_success}")
print(f"Status: {result.status}")
print(f"URL: {result.url}")
print(f"Content: {result.response}")
print(f"Links: {result.links}")
```

## License

MIT License

## Acknowledgments

- [crawl4ai](https://github.com/unclecode/crawl4ai): The underlying web crawling library