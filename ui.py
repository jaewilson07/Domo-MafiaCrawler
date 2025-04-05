"""
This module initializes and runs the Streamlit UI for the Agent Builder application.
It integrates with OpenAI and Supabase to provide a dynamic agent-building experience.
"""

from __future__ import annotations

# Standard library imports
import asyncio
from functools import partial
import os
import logging
import sys

# Third-party imports
from dotenv import load_dotenv
from supabase import Client as SupabaseClient
from openai import AsyncOpenAI

# Internal imports
from agents.ai_expert import ai_expert as agent, PydanticAIDependencies
from agents.ui import run_agent_with_streaming, streamlit_ui

# -------------------------------------------------------------------
# Environment Setup
# -------------------------------------------------------------------

# Load environment variables
# see env_sample for sample .env
load_dotenv()

# -------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

# -------------------------------------------------------------------
# API Keys and Client Initialization
# -------------------------------------------------------------------

open_ai_key = os.environ["OPENAI_API_KEY"]
supabase_url = os.environ["SUPABASE_URL"]
supabase_service_key = os.environ["SUPABASE_SERVICE_KEY"]

openai_client = AsyncOpenAI(api_key=open_ai_key)
supabase: SupabaseClient = SupabaseClient(supabase_url, supabase_service_key)

dependencies = PydanticAIDependencies(supabase=supabase, openai_client=openai_client)

# -------------------------------------------------------------------
# Main Application Logic
# -------------------------------------------------------------------


async def main():
    """
    Main entry point for the Streamlit UI application.
    """
    logger.info("Starting the Streamlit UI for the Agent Builder...")
    try:
        await streamlit_ui(
            title="RAG Expert",
            description="Ask me a question about data I have collated in Supabase",
            default_chat_input="How can I help you?",
            run_agent_with_streaming=partial(
                run_agent_with_streaming, agent=agent, dependencies=dependencies
            ),
        )
        logger.info("Streamlit UI has been successfully launched.")
    except Exception as e:
        logger.error(f"An error occurred while running the Streamlit UI: {e}")
        raise


# -------------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Initializing the main event loop...")
    asyncio.run(main())
    logger.info("Application has exited.")
