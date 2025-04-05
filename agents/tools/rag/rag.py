from typing import List
import logging
from agents.tools.rag.utils import format_supabase_chunks, format_supabase_page
from routes.openai import generate_openai_embedding

logger = logging.getLogger(__name__)


async def retrieve_llm(ctx, user_query: str) -> str:
    """
    Retrieve relevant documentation pages based on a user query.

    This function embeds the user query using OpenAI embeddings and retrieves the top 5
    relevant documentation pages from Supabase. If an expertise filter is set in the
    context dependencies, it applies the filter to narrow down the results.

    Args:
        ctx: The context object containing dependencies like Supabase and OpenAI client.
        user_query (str): The user's query string.

    Returns:
        str: A formatted string containing the top 5 relevant documentation pages,
        or a message indicating no relevant documentation was found.
    """
    logger.info(f"Retrieving documentation for query: {user_query}")
    query_embedding = await generate_openai_embedding(
        user_query, ctx.deps.openai_client
    )

    table_query = {
        "query_embedding": query_embedding,
        "match_count": 5,
    }

    if ctx.deps.expertise:
        table_query.update({"filter": {"source": ctx.deps.expertise}})

    result = ctx.deps.supabase.rpc("match_site_pages", table_query).execute()

    if not result.data:
        return "No relevant documentation found."

    print(result.data)

    return "\n\n---\n\n".join(format_supabase_chunks(result.data))


async def list_documentation_pages(ctx) -> List[str]:
    """
    List all available documentation pages.

    This function retrieves a list of all documentation page URLs from Supabase.
    If an expertise filter is set in the context dependencies, it filters the results
    by the specified source.

    Args:
        ctx: The context object containing dependencies like Supabase.

    Returns:
        List[str]: A sorted list of unique URLs for the documentation pages, or an
        empty list if no pages are found.
    """
    logger.info("Listing all documentation pages from Supabase...")
    result = None
    if ctx.deps.expertise:
        # If expertise is set, filter by that source

        result = (
            ctx.deps.supabase.table("site_pages")
            .select("url")
            .eq("metadata->>source", ctx.deps.expertise)
            .execute()
        )

    else:
        result = ctx.deps.supabase.table("site_pages").select("url").execute()

    if not result.data:
        return []

    return sorted(set(doc["url"] for doc in result.data))


async def get_page_content(ctx, url: str) -> str:
    """
    Retrieve the content of a specific documentation page.

    This function fetches the content of a documentation page from Supabase based on
    its URL. If an expertise filter is set in the context dependencies, it applies the
    filter to narrow down the results.

    Args:
        ctx: The context object containing dependencies like Supabase.
        url (str): The URL of the documentation page to retrieve.

    Returns:
        str: The formatted content of the documentation page, or a message indicating
        no content was found for the given URL.
    """
    logger.info(f"Retrieving content for URL: {url}")
    result = None

    if ctx.deps.expertise:
        result = (
            ctx.deps.supabase.table("site_pages")
            .select("title, content, chunk_number")
            .eq("url", url)
            .eq("metadata->>source", ctx.deps.expertise)
            .order("chunk_number")
            .execute()
        )

    else:
        result = (
            ctx.deps.supabase.table("site_pages")
            .select("title, content, chunk_number")
            .eq("url", url)
            .order("chunk_number")
            .execute()
        )

    if not result.data:
        return f"No content found for URL: {url}"

    return format_supabase_page(result.data)
