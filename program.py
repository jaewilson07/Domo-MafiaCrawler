import routes.crawler as crawler_routes
import routes.supabase as supabase_routes
import implementation.scraper as scraper

# Standard library imports
import os
import logging
from typing import Optional
from functools import partial
from crawl4ai import BrowserConfig

import asyncio

# Configure logging
logger = logging.getLogger(__name__)

domain_filter = crawler_routes.DomainFilter(allowed_domains=["docs.slack.dev"])

browser_config = crawler_routes.BrowserConfig(
    browser_type="chromium",
    headless=True,
    verbose=True,
    extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
)

config = crawler_routes.CrawlerRunConfig(
    cache_mode=crawler_routes.CacheMode.BYPASS,
    deep_crawl_strategy=crawler_routes.BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=crawler_routes.FilterChain([domain_filter]),
        include_external=False,
    ),
    stream=True,
    verbose=True,
)


async def main(debug_prn: bool = False):

    export_folder = "./export/slack_apis/"
    source = "slack_api_docs"

    res = await crawler_routes.crawl_urls(
        starting_url="https://docs.slack.dev/apis/",
        crawler_config=config,
        browser_config=browser_config,
        session_id=source,
        storage_fn=partial(supabase_routes.save_chunk_to_disk,
                           export_folder=export_folder),
        process_fn=partial(scraper.process_rgd),
        output_folder=export_folder,
    )

    return res


if __name__ == "__main__":
    asyncio.run(main())
