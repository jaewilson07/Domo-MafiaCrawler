from typing import List, Callable
from supabase import AsyncClient as Async_SupabaseClient

import agent_mafia.utils.files as amfi
from client.MafiaError import MafiaError
import json
import datetime as dt

from client.ResponseGetData import ResponseGetDataSupabase


async def store_data_in_supabase_table(
    async_supabase_client: Async_SupabaseClient,
    table_name: str,
    data: dict,
):
    """stores data into a supabase table"""
    res = (await async_supabase_client.table(table_name).upsert(
        data, on_conflict="url, chunk_number").execute())

    rgd = ResponseGetDataSupabase.from_res(res=res)

    return rgd


async def get_document_urls_from_supabase(
    async_supabase_client: Async_SupabaseClient,
    source: str = None,
    table_name: str = "site_pages",
) -> List[str]:
    """
    Function to retrieve a list of available documentation pages.

    Returns:
        List[str]: List of unique URLs for all documentation pages
    """
    try:
        # Query Supabase for unique URLs where source is pydantic_ai_docs

        if source:
            result = await (
                async_supabase_client.from_(table_name).select("url").eq(
                    "metadata->>source", source).execute())

        else:
            result = (await async_supabase_client.from_(table_name).select(
                "url").execute())

        if not result.data:
            return []

        # Extract unique URLs
        urls = sorted(set(doc["url"] for doc in result.data))
        return urls

    except Exception as e:
        raise MafiaError("Error retrieving documentation pages", exception=e)


# %% ../../nbs/routes/storage.ipynb 11
def format_supabase_chunks(data: List[dict]) -> List[str]:
    return [f"# {doc['title']}\n\n{doc['content']}" for doc in data if doc]


def format_supabase_chunks_into_pages(data: List[dict]) -> str:
    page_title = data[0]["title"].split(" - ")[0]

    formatted_content = [f"# {page_title}\n"]

    for chunk in data:
        formatted_content.append(chunk["content"])

    return "\n\n".join(formatted_content)


async def get_document_from_supabase(
        async_supabase_client: Async_SupabaseClient,
        url: str,
        table_name: str = "site_pages",
        source: str = None,
        format_fn: Callable = None) -> List[str]:
    try:

        result = (await async_supabase_client.from_(table_name).select(
            "title, content, chunk_number").eq("url", url).eq(
                "metadata->>source", source).order("chunk_number").execute())

        data = result.data or []

        if not format_fn:
            return data

        return format_fn(data)

    except Exception as e:
        print(e)
        raise MafiaError("Error retrieving chunks", exception=e)


async def get_chunks_from_supabase(async_supabase_client: Async_SupabaseClient,
                                   query_embedding: List[float],
                                   table_name: str = "site_pages",
                                   match_count: int = 5,
                                   source: str = None,
                                   format_fn: Callable = None) -> List[str]:
    try:
        result = await async_supabase_client.rpc(
            f"match_{table_name}",
            {
                "query_embedding": query_embedding,
                "match_count": match_count,
                "filter": {
                    "source": source
                },
            },
        ).execute()

        data = result.data or []

        if not format_fn:
            return data

        return format_fn(data)

    except Exception as e:
        raise MafiaError("Error retrieving chunks", exception=e) from e


def output_chunk_to_disk(
    output_path,
    data: dict,
    **kwargs,
):

    amfi.upsert_folder(output_path)

    url = data["url"]
    source = data["source"]
    content = data["content"]
    title = data.get("title")
    summary = data.get("summary")
    embedding = data.get("embedding")
    metadata = data.get("metadata")
    chunk_number = data.get("chunk_number")

    output_ls = [
        "---",
        f"url: {url}",
        f"session_id: {source}",
        f"chunk_number: {chunk_number}" if chunk_number is not None else None,
        f"title: {title}" if title is not None else None,
        f"summary: {summary}" if summary is not None else None,
        f"embedding: {embedding}" if embedding is not None else None,
        f"metadata : {json.dumps(metadata)}" if metadata is not None else None,
        f"updated_dt: {dt.datetime.now().isoformat()}",
        "---",
        content,
    ]

    with open(output_path, "w+", encoding="utf-8") as f:
        f.write("\n".join([row for row in output_ls if row is not None]))

        return True
