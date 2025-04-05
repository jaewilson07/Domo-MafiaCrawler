from typing import List


def format_supabase_chunks(data: List[dict]) -> List[str]:
    return [f"# {doc['title']}\n\n{doc['content']}" for doc in data]


def format_supabase_page(data: List[dict]) -> str:
    page_title = data[0]["title"].split(" - ")[0]
    formatted_content = [f"# {page_title}\n"]
    for chunk in data:
        formatted_content.append(chunk["content"])
    return "\n\n".join(formatted_content)
