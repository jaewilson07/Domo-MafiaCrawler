import routes.crawler as crawler_routes
import routes.supabase as supabase_routes
import implementation.scraper as scraper
import utils.convert as utcv
import json

# Standard library imports
import os
import logging
from typing import List
from functools import partial
from supabase import AsyncClient as AsyncSupabaseClient
from openai import AsyncClient as AsyncOpenaiClient

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Configure the crawler

browser_config = crawler_routes.BrowserConfig(
    browser_type="chromium",
    headless=True,
    verbose=True,
    extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
)

supabase_client = AsyncSupabaseClient(
    os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
)

async_openai_client = AsyncOpenaiClient(api_key=os.environ["OPENAI_API_KEY"])


async def main(
    starting_url: str,
    allowed_domains: List[str],
    export_folder: str,
    source: str,
    debug_prn: bool = False,
):
    """Main function to crawl URLs and process the results."""

    allowed_domains = allowed_domains or [utcv.extract_domain(starting_url)]

    domain_filter = crawler_routes.DomainFilter(allowed_domains=allowed_domains)

    config = crawler_routes.CrawlerRunConfig(
        magic=True,
        cache_mode=crawler_routes.CacheMode.BYPASS,
        deep_crawl_strategy=crawler_routes.BFSDeepCrawlStrategy(
            max_depth=20,
            filter_chain=crawler_routes.FilterChain([domain_filter]),
            include_external=False,
        ),
        stream=True,
        verbose=False,
        session_id=source,
    )

    storage_fn = partial(
        supabase_routes.save_chunk_to_disk, export_folder=export_folder
    )

    process_fn = partial(
        scraper.process_rgd,
        export_folder=export_folder,
        supabase_client=supabase_client,
        async_embedding_client=async_openai_client,
        async_openai_client=async_openai_client,
    )
    # Crawl URLs
    with open("LOGS/crawl_progress_mermaid_js_docs.log", "r") as f:
        logs = json.loads(f.read())

    await crawler_routes.crawl_urls(
        logs=logs,
        starting_url=starting_url,
        crawler_config=config,
        browser_config=browser_config,
        session_id=source,
        storage_fn=storage_fn,
        process_fn=process_fn,
    )

    # if logs.get("failed"):
    #     crawler_routes.crawl_url(
    #         logs=logs,
    #         crawler_config=config,
    #         browser_config=browser_config,
    #         session_id=source,
    #         storage_fn=storage_fn,
    #         process_fn=process_fn,
    #     )

    # if debug_prn:
    #     logger.info("Completed crawling with results: %s", res)

    # return res


if __name__ == "__main__":
    import asyncio

    STARTING_URL = "https://mermaid.js.org/"
    ALLOWED_DOMAINS = ["mermaid.js.org", "mermaid-js.github.io"]
    EXPORT_FOLDER = "EXPORT/"
    SOURCE = "mermaid_js_docs"

    asyncio.run(
        main(
            starting_url=STARTING_URL,
            allowed_domains=ALLOWED_DOMAINS,
            export_folder=EXPORT_FOLDER,
            source=SOURCE,
            debug_prn=False,
        )
    )
