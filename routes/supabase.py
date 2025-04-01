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

import json
import logging
import os
import datetime as dt
from typing import List, Dict, Callable, Optional, Any, Union, TypeVar, cast

# Try to import supabase safely
try:
    from supabase import AsyncClient as Async_SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    # Create a placeholder for type hints if supabase is not available
    class Async_SupabaseClient:
        """
        Placeholder for type hints when supabase is not available.
        
        This class mimics the structure of the Supabase AsyncClient to provide
        type hints and code completion in environments where the Supabase package
        is not installed. This allows for cleaner error handling and better
        development experience.
        
        In a production environment, the real Async_SupabaseClient from the
        supabase package should be used instead.
        
        Note:
            These mock methods are only intended for LSP type checking and should not
            be used in actual code. The SUPABASE_AVAILABLE flag should be checked
            before attempting to use any Supabase functionality.
        """
        def __init__(self, *args, **kwargs):
            """Initialize a placeholder client that will raise appropriate errors when used."""
            import warnings
            warnings.warn(
                "Using mock Supabase client. Install the supabase package for actual functionality.",
                DeprecationWarning, stacklevel=2
            )
            
        def from_(self, table_name):
            """[MOCK] Method for table selection in Supabase queries."""
            return self
            
        def table(self, table_name):
            """[MOCK] Method for table operations in Supabase."""
            return self
            
        def select(self, columns):
            """[MOCK] Method for column selection in Supabase queries."""
            return self
            
        def eq(self, column, value):
            """[MOCK] Method for equality filtering in Supabase queries."""
            return self
            
        def order(self, column):
            """[MOCK] Method for ordering results in Supabase queries."""
            return self
            
        def upsert(self, data, **kwargs):
            """[MOCK] Method for upserting data in Supabase."""
            return self
            
        def rpc(self, function_name, params=None):
            """[MOCK] Method for RPC calls in Supabase."""
            return self
            
        async def execute(self):
            """[MOCK] Method for executing Supabase queries."""
            class MockResult:
                data = []
                
            return MockResult()
            
    # Mark that Supabase is not available in this environment
    SUPABASE_AVAILABLE = False

# Local imports
from client.MafiaError import MafiaError
from client.ResponseGetData import ResponseGetDataSupabase

# Try to import local file utilities or use built-in alternatives
try:
    from utils.files import upsert_folder
    LOCAL_FILES_MODULE = True
except ImportError:
    # Fallback implementation if utils.files is not available
    def upsert_folder(folder_path: str) -> str:
        """
        Simple fallback to ensure a folder exists for file operations.
        
        Args:
            folder_path: Path to create
            
        Returns:
            Absolute path to the folder
        """
        dir_path = os.path.dirname(os.path.abspath(folder_path))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        return dir_path

    LOCAL_FILES_MODULE = False

# Configure logging
logger = logging.getLogger(__name__)

# Type aliases for improved code readability and type checking
T = TypeVar('T')  # Generic type for formatter functions
Document = Dict[str, Any]  # Represents a single document or chunk
DocumentList = List[Document]  # List of documents or chunks

# These type aliases are used throughout the module to provide better type hints
# and make the code more maintainable. Examples:
# - T allows for generic formatting functions that can return any type
# - Document represents a dictionary with string keys and any values (document data)
# - DocumentList represents a list of Document objects (e.g., chunks of a page)


class SupabaseError(MafiaError):
    """
    Custom exception for Supabase-related errors.
    
    This class extends MafiaError to provide consistent error handling for Supabase operations.
    It adds helpful context about Supabase operations and wraps any original exceptions.
    
    Attributes:
        message (str): Human-readable error description
        exception (Exception): Original exception that was caught, if any
        
    Example:
        ```python
        try:
            result = await get_document_from_supabase(client, "https://example.com")
        except SupabaseError as e:
            print(f"Supabase error occurred: {e}")
            # Handle the error appropriately
        ```
    """

    def __init__(self,
                 message: Optional[str] = None,
                 exception: Optional[Exception] = None):
        """
        Initialize a new SupabaseError.
        
        Args:
            message: Description of the error
            exception: Original exception that was caught
        """
        super().__init__(message=message, exception=exception)


async def store_data_in_supabase_table(
        async_supabase_client: Async_SupabaseClient,
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
    if not SUPABASE_AVAILABLE:
        raise SupabaseError(
            "Supabase client not available. Please install the supabase package."
        )

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
        async_supabase_client: Async_SupabaseClient,
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
    if not SUPABASE_AVAILABLE:
        raise SupabaseError(
            "Supabase client not available. Please install the supabase package."
        )

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


def format_supabase_chunks_into_pages(data: List[Dict[str, Any]]) -> str:
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
    async_supabase_client: Async_SupabaseClient,
    url: str,
    table_name: str = "site_pages",
    source: Optional[str] = None,
    format_fn: Optional[Callable[[List[Dict[str, Any]]], T]] = None
) -> Union[List[Dict[str, Any]], T]:
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
    if not SUPABASE_AVAILABLE:
        raise SupabaseError(
            "Supabase client not available. Please install the supabase package."
        )

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
        return cast(T, format_fn(data))

    except Exception as e:
        error_msg = f"Error retrieving document for URL: {url}"
        logger.error(f"{error_msg}: {str(e)}")
        raise SupabaseError(error_msg, exception=e)


async def get_chunks_from_supabase(
    async_supabase_client: Async_SupabaseClient,
    query_embedding: List[float],
    table_name: str = "site_pages",
    match_count: int = 5,
    source: Optional[str] = None,
    format_fn: Optional[Callable[[List[Dict[str, Any]]], T]] = None
) -> Union[List[Dict[str, Any]], T]:
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
    if not SUPABASE_AVAILABLE:
        raise SupabaseError(
            "Supabase client not available. Please install the supabase package."
        )

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
        return cast(T, format_fn(data))

    except Exception as e:
        error_msg = "Error retrieving chunks from vector similarity search"
        logger.error(f"{error_msg}: {str(e)}")
        raise SupabaseError(error_msg, exception=e)


def save_chunk_to_disk(output_path: str, data: Dict[str, Any],
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
    try:
        # Ensure directory exists
        upsert_folder(output_path)

        # Extract required fields
        try:
            url = data["url"]
            source = data["source"]
            content = data["content"]
        except KeyError as e:
            raise SupabaseError(f"Missing required field in data: {e}")

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
