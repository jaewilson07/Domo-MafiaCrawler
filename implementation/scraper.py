import utils.chunking as utch
import utils.convert as utcv
import utils.chunk_execution as utce

from routes import supabase as supabase_routes

from implementation.Crawler import Crawler_ProcessedChunk, CrawlerDependencies

# Standard library imports
import logging

# Set up logger
logger = logging.getLogger(__name__)


async def process_chunk(
    url,
    chunk,
    chunk_number,
    source,
    async_supabase_client,
    async_openai_client,
    async_embedding_client,
    database_table_name,
    export_folder,
    is_replace_llm_metadata: bool = False,
    debug_prn: bool = False,
):
    """
    Process a single chunk of content.

    Args:
        url (str): The URL the chunk is from
        chunk (str): The content of the chunk
        chunk_number (int): The chunk number
        source (str): The source identifier
        async_supabase_client: The Supabase client
        database_table_name (str): The database table to store the chunk in
        export_folder (str): The folder to export to
        is_replace_llm_metadata (bool): Whether to replace existing metadata
        debug_prn (bool): Whether to print debug info
        async_openai_client: The OpenAI client

    Returns:
        Crawler_ProcessedChunk: The processed chunk
    """
    if debug_prn:
        logger.info("Starting chunk processing: %s - %d", url, chunk_number)

    try:
        chunk_path = f"{export_folder}/chunks/{utcv.convert_url_to_file_name(url)}/{chunk_number}.md"

        print(chunk_path, type(chunk_path))

        dependencies = CrawlerDependencies(
            async_supabase_client=async_supabase_client,
            async_openai_client=async_openai_client,
            async_embedding_client=async_embedding_client,
        )

        chunk = Crawler_ProcessedChunk.from_chunk(
            content=chunk,
            chunk_number=chunk_number,
            url=url,
            source=source,
            output_path=chunk_path,
            dependencies=dependencies,
        )

        # Generate metadata
        await chunk.generate_metadata(
            output_path=chunk_path,
            is_replace_llm_metadata=is_replace_llm_metadata,
            debug_prn=debug_prn,
        )

        data = chunk.to_json()
        # Remove source as it might be duplicated elsewhere in the schema

        if "source" in data:
            data.pop("source")

        # try:
        await supabase_routes.store_data_in_supabase_table(
            async_supabase_client=async_supabase_client,
            table_name=database_table_name,
            data=data,
        )

        if debug_prn:
            logger.info("Stored chunk in database: %s-%d", url, chunk_number)

        # except Exception as db_error:
        #     error_msg = f"Error storing chunk in database: {str(db_error)}"
        #     logger.error(error_msg)
        #     chunk.error_logs.append(error_msg)

        if debug_prn:
            logger.info("Successfully processed chunk: %s-%d", url, chunk_number)

        return chunk

    except Exception as e:
        msg = f"💀 Error processing chunk {url}-{chunk_number}: {str(e)}"
        logger.error(msg)
        print(msg)
        raise e from e
        return None


async def process_rgd(
    rgd,
    export_folder: str,
    supabase_client,
    async_embedding_client,
    async_openai_client,
    database_table_name: str = "site_pages",
    debug_prn: bool = False,
    is_replace_llm_metadata: bool = False,
    max_conccurent_requests=5,
):
    """
    Process a ResponseGetDataCrawler object.

    Args:
        rgd: The ResponseGetDataCrawler object
        source (str): The source identifier
        export_folder (str): The folder to export to
        database_table_name (str): The database table to store chunks in
        supabase_client: The Supabase client
        async_openai_client: The OpenAI client
        debug_prn (bool): Whether to print debug info
        is_replace_llm_metadata (bool): Whether to replace existing metadata
        max_conccurent_requests (int): Maximum number of concurrent requests

    Returns:
        list: The processed chunks
    """

    if debug_prn:
        logger.info("Processing ResponseGetDataCrawler for: %s", rgd.url)

    source = rgd.source
    url = rgd.url or "unknown-url"

    chunks = utch.chunk_text(rgd.markdown or rgd.response)

    if debug_prn:
        logger.info(
            "Generated %d chunks to process from ResponseGetDataCrawler", len(chunks)
        )

    res = await utce.gather_with_concurrency(
        *[
            process_chunk(
                url=url,
                chunk=chunk,
                chunk_number=idx,
                source=source,
                async_supabase_client=supabase_client,
                async_openai_client=async_openai_client,
                async_embedding_client=async_embedding_client,
                database_table_name=database_table_name,
                export_folder=export_folder,
                debug_prn=debug_prn,
                is_replace_llm_metadata=is_replace_llm_metadata,
            )
            for idx, chunk in enumerate(chunks)
        ],
        n=max_conccurent_requests,
    )

    # except Exception as e:
    #     error_msg = f"Error processing chunks from ResponseGetDataCrawler: {str(e)}"
    #     logger.error(error_msg)
    #     return []

    if debug_prn:
        logger.info("Completed processing ResponseGetDataCrawler")

    return res
