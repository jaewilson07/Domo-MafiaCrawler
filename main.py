import routes.crawler as crawler_routes
import routes.supabase as supabase_routes
import routes.openai as openai_routes
import implementation.scraper as scraper

# Standard library imports
import os
import logging
import asyncio
from typing import Optional
from functools import partial

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

supabase_client = supabase_routes.AsyncSupabaseClient(
    os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

async_openai_client = openai_routes.AsyncOpenaiClient(
    api_key=os.environ["OPENAI_API_KEY"])


async def main(debug_prn: bool = False):
    """Main function to crawl URLs and process the results."""
    export_folder = "./export/slack_apis/"
    source = "slack_api_docs"

    domain_filter = crawler_routes.DomainFilter(
        allowed_domains=["https://docs.slack.dev/admins/managing-users"])

    config = crawler_routes.CrawlerRunConfig(
        cache_mode=crawler_routes.CacheMode.BYPASS,
        deep_crawl_strategy=crawler_routes.BFSDeepCrawlStrategy(
            max_depth=1,
            filter_chain=crawler_routes.FilterChain([domain_filter]),
            include_external=False,
        ),
        stream=True,
        verbose=True,
        session_id=source)

    # Ensure the export folder exists
    os.makedirs(export_folder, exist_ok=True)

    # Crawl URLs
    res = await crawler_routes.crawl_urls(
        starting_url="https://docs.slack.dev/admins/managing-users",
        crawler_config=config,
        browser_config=browser_config,
        session_id=source,
        storage_fn=partial(supabase_routes.save_chunk_to_disk,
                           export_folder=export_folder),
        process_fn=partial(
            scraper.process_rgd,
            export_folder=export_folder,
            supabase_client=supabase_client,
            async_embedding_client=async_openai_client,
            async_openai_client=async_openai_client,
        ),
        output_folder=export_folder,
    )

    if debug_prn:
        logger.info(f"Completed crawling with results: {res}")

    return res


if __name__ == "__main__":
    """Run the main program directly."""
    asyncio.run(main(debug_prn=True))
