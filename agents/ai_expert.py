from pydantic_ai import Agent as PydanticAgent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from agents.tools.dependencies import PydanticAIDependencies
from agents.tools.rag import retrieve_llm, list_documentation_pages, get_page_content
from pydantic_ai import Tool

model = OpenAIModel("gpt-4o-mini-2024-07-18")

with open("agents/prompts/ai_expert.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read().strip()


ai_expert = PydanticAgent(
    model=model,
    system_prompt=system_prompt,
    deps_type=PydanticAIDependencies,
    retries=2,
    tools=[
        Tool(retrieve_llm, takes_ctx=True),
        Tool(list_documentation_pages, takes_ctx=True),
        Tool(get_page_content, takes_ctx=True),
    ],  # Registering tools here
)
