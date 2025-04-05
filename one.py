import routes.crawler as crawler_routes
import routes.supabase as supabase_routes
import implementation.scraper as scraper
import utils.convert as utcv
import json
import argparse

# Standard library imports
import os
import logging
from typing import List
from functools import partial
from supabase import AsyncClient as AsyncSupabaseClient
from openai import AsyncClient as AsyncOpenaiClient
from routes.crawler import DefaultMarkdownGenerator

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


wait_condition = """() => {
  return document.querySelector(".section-list-item, .article-list-item");
}"""

prune_filter = crawler_routes.PruningContentFilter(
    threshold=0.5,
    threshold_type="dynamic",  # or "static"
    # min_length=100,  # Minimum length of text to keep
    # min_word_threshold=50  # or "dynamic"
)

md_generator = crawler_routes.DefaultMarkdownGenerator(
    content_filter=prune_filter, options={"ignore_links": True}
)

crawler_config = crawler_routes.CrawlerRunConfig(
    wait_for=wait_condition,
    markdown_generator=md_generator,
)


async def main(
    url: str,
    export_folder: str,
    source: str,
):
    """Main function to crawl URLs and process the results."""

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

    return await crawler_routes.crawl_url(
        crawler_config=crawler_config,
        url=url,
        session_id=source,
        storage_fn=storage_fn,
        process_fn=process_fn,
    )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Crawl a website and process the results."
    )
    parser.add_argument(
        "--url", type=str, required=True, help="The URL for the crawler."
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="The source identifier for the session.",
    )
    parser.add_argument(
        "--export-folder",
        type=str,
        default="EXPORT/",
        help="Folder to export the results.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    import asyncio

    args = parse_arguments()

    print(args)

    asyncio.run(
        main(
            url=args.url,
            export_folder=args.export_folder,
            source=args.source,
        )
    )
