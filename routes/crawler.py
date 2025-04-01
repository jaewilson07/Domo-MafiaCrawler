
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter
from ..client.ResponseGetData import ResponseGetDataCrawler

import os
from typing import Callable
from agent_mafia.client import MafiaError as amme
from agent_mafia.utils import convert as amcv



class Crawler_Route_NotSuccess(amme.MafiaError):
    def __init__(self, message = None, exception = None):
        super().__init__(message = message, exception = exception)

# %% ../../nbs/routes/crawler.ipynb 7
async def scrape_url(
    url: str,
    session_id: str,
    browser_config: BrowserConfig = None,
    crawler_config: CrawlerRunConfig = None,
    storage_fn: Callable = None,
):

    browser_config = browser_config or default_browser_config

    res = None
    content = None

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            crawler_config = crawler_config or CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,

            )

            res = await crawler.arun(
                url=url,
                config=crawler_config,
                session_id=session_id,
                timeout=15,
            )

            print(res)

    except NotImplementedError as e:
        raise Crawler_Route_NotSuccess(
            message="have you run create4ai-create and create4ai-doctor? in terminal",
            exception=e,
        )

    except Exception as e:
        raise Crawler_Route_NotSuccess(
            exception=e,
        ) from e

    if not res.success:
        raise Crawler_Route_NotSuccess(
            message=f"error crawling {url} - {res.error_message}"
        )

    rgd = ResponseGetDataCrawler.from_res(res)

    if storage_fn:
        storage_fn(
            data={
                "content": rgd.markdown or rgd.response,
                "source": session_id,
                "url": res.url,
            }
        )

    return rgd

# %% ../../nbs/routes/crawler.ipynb 10
async def crawl_urls(
    starting_url: str,
    session_id: str,
    output_folder: str,
    crawler_config: CrawlerRunConfig = None,
    browser_config: BrowserConfig = None,
    storage_fn: Callable = None,
    process_fn: Callable = None,
    delay_before_return_html: int = 3,
):
    browser_config = browser_config or default_browser_config
    try:

        results = []
        async with AsyncWebCrawler(config=browser_config) as crawler:
            async for res in await crawler.arun(
                starting_url,
                config=crawler_config,
                # timeout=15,
                magic = True,
                delay_before_return_html=delay_before_return_html,
                session_id=session_id,
            ):

                rgd = ResponseGetDataCrawler.from_res(res)

                output_path=f"{os.path.join(
                    output_folder, amcv.convert_url_file_name(rgd.url))}.md"

                print(output_path)

                if storage_fn:
                    storage_fn(
                        output_path = output_path,
                        data={
                            "content": rgd.markdown or rgd.response,
                            "source": session_id,
                            "url": rgd.url,
                        },
                    )

                if process_fn:
                    await process_fn(
                            rgd=rgd,
                            export_folder=output_folder,
                            source=session_id
                        )

                results.append(rgd)

        return results

    except NotImplementedError as e:
        raise Crawler_Route_NotSuccess(
            message="have you run create4ai-create and create4ai-doctor? in terminal",
            exception=e,
        )

    except Exception as e:
        raise Crawler_Route_NotSuccess(
            exception=e,
        ) from e
