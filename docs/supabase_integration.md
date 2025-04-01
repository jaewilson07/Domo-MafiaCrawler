# Supabase Integration Guide

This document provides detailed information about the Supabase integration module in this project. The module (`routes/supabase.py`) provides functionality for storing and retrieving crawled data in a Supabase database.

## Table of Contents
- [Overview](#overview)
- [Setup](#setup)
- [Core Functions](#core-functions)
- [Data Formatting](#data-formatting)
- [Examples](#examples)
- [Error Handling](#error-handling)
- [Type Definitions](#type-definitions)

## Overview

The Supabase integration module provides functions for:
- Storing crawled data in Supabase tables
- Retrieving document URLs
- Getting document content by URL
- Performing vector similarity searches
- Saving chunks to disk with frontmatter

The module is designed to be robust, with graceful fallbacks when dependencies are unavailable and comprehensive error handling.

## Setup

### Prerequisites

1. Install the required packages:
   ```bash
   pip install supabase python-frontmatter
   ```

2. Set up environment variables for Supabase:
   ```
   SUPABASE_URL=your-project-url
   SUPABASE_SERVICE_KEY=your-service-key
   ```

3. Import and initialize the Supabase client:
   ```python
   import os
   from supabase import AsyncClient

   # Initialize client
   supabase_client = AsyncClient(
       os.environ["SUPABASE_URL"],
       os.environ["SUPABASE_SERVICE_KEY"]
   )
   ```

## Core Functions

### store_data_in_supabase_table

Stores data in a Supabase table using the upsert operation.

```python
async def store_data_in_supabase_table(
    async_supabase_client: Async_SupabaseClient,
    table_name: str,
    data: Dict[str, Any],
    on_conflict: str = "url, chunk_number"
) -> ResponseGetDataSupabase
```

**Parameters:**
- `async_supabase_client`: Initialized Supabase client
- `table_name`: Name of the table to store data in
- `data`: Data dictionary to store
- `on_conflict`: Comma-separated column names to check for conflicts

**Returns:**
- `ResponseGetDataSupabase`: Standardized response object

**Raises:**
- `SupabaseError`: If the data cannot be stored

**Example:**
```python
response = await store_data_in_supabase_table(
    supabase_client,
    "documents",
    {
        "url": "https://example.com",
        "title": "Example Domain",
        "content": "This domain is for use in illustrative examples...",
        "chunk_number": 1
    }
)
```

### get_document_urls_from_supabase

Retrieves a list of available document URLs from Supabase.

```python
async def get_document_urls_from_supabase(
    async_supabase_client: Async_SupabaseClient,
    source: Optional[str] = None,
    table_name: str = "site_pages"
) -> List[str]
```

**Parameters:**
- `async_supabase_client`: Initialized Supabase client
- `source`: Optional metadata source filter
- `table_name`: Name of the table to query

**Returns:**
- List of unique document URLs

**Raises:**
- `SupabaseError`: If URLs cannot be retrieved

**Example:**
```python
# Get all URLs
all_urls = await get_document_urls_from_supabase(supabase_client)

# Get URLs with a specific source
docs_urls = await get_document_urls_from_supabase(
    supabase_client,
    source="documentation"
)
```

### get_document_from_supabase

Retrieves a document from Supabase by URL.

```python
async def get_document_from_supabase(
    async_supabase_client: Async_SupabaseClient,
    url: str,
    table_name: str = "site_pages",
    source: Optional[str] = None,
    format_fn: Optional[Callable[[List[Dict[str, Any]]], T]] = None
) -> Union[List[Dict[str, Any]], T]
```

**Parameters:**
- `async_supabase_client`: Initialized Supabase client
- `url`: URL of the document to retrieve
- `table_name`: Name of the table to query
- `source`: Optional metadata source filter
- `format_fn`: Optional function to format the results

**Returns:**
- Document data, either raw or formatted based on format_fn

**Raises:**
- `SupabaseError`: If document cannot be retrieved

**Example:**
```python
# Get raw document data
doc_data = await get_document_from_supabase(
    supabase_client,
    "https://example.com"
)

# Get formatted document
formatted_doc = await get_document_from_supabase(
    supabase_client,
    "https://example.com",
    format_fn=format_supabase_chunks_into_pages
)
```

### get_chunks_from_supabase

Retrieves chunks from Supabase using vector similarity search.

```python
async def get_chunks_from_supabase(
    async_supabase_client: Async_SupabaseClient,
    query_embedding: List[float],
    table_name: str = "site_pages",
    match_count: int = 5,
    source: Optional[str] = None,
    format_fn: Optional[Callable[[List[Dict[str, Any]]], T]] = None
) -> Union[List[Dict[str, Any]], T]
```

**Parameters:**
- `async_supabase_client`: Initialized Supabase client
- `query_embedding`: Vector embedding for similarity search
- `table_name`: Name of the table to query
- `match_count`: Maximum number of matches to return
- `source`: Optional metadata source filter
- `format_fn`: Optional function to format the results

**Returns:**
- Chunks data, either raw or formatted based on format_fn

**Raises:**
- `SupabaseError`: If chunks cannot be retrieved

**Example:**
```python
# Get semantically similar chunks
# (assuming you have a vector embedding)
matches = await get_chunks_from_supabase(
    supabase_client,
    query_embedding=[0.1, 0.2, 0.3, ...],  # Your vector here
    match_count=5
)
```

### save_chunk_to_disk

Saves a data chunk to disk as a markdown file with frontmatter.

```python
def save_chunk_to_disk(
    output_path: str,
    data: Dict[str, Any],
    **kwargs
) -> bool
```

**Parameters:**
- `output_path`: Path where file should be saved
- `data`: Data to save, including required fields: url, source, content
- `**kwargs`: Additional parameters (unused)

**Returns:**
- `True` if successful, `False` otherwise

**Raises:**
- `SupabaseError`: If chunk cannot be saved

**Example:**
```python
success = save_chunk_to_disk(
    "output/example.md",
    {
        "url": "https://example.com",
        "source": "web_crawler",
        "content": "This is the main content",
        "title": "Example Page",
        "chunk_number": 1
    }
)
```

## Data Formatting

The module provides two utility functions for formatting Supabase data:

### format_supabase_chunks

Formats Supabase chunks into a list of markdown strings.

```python
def format_supabase_chunks(data: List[Dict[str, Any]]) -> List[str]
```

**Example output:**
```
[
  "# Title 1\n\nContent of chunk 1",
  "# Title 2\n\nContent of chunk 2"
]
```

### format_supabase_chunks_into_pages

Formats multiple Supabase chunks into a single page.

```python
def format_supabase_chunks_into_pages(data: List[Dict[str, Any]]) -> str
```

**Example output:**
```
# Main Title

Content of chunk 1

Content of chunk 2

Content of chunk 3
```

## Examples

### Basic Usage Example

```python
import os
import asyncio
from supabase import AsyncClient

# Initialize Supabase client
supabase_client = AsyncClient(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

# Define async main function
async def main():
    # Store crawled data in Supabase
    await store_data_in_supabase_table(
        supabase_client,
        "documents",
        {
            "url": "https://example.com",
            "title": "Example Domain",
            "content": "This is an example domain.",
            "chunk_number": 1
        }
    )
    
    # Get all document URLs
    urls = await get_document_urls_from_supabase(supabase_client)
    print(f"Found {len(urls)} documents")
    
    # Get a specific document
    document = await get_document_from_supabase(
        supabase_client,
        "https://example.com"
    )
    
    # Format and save to disk
    if document:
        save_chunk_to_disk(
            "output/example.md",
            document[0]  # Assuming it's the first chunk
        )

# Run the async function
asyncio.run(main())
```

### Advanced Example with Vector Search

```python
import os
import asyncio
from supabase import AsyncClient

# Initialize Supabase client
supabase_client = AsyncClient(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

# Define a custom formatter
def custom_format(chunks):
    return "\n\n".join([
        f"## {chunk.get('title', 'No Title')}\n{chunk.get('content', '')}"
        for chunk in chunks
    ])

async def vector_search_example():
    # Your vector embedding (this would typically come from a model)
    # In a real scenario, you would use an embedding model to convert text to vectors
    query_embedding = [0.1, 0.2, 0.3] * 100  # Example vector (300 dimensions)
    
    # Perform vector similarity search
    similar_chunks = await get_chunks_from_supabase(
        supabase_client,
        query_embedding=query_embedding,
        match_count=3,
        source="documentation",
        format_fn=custom_format
    )
    
    print("Formatted similar content:")
    print(similar_chunks)

# Run the async function
asyncio.run(vector_search_example())
```

## Error Handling

The module uses the custom `SupabaseError` class for error handling, which inherits from `MafiaError`. This ensures consistent error handling across the application.

```python
try:
    result = await get_document_from_supabase(client, "https://example.com")
except SupabaseError as e:
    print(f"Error: {e}")
    # Handle the error gracefully
```

## Type Definitions

The module defines several type aliases for improved code readability:

```python
T = TypeVar('T')  # Generic type for formatter functions
Document = Dict[str, Any]  # Represents a document
DocumentList = List[Document]  # List of documents
```

These types are used in function signatures to provide better type hints and documentation.