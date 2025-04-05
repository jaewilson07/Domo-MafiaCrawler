from dotenv import load_dotenv

import os

import asyncio

from agents.ui import (
    st,
    run_agent_with_streaming,
    ModelRequest,
    ModelResponse,
    display_message_part,
    UserPromptPart,
)

from supabase import Client as SupabaseClient
from openai import AsyncOpenAI

from agents.ai_expert import ai_expert as agent, PydanticAIDependencies, PydanticAgent

load_dotenv()

open_ai_key = os.environ["OPENAI_API_KEY"]
supabase_url = os.environ["SUPABASE_URL"]
supabase_service_key = os.environ["SUPABASE_SERVICE_KEY"]

openai_client = AsyncOpenAI(api_key=open_ai_key)
supabase: SupabaseClient = SupabaseClient(supabase_url, supabase_service_key)

# logfire.configure(send_to_logfire="never")

dependencies = PydanticAIDependencies(supabase=supabase, openai_client=openai_client)

title = "Pydantic AI Agenti RAG"
description = "Ask me any question about Pydantic AI"
default_chat_input = "What questions do you have about Pydantic AI?"


async def expert_ui(
    title: str,
    description: str,
    default_chat_input: str,
    agent: PydanticAgent,
    agent_dependencies: PydanticAIDependencies,
):
    st.title(title)
    st.write(description)

    # initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # display all messages so far
    # each message is either a ModelRequest or ModelResponse
    for msg in st.session_state.messages:
        if isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
            for part in msg.parts:
                display_message_part(part)

    user_input = st.chat_input(default_chat_input)

    if user_input:
        st.session_state.messages.append(
            ModelRequest(parts=[UserPromptPart(content=user_input)])
        )

    with st.chat_message("assistant"):
        await run_agent_with_streaming(
            user_input, agent=agent, dependencies=agent_dependencies
        )


async def main():
    await expert_ui(
        title=title,
        description=description,
        default_chat_input=default_chat_input,
        agent=agent,
        agent_dependencies=dependencies,
    )


if __name__ == "__main__":
    asyncio.run(main())
