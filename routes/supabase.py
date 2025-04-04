# Standard library imports
import json
import logging
import datetime as dt
from typing import List, Dict, Callable, Optional, Any, Union

from supabase import AsyncClient as AsyncSupabaseClient

# Local application imports
from client.MafiaError import MafiaError
from client.ResponseGetData import ResponseGetDataSupabase

from utils.files import upsert_folder
from utils.convert import convert_url_to_file_name, sanitize_frontmatter_value

logger = logging.getLogger(__name__)


class SupabaseError(MafiaError):

    def __init__(
        self, message: Optional[str] = None, exception: Optional[Exception] = None
    ):

        super().__init__(message=message, exception=exception)


async def store_data_in_supabase_table(
    async_supabase_client: AsyncSupabaseClient,
    table_name: str,
    data: Dict[str, Any],
    on_conflict: str = "url, chunk_number",
) -> ResponseGetDataSupabase:
    """
    Store data in a Supabase table using upsert operation.

    Args:
        async_supabase_client: Initialized Supabase client
        table_name: Name of the table to store data in
        data: Data dictionary to store
        on_conflict: Comma-separated column names to check for conflicts

    Returns:
        ResponseGetDataSupabase: Standardized response object

    Raises:
        SupabaseError: If the data cannot be stored
    """

    try:
        logger.debug("Storing data in table %s", table_name)

        # Ensure async operation is awaited properly
        res = await (
            async_supabase_client.table(table_name)
            .upsert(data, on_conflict=on_conflict)
            .execute()
        )

        # Convert result to standardized response format
        response = ResponseGetDataSupabase.from_res(res=res)

        # Check for success
        if not response.is_success:
            error_msg = f"Failed to store data in {table_name} : {response.response}"
            logger.error(error_msg)
            raise SupabaseError(error_msg)

        msg = f"Successfully stored data in {table_name}"
        logger.info(msg)
        return response

    except Exception as e:
        error_msg = f"Error storing data in Supabase table {table_name} : {str(e)}"
        logger.error(error_msg)
        raise SupabaseError(error_msg, exception=e) from e


async def get_document_urls_from_supabase(
    async_supabase_client: AsyncSupabaseClient,
    source: Optional[str] = None,
    table_name: str = "site_pages",
) -> List[str]:
    """
    Retrieve a list of available document URLs from Supabase.

    Args:
        async_supabase_client: Initialized Supabase client
        source: Optional metadata source filter
        table_name: Name of the table to query

    Returns:
        List of unique document URLs

    Raises:
        SupabaseError: If URLs cannot be retrieved
    """

    try:
        msg = f"Retrieving document URLs from {table_name}" + (
            f" with source '{source}'" if source else ""
        )
        logger.debug(msg)

        # Ensure async operation is awaited properly
        if source:
            result = await (
                async_supabase_client.table(table_name)
                .select("url")
                .eq("metadata->>source", source)
                .execute()
            )
        else:
            result = await (
                async_supabase_client.table(table_name).select("url").execute()
            )

        # Handle empty results
        if not result.data:
            logger.info("No document URLs found")
            return []

        # Extract and deduplicate URLs
        urls = sorted(set(doc["url"] for doc in result.data))
        msg = f"Retrieved {len(urls)} unique document URLs"
        logger.info(msg)
        return urls

    except Exception as e:
        error_msg = f"Error retrieving document URLs : {str(e)}"
        logger.error(error_msg)
        raise SupabaseError(error_msg, exception=e) from e


def format_supabase_chunks(data: List[Dict[str, Any]]) -> List[str]:

    if not data:
        logger.warning("Empty data provided to format_supabase_chunks")
        return []

    try:
        return [
            f"# {doc.get('title', 'Untitled')}\n\n{doc.get('content', '')}"
            for doc in data
            if doc
        ]
    except Exception as e:
        logger.error(f"Error formatting chunks: {str(e)}")
        return [str(doc) for doc in data if doc]


def format_supabase_chunks_into_pages(data: List[dict]) -> str:
    """
    Format multiple Supabase chunks into a single page.

    This function combines multiple chunks from a document into a coherent page.
    It extracts the title from the first chunk and then concatenates all content,
    preserving the order based on chunk_number if available.

    Args:
        data: List of chunk data from Supabase, each containing at least 'title' and 'content'

    Returns:
        Combined page content as a markdown string with title and all chunk contents

    Raises:
        IndexError: If data list is empty and title extraction is attempted

    Example:
        ```python
        chunks = [
            {"title": "Introduction - Document", "content": "This is the first part..."},
            {"title": "Chapter 1 - Document", "content": "This is the second part..."}
        ]
        formatted = format_supabase_chunks_into_pages(chunks)
        # Result: "# Introduction\n\nThis is the first part...\n\nThis is the second part..."
        ```
    """
    if not data:
        logger.warning("Empty data provided to format_supabase_chunks_into_pages")
        return ""

    try:
        # Extract page title from first chunk
        page_title = data[0].get("title", "Untitled")
        if " - " in page_title:
            page_title = page_title.split(" - ")[0]

        # Format content with title and content from all chunks
        formatted_content = [f"# {page_title}\n"]
        for chunk in data:
            content = chunk.get("content", "")
            if content:
                formatted_content.append(content)

        return "\n\n".join(formatted_content)
    except Exception as e:
        logger.error(f"Error formatting page: {str(e)}")
        return "\n\n".join([chunk.get("content", "") for chunk in data if chunk])


async def get_document_from_supabase(
    async_supabase_client: AsyncSupabaseClient,
    url: str,
    table_name: str = "site_pages",
    source: Optional[str] = None,
    format_fn: Optional[Callable] = None,
) -> Union[List[dict], None]:
    """
    Retrieve a document from Supabase by URL.

    Args:
        async_supabase_client: Initialized Supabase client
        url: URL of the document to retrieve
        table_name: Name of the table to query
        source: Optional metadata source filter
        format_fn: Optional function to format the results

    Returns:
        Document data, either raw or formatted based on format_fn

    Raises:
        SupabaseError: If document cannot be retrieved
    """
    try:
        logger.debug(f"Retrieving document from {table_name} with URL: {url}")

        # Ensure async operation is awaited properly
        query = (
            async_supabase_client.from_(table_name)
            .select("title, content, chunk_number")
            .eq("url", url)
        )

        # Add source filter if provided
        if source:
            query = query.eq("metadata->>source", source)

        result = await query.order("chunk_number").execute()

        # Process results
        data = result.data or []
        logger.info(f"Retrieved {len(data)} chunks for document {url}")

        # Return raw or formatted data
        if not format_fn:
            return data

        # Apply formatter and return
        return format_fn(data)

    except Exception as e:
        error_msg = f"Error retrieving document for URL: {url}"
        logger.error(f"{error_msg}: {str(e)}")
        raise SupabaseError(error_msg, exception=e)


async def get_chunks_from_supabase(
    async_supabase_client: AsyncSupabaseClient,
    query_embedding: List[float],
    table_name: str = "site_pages",
    match_count: int = 5,
    source: Optional[str] = None,
    format_fn: Optional[Callable] = None,
) -> Union[List[dict], str]:
    """
    Retrieve chunks from Supabase using vector similarity search.

    Args:
        async_supabase_client: Initialized Supabase client
        query_embedding: Vector embedding for similarity search
        table_name: Name of the table to query
        match_count: Maximum number of matches to return
        source: Optional metadata source filter
        format_fn: Optional function to format the results

    Returns:
        Chunks data, either raw or formatted based on format_fn

    Raises:
        SupabaseError: If chunks cannot be retrieved
    """
    try:
        logger.debug(f"Retrieving chunks from {table_name} using vector search")

        filter_params = {}
        if source:
            filter_params["source"] = source

        # Ensure async operation is awaited properly
        result = await async_supabase_client.rpc(
            f"match_{table_name}",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "filter": filter_params,
            },
        ).execute()

        # Process results
        data = result.data or []
        logger.info(f"Retrieved {len(data)} chunks for vector similarity search")

        # Return raw or formatted data
        if not format_fn:
            return data

        # Apply formatter and return
        return format_fn(data)

    except Exception as e:
        error_msg = "Error retrieving chunks from vector similarity search"
        logger.error(f"{error_msg}: {str(e)}")
        raise SupabaseError(error_msg, exception=e)


def build_frontmatter(data: Dict[str, Any]) -> List[str]:
    fm = [
        "---",
        f"url: {sanitize_frontmatter_value(data.get('url'))}",
        f"session_id: {sanitize_frontmatter_value(data.get('source'))}",
    ]

    if data.get("chunk_number"):
        fm.append(
            f"chunk_number: {sanitize_frontmatter_value(data.get('chunk_number'))}"
        )

    if data.get("title"):
        fm.append(f"title: {sanitize_frontmatter_value(data.get('title'))}")

    if data.get("summary"):
        fm.append(f"summary: {sanitize_frontmatter_value(data.get('summary'))}")

    if data.get("embedding"):
        fm.append(f"embedding: {sanitize_frontmatter_value(data.get('embedding'))}")

    if data.get("metadata"):
        fm.append(f"metadata: {sanitize_frontmatter_value(data.get('metadata'))}")

    fm.append(f"updated_dt: {dt.datetime.now().isoformat()}")
    fm.append("---")

    return [line for line in fm if line is not None]


def save_chunk_to_disk(
    rgd: ResponseGetDataSupabase = None,
    data: Dict[str, Any] = None,
    url: str = None,
    export_folder=None,
    output_path=None,
) -> bool:
    """
    Save a data chunk to disk as a markdown file with frontmatter.

    Args:
        rgd: ResponseGetDataSupabase object containing data.
        data: Dictionary containing chunk data.
        url: URL of the document.
        export_folder: Folder to save the file.
        output_path: Specific file path to save the file.

    Returns:
        True if the file is saved successfully, False otherwise.
    """
    data = data or {}

    # Determine output path
    output_path = (
        output_path
        or f"{export_folder}/{convert_url_to_file_name(url or rgd and rgd.url)}.md"
    )

    # Ensure directory exists
    upsert_folder(output_path)

    # Extract required fields
    content = rgd and (rgd.markdown or rgd.html) or data.get("content")
    if isinstance(content, dict):
        content = json.dumps(content)
    if not content or content == "{}":
        content = " "

    # Build frontmatter
    frontmatter = build_frontmatter(
        {
            "url": rgd and rgd.url or data.get("url"),
            "source": rgd and rgd.source or data.get("source"),
            "chunk_number": data.get("chunk_number"),
            "title": data.get("title"),
            "summary": data.get("summary"),
            "embedding": data.get("embedding"),
            "metadata": data.get("metadata"),
        }
    )

    # Write to file
    try:
        with open(output_path, "w+", encoding="utf-8") as f:
            f.write("\n".join(frontmatter + [content]))
        logger.info(f"Successfully saved chunk to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving chunk to {output_path}: {e}")
        return False
