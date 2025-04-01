# Supabase Integration Guide

This document provides comprehensive guidance on integrating Supabase with the web crawler application. It covers setup, configuration, and common usage patterns.

## Overview

The crawler application leverages Supabase as an optional backend for storing and retrieving crawled data. The integration is built with graceful degradation in mind, allowing the application to function even when Supabase is not available.

## Key Components

The Supabase integration consists of the following key components:

1. **AsyncClient Wrapper**: A type-safe wrapper around the Supabase AsyncClient that provides proper error handling
2. **Data Storage Functions**: Functions for storing crawl results in Supabase tables
3. **Data Retrieval Functions**: Functions for querying and retrieving crawled data
4. **Formatting Utilities**: Tools for formatting retrieved data into markdown, JSON, or other formats

## Setup Instructions

### Prerequisites

- Supabase account and project
- API keys (URL and anon key)
- PostgreSQL database with appropriate schema

### Configuration

1. Install the Supabase Python client:
   ```bash
   pip install supabase
   ```

2. Set up environment variables:
   ```bash
   export SUPABASE_URL="https://your-project-id.supabase.co"
   export SUPABASE_KEY="your-anon-key"
   ```

3. Initialize the client:
   ```python
   from supabase import create_client
   
   supabase_url = os.environ.get("SUPABASE_URL")
   supabase_key = os.environ.get("SUPABASE_KEY")
   
   supabase = create_client(supabase_url, supabase_key)
   ```

## Database Schema

The integration expects a database table with at least the following structure:

```sql
CREATE TABLE site_pages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  url TEXT NOT NULL,
  title TEXT,
  content TEXT,
  chunk_number INTEGER DEFAULT 0,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(url, chunk_number)
);
```

## Usage Examples

### Storing Crawl Results

```python
from routes.supabase import store_data_in_supabase_table

async def store_crawl_results(client, url, content, title):
    data = {
        "url": url,
        "content": content,
        "title": title,
        "chunk_number": 0,
        "metadata": {
            "source": "web_crawler",
            "crawl_date": datetime.now().isoformat()
        }
    }
    
    result = await store_data_in_supabase_table(client, "site_pages", data)
    return result.is_success
```

### Retrieving Document by URL

```python
from routes.supabase import get_document_from_supabase, format_supabase_chunks_into_pages

async def get_document_content(client, url):
    try:
        # Get the document and format it as a single page
        content = await get_document_from_supabase(
            client, 
            url,
            format_fn=format_supabase_chunks_into_pages
        )
        return content
    except SupabaseError as e:
        print(f"Error retrieving document: {e}")
        return None
```

### Vector Similarity Search

For advanced use cases, the integration supports vector similarity search:

```python
from routes.supabase import get_chunks_from_supabase

async def find_similar_documents(client, query_embedding):
    try:
        results = await get_chunks_from_supabase(
            client,
            query_embedding,
            match_count=5
        )
        return results
    except SupabaseError as e:
        print(f"Error during vector search: {e}")
        return []
```

## Error Handling

The integration provides consistent error handling through the `SupabaseError` class:

```python
try:
    result = await get_document_from_supabase(client, "https://example.com")
except SupabaseError as e:
    # Handle the error appropriately
    print(f"Supabase error occurred: {e}")
    if e.exception:
        print(f"Original exception: {e.exception}")
```

## Graceful Degradation

The module automatically detects when Supabase is not available and provides appropriate fallbacks:

1. Clear error messages when attempting to use Supabase functions
2. Alternative storage to disk using the `save_chunk_to_disk` function
3. Mock implementations for LSP type checking and development

## Best Practices

1. Always check for the availability of Supabase before attempting operations
2. Use the standardized response objects for consistent error handling
3. Implement proper retry mechanisms for network operations
4. Structure your data to take advantage of chunk-based storage for large documents

## Troubleshooting

Common issues and their solutions:

1. **Authentication Errors**: Verify your environment variables are set correctly
2. **RPC Errors**: Ensure your database has the correct functions installed
3. **Schema Mismatches**: Check that your table structure matches the expected schema
4. **Import Errors**: Make sure the Supabase package is installed in your environment