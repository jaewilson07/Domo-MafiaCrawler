"""
Web Crawler Routes Module

This module provides route handlers for web crawling functionality using crawl4ai.
It includes functions for scraping individual URLs and crawling multiple connected URLs.

The module handles all web crawling operations with proper error handling and 
standardized response formatting via ResponseGetDataCrawler objects.
"""

# Standard library imports
import logging
import asyncio
import argparse
import sys
import os
from typing import Callable, List, Optional, Any, Union

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
    from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    print(
        "Warning: crawl4ai module not available. Some functionality will be limited."
    )

# Configure path for client imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from client.ResponseGetData import ResponseGetDataCrawler
    from client.MafiaError import MafiaError
    CLIENT_MODULES_AVAILABLE = True
except ImportError:
    CLIENT_MODULES_AVAILABLE = False
    print("Warning: client modules not available. Using basic error handling.")

    # Define fallback classes
    class MafiaError(Exception):

        def __init__(self, message=None, exception=None):
            super().__init__(message)
            self.original_exception = exception

    class ResponseGetDataCrawler:

        @classmethod
        def from_res(cls, res):
            return {"success": getattr(res, "success", False), "data": res}


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

    def __init__(self,
                 message: Optional[str] = None,
                 exception: Optional[Exception] = None):
        super().__init__(message=message, exception=exception)


def create_default_browser_config() -> BrowserConfig:
    """
    Creates a default browser configuration with recommended settings.
    
    Returns:
        BrowserConfig: Configured browser settings object
    """
    return BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True,
        extra_args=[
            "--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"
        ],
    )


def create_default_crawler_config() -> CrawlerRunConfig:
    """
    Creates a default crawler configuration with recommended settings.
    
    Returns:
        CrawlerRunConfig: Configured crawler settings object
    """
    return CrawlerRunConfig(cache_mode=CacheMode.BYPASS,
                            max_pages=10,
                            same_domain=True)


async def scrape_url(url: str,
                     session_id: str,
                     browser_config: Optional[BrowserConfig] = None,
                     crawler_config: Optional[CrawlerRunConfig] = None,
                     storage_fn: Optional[Callable] = None,
                     process_fn: Optional[Callable] = None,
                     timeout: int = 15) -> ResponseGetDataCrawler:
    """
    Scrapes a single URL and processes the result.
    
    Args:
        url (str): The URL to scrape
        session_id (str): Unique session identifier
        browser_config (BrowserConfig, optional): Browser configuration
        crawler_config (CrawlerRunConfig, optional): Crawler configuration
        storage_fn (Callable, optional): Function to store crawl results
        process_fn (Callable, optional): Function to process crawl results
        timeout (int, optional): Request timeout in seconds
        
    Returns:
        ResponseGetDataCrawler: Standardized response with crawl results
        
    Raises:
        CrawlerRouteError: If crawling fails or returns unsuccessful results
    """
    # Use provided config or create default
    browser_config = browser_config or create_default_browser_config()
    crawler_config = crawler_config or create_default_crawler_config()

    logger.info(f"Scraping URL: {url} with session ID: {session_id}")

    # Check if crawl4ai is available before attempting to use it

    try:
        # Create a new crawler instance using the context manager pattern
        # This ensures proper cleanup of browser resources after crawling
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Execute the crawling operation
            logger.debug(f"Starting crawl operation for {url}")
            res = await crawler.arun(
                url=url,
                config=crawler_config,
                session_id=
                session_id,  # Session ID for potential caching/resuming
                timeout=timeout,  # Maximum time to wait for page load
            )

            # Check if the crawl was successful
            # Different errors can occur: network issues, timeouts, invalid URLs
            if not res.success:
                error_message = getattr(res, 'error_message', 'Unknown error')
                logger.error(f"Failed to crawl {url}: {error_message}")
                raise CrawlerRouteError(
                    message=f"Error crawling {url} - {error_message}")

            logger.info(f"Successfully crawled {url}")

            # Convert raw crawl results to our standardized format
            # This provides a consistent interface regardless of crawler implementation
            rgd = ResponseGetDataCrawler.from_res(res)

            # Execute optional callback functions if provided
            # storage_fn: typically saves results to database or filesystem
            if storage_fn:
                logger.debug(f"Storing results for {url}")
                try:
                    storage_fn(rgd=rgd)
                except Exception as e:
                    # Log storage errors but don't fail the entire operation
                    logger.warning(f"Error in storage callback: {str(e)}")

            # process_fn: typically transforms or extracts data from results
            if process_fn:
                logger.debug(f"Processing results for {url}")
                try:
                    process_fn(rgd)
                except Exception as e:
                    # Log processing errors but don't fail the entire operation
                    logger.warning(f"Error in process callback: {str(e)}")

            # Return the standardized response
            return rgd

    except NotImplementedError as e:
        logger.error(f"Crawler implementation error: {str(e)}")
        raise CrawlerRouteError(
            message=
            "Crawler dependencies not installed correctly. Have you run create4ai-create and create4ai-doctor?",
            exception=e)
    except Exception as e:
        logger.error(f"Unexpected error while crawling {url}: {str(e)}")
        raise CrawlerRouteError(exception=e) from e


async def crawl_urls(
    starting_url: str,
    session_id: str,
    output_folder: str,
    crawler_config: Optional[CrawlerRunConfig] = None,
    browser_config: Optional[BrowserConfig] = None,
    storage_fn: Optional[Callable] = None,
    process_fn: Optional[Callable] = None,
    delay_before_return_html: int = 3,
) -> List[ResponseGetDataCrawler]:
    """
    Crawls multiple URLs starting from an initial URL.
    
    Args:
        starting_url (str): The initial URL to start crawling from
        session_id (str): Unique session identifier
        output_folder (str): Folder to store crawling results
        crawler_config (CrawlerRunConfig, optional): Crawler configuration
        browser_config (BrowserConfig, optional): Browser configuration
        storage_fn (Callable, optional): Function to store crawl results
        process_fn (Callable, optional): Function to process crawl results
        delay_before_return_html (int, optional): Delay before extracting HTML in seconds
        
    Returns:
        List[ResponseGetDataCrawler]: List of standardized responses with crawl results
        
    Raises:
        CrawlerRouteError: If crawling fails or encounters errors
    """
    # Use provided config or create default
    browser_config = browser_config or create_default_browser_config()
    crawler_config = crawler_config or create_default_crawler_config()

    logger.info(
        f"Starting crawl from URL: {starting_url} with session ID: {session_id}"
    )
    logger.info(f"Output folder: {output_folder}")

    try:
        # Initialize results list to store all crawled pages
        results = []

        # Create a new crawler instance using the context manager pattern
        # This ensures proper cleanup of browser resources after crawling
        async with AsyncWebCrawler(config=browser_config) as crawler:
            logger.debug(f"Initializing multi-page crawl from {starting_url}")

            # The crawler.arun() returns an async iterator that yields results as pages are crawled
            # We use "await" here because arun() is an async function that returns an async iterator
            crawl_iterator = await crawler.arun(
                starting_url,
                config=crawler_config,
                magic=True,  # Enable magic mode for automatic content extraction
                delay_before_return_html=
                delay_before_return_html,  # Wait time for dynamic content loading
                session_id=session_id,  # For tracking and resuming crawls
            )

            # Now we iterate through the results as they come in
            # The "async for" loop will process each result as it becomes available
            page_count = 0
            async for res in crawl_iterator:
                page_count += 1
                current_url = getattr(res, 'url', 'unknown')
                logger.debug(
                    f"Processing crawl result #{page_count} for URL: {current_url}"
                )

                # Convert the raw crawl result to our standardized format
                # This provides a consistent interface for all downstream processing
                rgd = ResponseGetDataCrawler.from_res(res)

                # Execute the storage callback if provided
                # This typically saves results to a database or file system
                if storage_fn:
                    logger.debug(f"Storing results for {rgd.url}")
                    try:
                        storage_fn(rgd)
                    except Exception as e:
                        # Log storage errors but continue processing
                        logger.warning(
                            f"Error in storage callback for {rgd.url}: {str(e)}"
                        )

                # Execute the process callback if provided
                # This allows for custom processing of each crawled page
                if process_fn:
                    logger.debug(f"Processing results for {rgd.url}")
                    try:
                        # Note that process_fn might be async, so we await it
                        await process_fn(rgd=rgd)
                    except Exception as e:
                        # Log processing errors but continue crawling
                        logger.warning(
                            f"Error in process callback for {rgd.url}: {str(e)}"
                        )

                # Add the result to our collection
                results.append(rgd)

                # Log progress periodically
                if page_count % 10 == 0:
                    logger.info(f"Crawled {page_count} pages so far...")

        # Log completion summary
        logger.info(
            f"Crawl completed successfully with {len(results)} pages crawled")
        return results

    except NotImplementedError as e:
        logger.error(f"Crawler implementation error: {str(e)}")
        raise CrawlerRouteError(
            message=
            "Crawler dependencies not installed correctly. Have you run create4ai-create and create4ai-doctor?",
            exception=e)
    except Exception as e:
        logger.error(f"Unexpected error during crawl: {str(e)}")
        raise CrawlerRouteError(exception=e) from e


async def main(url,
               output_dir=None,
               max_pages=10,
               session_id=None,
               verbose=False):
    """
    Main entry point for command-line usage.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if session_id is None:
        import uuid
        session_id = str(uuid.uuid4())

    if output_dir is None:
        output_dir = './export/crawler_output'
        os.makedirs(output_dir, exist_ok=True)

    # Create configs
    browser_config = create_default_browser_config()
    crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS,
                                      max_pages=max_pages,
                                      same_domain=True,
                                      stream=True)

    try:
        if CRAWL4AI_AVAILABLE:
            print(f"Starting crawler for URL: {url}")
            print(f"Output directory: {output_dir}")
            print(f"Session ID: {session_id}")
            print(f"Max pages: {max_pages}")

            # Define storage function
            def save_to_disk(result):
                try:
                    filename = os.path.join(
                        output_dir,
                        f"{session_id}_{result.url.replace('://', '_').replace('/', '_')}.txt"
                    )
                    with open(filename, 'w') as f:
                        html_content = getattr(result, 'html',
                                               'No HTML content available')
                        f.write(f"URL: {result.url}\n\n")
                        f.write(html_content)
                    print(f"Saved content to {filename}")
                except Exception as e:
                    print(f"Error saving content: {str(e)}")

            # Start crawling
            results = await crawl_urls(starting_url=url,
                                       session_id=session_id,
                                       output_folder=output_dir,
                                       crawler_config=crawler_config,
                                       browser_config=browser_config,
                                       storage_fn=save_to_disk,
                                       delay_before_return_html=3)

            print(f"Crawling completed. Downloaded {len(results)} pages.")
            return results
        else:
            print(
                "Error: crawl4ai module is not available. Please install it with 'pip install crawl4ai'."
            )
            return None
    except Exception as e:
        print(f"Error during crawling: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Crawler CLI")
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument("-o",
                        "--output",
                        help="Output directory for crawled content")
    parser.add_argument("-m",
                        "--max-pages",
                        type=int,
                        default=10,
                        help="Maximum number of pages to crawl")
    parser.add_argument("-s", "--session-id", help="Session ID for the crawl")
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="Enable verbose output")

    args = parser.parse_args()

    if not args.url.startswith(('http://', 'https://')):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)

    asyncio.run(
        main(url=args.url,
             output_dir=args.output,
             max_pages=args.max_pages,
             session_id=args.session_id,
             verbose=args.verbose))
