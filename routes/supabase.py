"""
Supabase Database Routes Module

This module provides route handlers for Supabase database operations.
It includes functions for storing, retrieving, and formatting data from Supabase tables.

The module handles all Supabase database operations with proper error handling and
standardized response formatting via ResponseGetDataSupabase objects. It's designed
to gracefully handle environments where the Supabase package is not available by
providing proper type hints and clear error messages.

## Core Functions:
- store_data_in_supabase_table: Store data in a Supabase table
- get_document_urls_from_supabase: Get all document URLs from a table
- get_document_from_supabase: Retrieve a document by URL
- get_chunks_from_supabase: Perform vector similarity search
- save_chunk_to_disk: Save a data chunk as a markdown file with frontmatter

## Formatting Functions:
- format_supabase_chunks: Format chunks as markdown strings
- format_supabase_chunks_into_pages: Format multiple chunks into a single page

## Type Handling:
This module uses type hints throughout to improve code completion and error checking.
Key types include:
- Async_SupabaseClient: The Supabase client type (real or mock for LSP)
- Document: Dict representing a document or chunk from Supabase
- DocumentList: List of Document objects
- SupabaseError: Custom exception for Supabase-related errors

## Usage Examples:
```python
# Store data example
await store_data_in_supabase_table(
    supabase_client, 
    "documents", 
    {"url": "https://example.com", "content": "Example content"}
)

# Retrieve document example
doc = await get_document_from_supabase(
    supabase_client, 
    "https://example.com",
    format_fn=format_supabase_chunks_into_pages
)

# Save to disk example
save_chunk_to_disk("output/example.md", document_data)
```

## Error Handling:
All functions in this module check for the availability of the Supabase package
and raise appropriate SupabaseError exceptions with clear error messages when
operations cannot be completed. This ensures consistent error handling throughout
the application.
"""

# Standard library imports
import json
import logging
import os
import datetime as dt
from typing import List, Dict, Callable, Optional, Any, Union, TypeVar, cast

from supabase import AsyncClient as AsyncSupabaseClient

# Local application imports
from client.MafiaError import MafiaError
from client.ResponseGetData import ResponseGetDataSupabase

from utils.files import upsert_folder
from utils.convert import convert_url_file_name

logger = logging.getLogger(__name__)


class SupabaseError(MafiaError):

    def __init__(self,
                 message: Optional[str] = None,
                 exception: Optional[Exception] = None):

        super().__init__(message=message, exception=exception)


async def store_data_in_supabase_table(
        async_supabase_client: AsyncSupabaseClient,
        table_name: str,
        data: Dict[str, Any],
        on_conflict: str = "url, chunk_number") -> ResponseGetDataSupabase:
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
        logger.debug(f"Storing data in table {table_name}")

        # Execute upsert operation with provided data and conflict columns
        res = await async_supabase_client.table(table_name).upsert(
            data, on_conflict=on_conflict).execute()

        # Convert result to standardized response format
        response = ResponseGetDataSupabase.from_res(res=res)

        # Check for success
        if not response.is_success:
            error_msg = f"Failed to store data in {table_name}"
            logger.error(f"{error_msg}: {response.response}")
            raise SupabaseError(error_msg)

        logger.info(f"Successfully stored data in {table_name}")
        return response

    except Exception as e:
        error_msg = f"Error storing data in Supabase table {table_name}"
        logger.error(f"{error_msg}: {str(e)}")
        raise SupabaseError(error_msg, exception=e)


async def get_document_urls_from_supabase(
        async_supabase_client: AsyncSupabaseClient,
        source: Optional[str] = None,
        table_name: str = "site_pages") -> List[str]:
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
        logger.debug(f"Retrieving document URLs from {table_name}" +
                     (f" with source '{source}'" if source else ""))

        # Build query based on whether source filter is provided
        if source:
            result = await async_supabase_client.table(table_name).select(
                "url").eq("metadata->>source", source).execute()
        else:
            result = await async_supabase_client.table(table_name).select(
                "url").execute()

        # Handle empty results
        if not result.data:
            logger.info("No document URLs found")
            return []

        # Extract and deduplicate URLs
        urls = sorted(set(doc["url"] for doc in result.data))
        logger.info(f"Retrieved {len(urls)} unique document URLs")
        return urls

    except Exception as e:
        error_msg = "Error retrieving document URLs"
        logger.error(f"{error_msg}: {str(e)}")
        raise SupabaseError(error_msg, exception=e)


def format_supabase_chunks(data: List[Dict[str, Any]]) -> List[str]:
    """
    Format Supabase chunks into a list of markdown strings.
    
    This function takes a list of document chunks retrieved from Supabase
    and formats each chunk as a markdown string with a title and content.
    It's useful for displaying individual chunks separately.
    
    Args:
        data: List of chunk data from Supabase, each containing 'title' and 'content' fields
        
    Returns:
        List of formatted markdown strings, one for each chunk
        
    Example:
        ```python
        chunks = [
            {"title": "Introduction", "content": "This is the introduction."},
            {"title": "Chapter 1", "content": "This is chapter 1."}
        ]
        formatted = format_supabase_chunks(chunks)
        # Returns: ["# Introduction\n\nThis is the introduction.", "# Chapter 1\n\nThis is chapter 1."]
        ```
    """
    if not data:
        logger.warning("Empty data provided to format_supabase_chunks")
        return []

    try:
        return [
            f"# {doc.get('title', 'Untitled')}\n\n{doc.get('content', '')}"
            for doc in data if doc
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
        logger.warning(
            "Empty data provided to format_supabase_chunks_into_pages")
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
        return "\n\n".join(
            [chunk.get("content", "") for chunk in data if chunk])


async def get_document_from_supabase(
        async_supabase_client: AsyncSupabaseClient,
        url: str,
        table_name: str = "site_pages",
        source: Optional[str] = None,
        format_fn: Optional[Callable] = None) -> Union[List[dict], None]:
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

        # Build the query to get document data
        query = async_supabase_client.from_(table_name).select(
            "title, content, chunk_number").eq("url", url)

        # Add source filter if provided
        if source:
            query = query.eq("metadata->>source", source)

        # Execute query with chunk ordering
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
        format_fn: Optional[Callable] = None) -> Union[List[dict], str]:
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
        logger.debug(
            f"Retrieving chunks from {table_name} using vector search")

        # Prepare filter params if source is provided
        filter_params = {}
        if source:
            filter_params["source"] = source

        # Execute vector similarity search
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
        logger.info(
            f"Retrieved {len(data)} chunks for vector similarity search")

        # Return raw or formatted data
        if not format_fn:
            return data

        # Apply formatter and return
        return format_fn(data)

    except Exception as e:
        error_msg = "Error retrieving chunks from vector similarity search"
        logger.error(f"{error_msg}: {str(e)}")
        raise SupabaseError(error_msg, exception=e)


def save_chunk_to_disk(rgd: ResponseGetDataSupabase = None,
                       data: Dict[str, Any] = None,
                       url: str = None,
                       export_folder=None,
                       output_path=None,
                       **kwargs) -> bool:
    """
    Save a data chunk to disk as a markdown file with frontmatter.
    
    This function saves crawled data as markdown files with YAML frontmatter.
    The frontmatter contains metadata about the document (URL, title, etc.),
    while the main content is stored in the markdown body.
    
    Args:
        output_path: Path where file should be saved
        data: Data to save, including required fields: url, source, content
        **kwargs: Additional parameters (unused)
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        SupabaseError: If chunk cannot be saved, particularly if required fields are missing
        
    Example:
        ```python
        save_chunk_to_disk(
            "output/example.md",
            {
                "url": "https://example.com",
                "source": "web_crawler",
                "content": "This is the main content",
                "title": "Example Page",
                "chunk_number": 1
            }
        )
        # Creates a file with content:
        # ---
        # url: https://example.com
        # session_id: web_crawler
        # chunk_number: 1
        # title: Example Page
        # updated_dt: 2023-01-01T12:00:00.000000
        # ---
        # This is the main content
        ```
    """
    data = data or {}
    try:
        output_path = output_path or f"{export_folder}/{convert_url_file_name(url or rgd and rgd.url)}.md"

        # Ensure directory exists
        upsert_folder(output_path)

        # Extract required fields

        url = rgd and rgd.url or data and data["url"]
        source = rgd and rgd.source or data and data["source"]
        content = rgd and (rgd.markdown
                           or rgd.html) or data and data["content"]

        # Extract optional fields
        title = data.get("title")
        summary = data.get("summary")
        embedding = data.get("embedding")
        metadata = data.get("metadata")
        chunk_number = data.get("chunk_number")

        # Build frontmatter and content
        output_lines = [
            "---",
            f"url: {url}",
            f"session_id: {source}",
            f"chunk_number: {chunk_number}"
            if chunk_number is not None else None,
            f"title: {title}" if title is not None else None,
            f"summary: {summary}" if summary is not None else None,
            f"embedding: {embedding}" if embedding is not None else None,
            f"metadata: {json.dumps(metadata)}"
            if metadata is not None else None,
            f"updated_dt: {dt.datetime.now().isoformat()}",
            "---",
            content,
        ]

        # Write to file, filtering out None values
        with open(output_path, "w+", encoding="utf-8") as f:
            f.write("\n".join(
                [line for line in output_lines if line is not None]))

        logger.info(f"Successfully saved chunk to {output_path}")
        return True

    except Exception as e:
        error_msg = f"Error saving chunk to {output_path}"
        logger.error(f"{error_msg}: {str(e)}")
        if isinstance(e, SupabaseError):
            raise
        raise SupabaseError(error_msg, exception=e)
