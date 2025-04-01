
async def process_chunk(
    url,
    chunk,
    chunk_number,
    source,
    async_supabase_client,
    database_table_name,
    export_folder,
    is_replace_llm_metadata: bool = False,
    debug_prn: bool = False,
):
    if debug_prn:
        print(f"🎬 starting {url} - {chunk_number}")

    chunk_path = (
        f"{export_folder}/chunks/{amcv.convert_url_file_name(url)}/{chunk_number}.md"
    )

    chunk = pc.Crawler_ProcessedChunk.from_chunk(
        chunk=chunk,
        chunk_number=chunk_number,
        url=url,
        source=source,
        output_path=chunk_path,
    )

    # try:
    await chunk.generate_metadata(
        output_path=chunk_path,
        is_replace_llm_metadata=is_replace_llm_metadata,
        debug_prn=debug_prn,
    )

    data = chunk.to_json()
    data.pop("source")

    await storage_routes.store_data_in_supabase_table(
        async_supabase_client=async_supabase_client,
        table_name=database_table_name,
        data=data,
    )

    if debug_prn:
        print(f"successfully processed {url}-{chunk_number}")

    return chunk

    # except Exception as e:
    #     print(
    #         utils.generate_error_message(
    #             f"💀 process_chunk - {url} - {chunk_number} -{e}", exception=e
    #         )
    #     )

# %% ../../nbs/implementations/scrape_urls.ipynb 5
async def read_url(
    url,
    source,
    browser_config: crawler_routes.BrowserConfig,
    doc_path,
    crawler_config: crawler_routes.CrawlerRunConfig = None,
    debug_prn: bool = False,
):
    if os.path.exists(doc_path):
        content, _ = amfi.read_md_from_disk(doc_path)

        if debug_prn:
            print(f"🛢️  {url} - scraping not required, file retrieved from - {doc_path}")

        return content

    storage_fn = partial(storage_routes.save_chunk_to_disk,
        output_path=doc_path,
        )

    res = await crawler_routes.scrape_url(
        url=url,
        session_id=source,
        browser_config=browser_config,
        crawler_config=crawler_config,
        storage_fn = storage_fn
    )
    if debug_prn:
        print(f"🛢️  {url} - page scraped to {doc_path}")

    return res.markdown

# %% ../../nbs/implementations/scrape_urls.ipynb 6
async def process_url(
    url: str,
    source: str,
    export_folder: str,
    database_table_name: str,
    async_supabase_client=None,
    debug_prn: bool = False,
    browser_config: crawler_routes.BrowserConfig = None,
    crawler_config: crawler_routes.CrawlerRunConfig = None,
    is_replace_llm_metadata: bool = False,
    max_conccurent_requests=5,
):
    """process a document and store chunks in parallel"""

    browser_config = browser_config or crawler_routes.default_browser_config
    async_supabase_client = async_supabase_client or storage_routes.async_supabase_client

    doc_path = f"{export_folder}/{amcv.convert_url_file_name(url)}.md"

    ## scrape url and save results to doc_path
    try:
        if debug_prn:
            print(f"starting crawl - {url}")

        markdown = await read_url(
            url=url,
            source=source,
            browser_config=browser_config,
            doc_path=doc_path,
            debug_prn=debug_prn,
            crawler_config=crawler_config,
        )

    except Exception as e:
        print(f"⛔  {url} - error while read_url - {e}")
        return False

    if debug_prn:
        print(f"☀️  successfully crawled: {url}")

    chunks = amcn.chunk_text(markdown)

    if debug_prn:
        print(f"☀️  : {len(chunks)} to process {url}")

    res = await amce.gather_with_concurrency(
        *[
            process_chunk(
                url=url,
                chunk=chunk,
                chunk_number=idx,
                source=source,
                async_supabase_client=async_supabase_client,
                database_table_name=database_table_name,
                export_folder=export_folder,
                debug_prn=debug_prn,
                is_replace_llm_metadata=is_replace_llm_metadata,
            )
            for idx, chunk in enumerate(chunks)
        ],
        n=max_conccurent_requests,
    )

    if debug_prn:
        print(f"☀️  done processing url {url}")

    return res

# %% ../../nbs/implementations/scrape_urls.ipynb 7
async def process_rgd(
    rgd,
    source : str, 
    export_folder: str,
    database_table_name: str = "site_pages",
    supabase_client=None,
    debug_prn: bool = False,
    is_replace_llm_metadata: bool = False,
    max_conccurent_requests=5,
):

    supabase_client = supabase_client or storage_routes.async_supabase_client

    ## scrape url and save results to doc_path
    if debug_prn:
        print(f"processing - {rgd.url}")

    chunks = amcn.chunk_text(rgd.markdown)

    if debug_prn:
        print(f"☀️  : {len(chunks)} to process {rgd.url}")

    res = await amce.gather_with_concurrency(
        *[
            process_chunk(
                url=rgd.url,
                chunk=chunk,
                chunk_number=idx,
                source=source,
                async_supabase_client=supabase_client,
                database_table_name=database_table_name,
                export_folder=export_folder,
                debug_prn=debug_prn,
                is_replace_llm_metadata=is_replace_llm_metadata,
            )
            for idx, chunk in enumerate(chunks)
        ],
        n=max_conccurent_requests,
    )

    if debug_prn:
        print(f"☀️  done processing url {rgd.url}")

    return res

# %% ../../nbs/implementations/scrape_urls.ipynb 8
async def process_urls(
    urls: List[str | None],
    source: str,
    export_folder: str = "./export",
    database_table_name: str = "site_pages",
    max_conccurent_requests: int = 5,
    debug_prn: bool = False,
    browser_config : crawler_routes.BrowserConfig =None,
    crawler_config : crawler_routes.CrawlerRunConfig = None,
    is_replace_llm_metadata: bool = False,
):
    if not urls:
        print("No URLs found to crawl")
        return

    urls_path = f"./export/urls/{source}.txt"

    amfi.upsert_folder(urls_path)

    with open(urls_path, "w+", encoding="utf-8") as f:
        f.write("\n".join(urls))

    res = await amce.gather_with_concurrency(
        *[
            process_url(
                url=url,
                source=source,
                debug_prn=debug_prn,
                browser_config=browser_config,
                export_folder=export_folder,
                database_table_name=database_table_name,
                is_replace_llm_metadata=is_replace_llm_metadata,
                crawler_config=crawler_config
            )
            for url in urls
        ],
        n=max_conccurent_requests,
    )

    print("done")
    return res
