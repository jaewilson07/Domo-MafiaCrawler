# Domo-MafiaCrawler

## Overview

Domo-MafiaCrawler is a web crawling library designed to scrape individual URLs or crawl multiple interconnected pages. It leverages the `crawl4ai` library for advanced crawling capabilities and includes features like rate limiting, error handling, and progress logging. Additionally, it uses OpenAI to generate text embeddings and summaries of crawled documents before storing them in Supabase.

## Installation

To install the required dependencies, ensure you have Python 3.8 or later installed, then run:

```bash
pip install -r requirements.txt
```

## How It Works

1. **Configuration**: The library provides default configurations for the browser and crawler, which can be customized as needed.
2. **Crawling**: Use `crawl_url` to scrape a single URL or `crawl_urls` to crawl multiple pages starting from an initial URL.
3. **Text Processing**: OpenAI is used to generate embeddings and summaries for the crawled content.
4. **Data Storage**: Processed data, including embeddings and summaries, is stored in Supabase for further use.
5. **Logging**: Progress and summary logs are automatically generated and stored in the `LOGS` directory.
6. **Callbacks**: Optional `storage_fn` and `process_fn` callbacks allow you to save or process the crawled data.

### Example Usage

```python
from routes.crawler import crawl_url, crawl_urls

# Single URL crawl
response = await crawl_url(
    url="https://example.com",
    session_id="session123"
)

# Multi-page crawl
responses = await crawl_urls(
    starting_url="https://example.com",
    session_id="session123"
)
```

## Features

- **Rate Limiting**: Prevents overloading servers with configurable delays and retries.
- **Error Handling**: Standardized error responses using `ResponseGetDataCrawler`.
- **Text Processing**: Uses OpenAI to generate text embeddings and summaries for crawled content.
- **Data Storage**: Stores processed data in Supabase for easy access and scalability.
- **Progress Logging**: Logs progress and results to files for monitoring.
- **Customizable Callbacks**: Save or process crawled data using user-defined functions.
