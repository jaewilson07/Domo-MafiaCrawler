from supabase import Client as SupabaseClient
from openai import AsyncClient
from dataclasses import dataclass


@dataclass
class PydanticAIDependencies:
    supabase: SupabaseClient
    openai_client: AsyncClient
    expertise: str = None  # filter supabase metadata by source field
