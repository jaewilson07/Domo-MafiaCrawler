"""
Module defining dependencies for the Pydantic AI agent.

This module encapsulates the external services required by the agent, including:
- A Supabase client for database interactions.
- An asynchronous OpenAI client for generating embeddings and processing text.
- An optional expertise string to filter queries based on a specific source.
"""

from supabase import Client as SupabaseClient
from openai import AsyncClient
from dataclasses import dataclass


@dataclass
class PydanticAIDependencies:
    """
    Encapsulates the dependencies required by the Pydantic-based AI agent.

    Attributes:
        supabase (SupabaseClient): Client instance for interacting with the Supabase database.
        openai_client (AsyncClient): Asynchronous client for accessing OpenAI services.
        expertise (str, optional): An optional filter to query Supabase by a specific source.
    """

    supabase: SupabaseClient
    openai_client: AsyncClient
    expertise: str = None  # filter supabase metadata by source field
