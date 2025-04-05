"""
Web Crawler Routes Module

This module provides route handlers for web crawling functionality using crawl4ai.
It includes functions for scraping individual URLs and crawling multiple connected URLs.

The module handles all web crawling operations with proper error handling and
standardized response formatting via ResponseGetDataCrawler objects.
"""

# required Exports
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter

# Standard library imports
import logging
import json
import asyncio
import argparse
import sys
import os
from typing import Callable, List, Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# for this module
from crawl4ai import CrawlerMonitor, DisplayMode, RateLimiter
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

from client.ResponseGetData import ResponseGetDataCrawler
from client.MafiaError import MafiaError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CrawlerRouteError(MafiaError):
    """
    Custom exception for crawler route errors.
    Inherits from MafiaError for consistent error handling.

    Args:
        message (str, optional): Error message description
        exception (Exception, optional): Original exception that was caught
    """

    def __init__(
        self, message: Optional[str] = None, exception: Optional[Exception] = None
    ):
        super().__init__(message=message, exception=exception)


def create_default_browser_config() -> BrowserConfig:
    """
    Creates a default browser configuration with recommended settings.

    Returns:
        BrowserConfig: Configured browser settings object
    """
    browser = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )

    return browser


def create_default_crawler_config() -> CrawlerRunConfig:
    """
    Creates a default crawler configuration with recommended settings.

    Returns:
        CrawlerRunConfig: Configured crawler settings object
    """
    return CrawlerRunConfig(cache_mode=CacheMode.BYPASS)


def generate_async_dispatcher() -> MemoryAdaptiveDispatcher:
    rate_limiter = RateLimiter(
        base_delay=(2.0, 4.0),  # Random delay between 2-4 seconds
        max_delay=30.0,  # Cap delay at 30 seconds
        max_retries=5,  # Retry up to 5 times on rate-limiting errors
        rate_limit_codes=[429, 503],  # Handle these HTTP status codes
    )

    return MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=10,
        rate_limiter=rate_limiter,
    )


def log_progress(logs: dict, session_id: str, page_count: int):
    """
    Logs progress periodically and writes logs to a file.

    Args:
        logs (dict): Dictionary containing crawl logs.
        session_id (str): Unique session identifier.
        page_count (int): Number of pages crawled so far.
    """
    msg = f"Crawled {page_count} pages so far..."
    logger.info(msg)

    if not os.path.exists("LOGS"):
        os.makedirs("LOGS")

    with open(f"LOGS/crawl_progress_{session_id}.log", "w") as f:
        f.write(json.dumps(logs, indent=4))


def log_summary(results: list):
    """
    Logs the summary of the crawl operation.

    Args:
        results (list): List of successfully crawled pages.
    """
    msg = f"Crawl completed successfully with {len(results)} pages crawled"
    logger.info(msg)


async def crawl_url(
    url: str,
    session_id: str = None,
    browser_config: Optional[BrowserConfig] = None,
    crawler_config: Optional[CrawlerRunConfig] = None,
    storage_fn: Optional[Callable] = None,
    process_fn: Optional[Callable] = None,
    timeout: int = 15,
    logs=None,
    is_recrawl=False,
) -> ResponseGetDataCrawler:
    """
    Scrapes a single URL and processes the result.
    """
    logs = logs or {"success": [], "failed": []}

    if url in logs["success"] and not is_recrawl:
        if url in logs["failed"]:
            logs["failed"].remove(url)
        return "no need to recrawl, already successful"  # Skip if already successful and not a recrawl

    # Use provided config or create default
    browser_config = browser_config or create_default_browser_config()
    crawler_config = crawler_config or create_default_crawler_config()

    msg = f"Scraping URL: {url} with session ID: {session_id}"
    logger.info(msg)

    # Check if crawl4ai is available before attempting to use it

    # Create a new crawler instance using the context manager pattern
    # This ensures proper cleanup of browser resources after crawling
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Execute the crawling operation

        res = await crawler.arun(
            url=url,
            config=crawler_config,
            session_id=session_id,  # Session ID for potential caching/resuming
            timeout=timeout,  # Maximum time to wait for page load
        )

        # Check if the crawl was successful
        # Different errors can occur: network issues, timeouts, invalid URLs
        rgd = ResponseGetDataCrawler.from_res(res)

        if not rgd.is_success:
            if url not in logs["failed"]:
                logs["failed"].append(url)

            return rgd

        # Execute optional callback functions if provided
        # storage_fn: typically saves results to database or filesystem
        if storage_fn:
            storage_fn(rgd=rgd)

        # process_fn: typically transforms or extracts data from results
        if process_fn:
            await process_fn(rgd)

        # Return the standardized response

        if url in logs["failed"]:
            logs["failed"].remove(url)

        if url not in logs["success"]:
            logs["success"].append(url)
        return rgd


async def crawl_urls(
    starting_url: str,
    session_id: str,
    crawler_config: Optional[CrawlerRunConfig] = None,
    browser_config: Optional[BrowserConfig] = None,
    storage_fn: Optional[Callable] = None,
    process_fn: Optional[Callable] = None,
    delay_before_return_html: int = 3,
    logs=None,
    is_recrawl: bool = False,
) -> List[ResponseGetDataCrawler]:
    """
    Crawls multiple URLs starting from an initial URL.

    """
    logs = logs or {"success": [], "failed": []}

    # Use provided config or create default
    browser_config = browser_config or create_default_browser_config()
    crawler_config = crawler_config or create_default_crawler_config()

    msg = f"Starting crawl from URL: {starting_url} with session ID: {session_id}"
    logger.info(msg)

    results = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        msg = f"Initializing multi-page crawl from {starting_url}"
        logger.debug(msg)

        page_count = 0

        async for res in await crawler.arun(
            url=starting_url,  # Start crawling from the initial URL
            # dispatche=dispatcher,  # Use the adaptive dispatcher for rate limiting and memory management
            config=crawler_config,
            magic=True,  # Enable magic mode for automatic content extraction
            delay_before_return_html=delay_before_return_html,  # Wait time for dynamic content loading
            session_id=session_id,  # For tracking and resuming crawls
        ):

            page_count += 1
            current_url = getattr(res, "url", "unknown")

            msg = f"Processing crawl result #{page_count} for URL: {current_url}"
            logger.debug(msg)
            rgd = ResponseGetDataCrawler.from_res(res)

            if not rgd.is_success:
                if current_url not in logs["failed"]:
                    logs["failed"].append(current_url)

                log_progress(logs, session_id=session_id, page_count=page_count)
                continue

            if current_url in logs["success"] and not is_recrawl:
                # Skip if already successful and not a recrawl
                continue

            if storage_fn:
                storage_fn(rgd=rgd)

            if process_fn:
                await process_fn(rgd=rgd)

            results.append(rgd)
            logs["success"].append(current_url)

            if current_url in logs["failed"]:
                logs["failed"].remove(current_url)

            # Log progress periodically
            if page_count % 10 == 0:
                log_progress(logs, session_id, page_count)

        log_progress(logs, session_id, page_count)
        log_summary(results)
    return results
