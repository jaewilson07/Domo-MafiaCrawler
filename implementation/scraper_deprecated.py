from client.MafiaError import MafiaError

from client.ResponseGetData import ResponseGetData
import utils.files as utfi
import utils.convert as utcv
import utils.chunking as utch
import utils.chunk_execution as utce

from routes import openai as openai_routes
from routes import crawler as crawler_routes
from routes import supabase as supabase_routes

# Standard library imports
import os
import logging
from dataclasses import dataclass, field
from typing import Union, List, Optional
from urllib.parse import urlparse
import datetime as dt
from functools import partial

# Set up logger
logger = logging.getLogger(__name__)


# Utility imports with robust error handling
async def read_url(
    url,
    source,
    doc_path,
    browser_config: crawler_routes.BrowserConfig,
    crawler_config: crawler_routes.CrawlerRunConfig = None,
    debug_prn: bool = False,
):
    if os.path.exists(doc_path):
        content, _ = utfi.read_md_from_disk(doc_path)

        if debug_prn:
            print(
                f"🛢️  {url} - scraping not required, file retrieved from - {doc_path}"
            )

        return content

    storage_fn = partial(
        supabase_routes.save_chunk_to_disk,
        output_path=doc_path,
    )

    res = await crawler_routes.scrape_url(url=url,
                                          session_id=source,
                                          browser_config=browser_config,
                                          crawler_config=crawler_config,
                                          storage_fn=storage_fn)
    if debug_prn:
        print(f"🛢️  {url} - page scraped to {doc_path}")

    return res.markdown


async def process_url(
    url: str,
    source: str,
    export_folder: str,
    database_table_name: str,
    async_supabase_client,
    async_openai_client,
    async_embedding_client,
    debug_prn: bool = False,
    browser_config: crawler_routes.BrowserConfig = None,
    crawler_config: crawler_routes.CrawlerRunConfig = None,
    is_replace_llm_metadata: bool = False,
    max_conccurent_requests=5,
):
    """
    Process a document URL and store chunks in parallel.

    Args:
        url (str): The URL to process
        source (str): The source identifier
        export_folder (str): The folder to export to
        database_table_name (str): The database table to store chunks in
        async_supabase_client: The Supabase client
        async_openai_client: The OpenAI client
        debug_prn (bool): Whether to print debug info
        browser_config: The browser configuration
        crawler_config: The crawler configuration
        is_replace_llm_metadata (bool): Whether to replace existing metadata
        max_conccurent_requests (int): Maximum number of concurrent requests

    Returns:
        list: The processed chunks, or False if error
    """
    # Use provided configs or defaults if available
    browser_config = browser_config or crawler_routes.create_default_browser_config(
    )

    # Create document path
    doc_path = f"{export_folder}/{utcv.convert_url_file_name(url)}.md"

    # Scrape URL and save results to doc_path
    try:
        if debug_prn:
            logger.info(f"Starting crawl: {url}")

        markdown = await read_url(
            url=url,
            source=source,
            browser_config=browser_config,
            doc_path=doc_path,
            debug_prn=debug_prn,
            crawler_config=crawler_config,
        )

    except Exception as e:
        error_msg = f"Error reading URL {url}: {str(e)}"
        logger.error(error_msg)
        return False

    if debug_prn:
        logger.info(f"Successfully crawled: {url}")

    # Chunk the text
    chunks = utch.chunk_text(markdown)

    if debug_prn:
        logger.info(f"Generated {len(chunks)} chunks to process from {url}")

    # Process chunks in parallel
    try:
        res = await utce.gather_with_concurrency(
            *[
                process_chunk(
                    url=url,
                    chunk=chunk,
                    chunk_number=idx,
                    source=source,
                    async_supabase_client=async_supabase_client,
                    async_openai_client=async_openai_client,
                    async_embedding_client=async_embedding_client,
                    database_table_name=database_table_name,
                    export_folder=export_folder,
                    debug_prn=debug_prn,
                    is_replace_llm_metadata=is_replace_llm_metadata,
                ) for idx, chunk in enumerate(chunks)
            ],
            n=max_conccurent_requests,
        )
    except Exception as e:
        error_msg = f"Error processing chunks from {url}: {str(e)}"
        logger.error(error_msg)
        return False

    if debug_prn:
        logger.info(f"Completed processing all chunks from {url}")

    return res


async def process_urls(
    urls: List[str],
    source: str,
    async_openai_client,
    async_embedding_client,
    async_supabase_client,
    export_folder: str = "./export",
    database_table_name: str = "site_pages",
    max_conccurent_requests: int = 5,
    debug_prn: bool = False,
    browser_config: crawler_routes.BrowserConfig = None,
    crawler_config: crawler_routes.CrawlerRunConfig = None,
    is_replace_llm_metadata: bool = False,
):
    """
    Process multiple URLs in parallel.

    Args:
        urls (List[str]): List of URLs to process
        source (str): The source identifier
        export_folder (str): The folder to export to
        database_table_name (str): The database table to store chunks in
        max_conccurent_requests (int): Maximum number of concurrent requests
        debug_prn (bool): Whether to print debug info
        browser_config: The browser configuration
        crawler_config: The crawler configuration
        is_replace_llm_metadata (bool): Whether to replace existing metadata
        async_openai_client: The OpenAI client
        async_supabase_client: The Supabase client

    Returns:
        list: The results of processing each URL
    """
    if not urls:
        logger.warning("No URLs found to crawl")
        return []

    # Filter out None values
    valid_urls = [url for url in urls if url]

    if not valid_urls:
        logger.warning("No valid URLs found to crawl")
        return []

        # Save URLs to file if utils.files is available
    urls_path = f"{export_folder}/urls/{source}.txt"
    try:
        utfi.upsert_folder(urls_path)

        with open(urls_path, "w+", encoding="utf-8") as f:
            f.write("\n".join(valid_urls))

        if debug_prn:
            logger.info(f"Saved {len(valid_urls)} URLs to {urls_path}")

    except Exception as e:
        error_msg = f"Error saving URLs to file: {str(e)}"
        logger.error(error_msg)

    # Process URLs in parallel or sequentially
    try:
        res = await utce.gather_with_concurrency(
            *[
                process_url(
                    url=url,
                    source=source,
                    debug_prn=debug_prn,
                    browser_config=browser_config,
                    export_folder=export_folder,
                    database_table_name=database_table_name,
                    is_replace_llm_metadata=is_replace_llm_metadata,
                    crawler_config=crawler_config,
                    async_openai_client=async_openai_client,
                    async_supabase_client=async_supabase_client,
                    async_embedding_client=async_embedding_client,
                ) for url in valid_urls
            ],
            n=max_conccurent_requests,
        )

    except Exception as e:
        error_msg = f"Error processing URLs: {str(e)}"
        logger.error(error_msg)
        return []

    if debug_prn:
        logger.info(f"Completed processing {len(valid_urls)} URLs")

    return res
