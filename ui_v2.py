from __future__ import annotations

import asyncio
from functools import partial
from typing import Callable
from enum import Enum
import os
import streamlit as st
from pydantic_ai.messages import ModelResponse, TextPart, UserPromptPart, ModelRequest

from agents.ai_expert import ai_expert as agent, PydanticAIDependencies, PydanticAgent
from agents.ui import run_agent_with_streaming, streamlit_ui

from supabase import Client as SupabaseClient
from openai import AsyncOpenAI

from dotenv import load_dotenv
import logging
import sys

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],  # Logs will be printed to stdout
    force=True,  # Ensures the configuration is applied even if logging is already configured
)


open_ai_key = os.environ["OPENAI_API_KEY"]
supabase_url = os.environ["SUPABASE_URL"]
supabase_service_key = os.environ["SUPABASE_SERVICE_KEY"]

openai_client = AsyncOpenAI(api_key=open_ai_key)
supabase: SupabaseClient = SupabaseClient(supabase_url, supabase_service_key)

dependencies = PydanticAIDependencies(supabase=supabase, openai_client=openai_client)


async def main():
    logger.info("Starting the Streamlit UI for the Agent Builder...")
    try:
        await streamlit_ui(
            title="Agent Builder",
            description="Describe an agent and I'll code it for you.",
            default_chat_input="What questions do you have about Pydantic AI?",
            run_agent_with_streaming=partial(
                run_agent_with_streaming, agent=agent, dependencies=dependencies
            ),
        )
        logger.info("Streamlit UI has been successfully launched.")
    except Exception as e:
        logger.error(f"An error occurred while running the Streamlit UI: {e}")
        raise


if __name__ == "__main__":
    logger.info("Initializing the main event loop...")
    asyncio.run(main())
    logger.info("Application has exited.")
