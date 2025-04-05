from typing import List


def format_supabase_chunks(data: List[dict]) -> List[str]:
    """
    Format one or more Supabase response chunks into strings for LLM input.
    Each chunk includes its title and content.
    """
    return [f"LLM Info: {doc['title']}\n\n{doc['content']}" for doc in data]


def format_supabase_page(data: List[dict]) -> str:
    """
    Format a Supabase response page into one string for LLM input.
    Uses the first document's title for the page header.
    """
    page_title = data[0]["title"].split(" - ")[0]
    formatted_content = [f"LLM Page Info: {page_title}\n"]
    for chunk in data:
        formatted_content.append(chunk["content"])
    return "\n\n".join(formatted_content)
