from client.MafiaError import MafiaError

from client.ResponseGetData import ResponseGetData
import utils.files as utfi
import utils.convert as utcv
import utils.chunking as utch
import utils.chunk_execution as utce

from routes import openai as openai_routes
from routes import crawler as crawler_routes
from routes import supabase as supabase_routes

# Standard library imports
import os
import logging
from dataclasses import dataclass, field
from typing import Union, List, Optional
from urllib.parse import urlparse
import datetime as dt
from functools import partial

# Set up logger
logger = logging.getLogger(__name__)

# Utility imports with robust error handling

prompt_extract_title_and_summary = """
You are an AI that extracts titles and summaries from documentation chunks.
Return a JSON object with 'title' and 'summary' keys.
For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
For the summary: Create a concise summary of the main points in this chunk.
Keep both title and summary concise but informative.  The text will be stored as markdown frontmatter so avoid the use of special characters.
"""


@dataclass
class CrawlerDependencies:
    async_supabase_client: supabase_routes.AsyncSupabaseClient
    async_openai_client: openai_routes.AsyncOpenaiClient
    async_embedding_client: openai_routes.AsyncOpenaiClient


@dataclass
class Crawler_ProcessedChunk_Metadata:
    source: str
    crawled_at: str
    url_path: str
    chunk_size: int

    @classmethod
    def from_url(cls, source, chunk: str, url):
        return cls(
            source=source,
            crawled_at=dt.datetime.now().isoformat(),
            url_path=urlparse(url).path,
            chunk_size=len(chunk),
        )

    def to_json(self):
        return {
            "source": self.source,
            "crawled_at": self.crawled_at,
            "url_path": self.url_path,
            "chunk_size": self.chunk_size,
        }


class PC_PathNotExist(MafiaError):

    def __init__(self, md_path):
        super().__init__(f"path {md_path} does not exist")


@dataclass
class Crawler_ProcessedChunk:
    source: str  # where a piece of data came from (e.g. a session_id) // could be a complete website or subject area
    url: str
    chunk_number: int
    content: str = field(repr=False)  # the actual data
    title: str = ""
    summary: str = ""
    embedding: List[float] = field(default_factory=list)
    error_logs: List[str] = field(default_factory=list)
    Metadata: Union[Crawler_ProcessedChunk_Metadata, None] = None
    Dependencies: Optional[CrawlerDependencies] = field(default=None,
                                                        repr=False)

    def __eq__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False

        return self.url == other.url and self.chunk_number == other.chunk_number

    def __post_init__(self):
        self.Metadata = Crawler_ProcessedChunk_Metadata.from_url(
            url=self.url,
            source=self.source,
            chunk=self.content,
        )

    def compare_self_to_disk(self, md_path):
        if not os.path.exists(md_path):
            return False

        try:
            md_chunk = self.from_md_file(md_path=md_path)

        except PC_PathNotExist:
            return False

        if not md_chunk:
            return False

        if md_chunk.content == self.content:
            self.title = self.title or md_chunk.title
            self.summary = self.summary or md_chunk.summary
            self.embedding = self.embedding or md_chunk.embedding
            self.Metadata = md_chunk.Metadata
            self.error_logs = md_chunk.error_logs

        return self

    @classmethod
    def from_chunk(cls,
                   content: str,
                   chunk_number: int,
                   url: str,
                   source: str,
                   output_path=None,
                   dependencies=None):
        """
        Create a Crawler_ProcessedChunk from a content chunk.

        Args:
            content (str): The content of the chunk
            chunk_number (int): The number of the chunk
            url (str): The URL the chunk came from
            source (str): The source identifier
            output_path (str, optional): Path to check for existing content
            dependencies (CrawlerDependencies, optional): Dependencies for the chunk

        Returns:
            Crawler_ProcessedChunk: A new chunk instance
        """
        # Create default values for empty strings to avoid None type issues
        if not url:
            url = "unknown-url"
        if not source:
            source = "unknown-source"

        # Initialize with the provided values
        chk = cls(
            url=url,
            chunk_number=chunk_number,
            source=source,
            content=content,
            Dependencies=dependencies,
        )

        # Compare to existing content if output path provided
        if output_path:
            chk.compare_self_to_disk(output_path)

        return chk

    @classmethod
    def from_md_file(cls, md_path, dependencies=None):
        """
        Create a Crawler_ProcessedChunk from a markdown file.

        Args:
            md_path (str): Path to the markdown file
            dependencies (CrawlerDependencies, optional): Dependencies for the chunk

        Returns:
            Crawler_ProcessedChunk: A new chunk instance, or False if error
        """
        if not os.path.exists(md_path):
            raise PC_PathNotExist(md_path)

        try:
            content, fm = utfi.read_md_from_disk(md_path)

            # Get values with defaults for required fields
            url = fm.get("url", "unknown-url")
            source = fm.get("session_id", "unknown-source")
            chunk_number = fm.get("chunk_number", 0)

            # Create the chunk
            res = cls(
                url=url,
                source=source,
                chunk_number=chunk_number,
                title=fm.get("title", ""),
                summary=fm.get("summary", ""),
                embedding=fm.get("embedding", []),
                content=content,
                Dependencies=dependencies,
            )

            return res

        except Exception as e:
            logger.error(f"Error loading markdown file {md_path}: {str(e)}")
            return False

    async def get_title_and_summary(
        self,
        is_replace_llm_metadata: bool = False,
        model="gpt-4o-mini-2024-07-18",
        debug_prn: bool = False,
        return_raw: bool = False,
    ) -> Union[ResponseGetData, dict]:
        # Get client either from parameter or from Dependencies
        async_client = None
        if self.Dependencies and hasattr(self.Dependencies,
                                         'async_openai_client'):
            async_client = self.Dependencies.async_openai_client

        if async_client is None:
            logger.warning(
                "No OpenAI client provided and none available in Dependencies")
            self.error_logs.append("No OpenAI client available")
            return {"error": "No OpenAI client available"}

        if not is_replace_llm_metadata and self.title and self.summary:
            if debug_prn:
                print(f"🛢️ {self.url} title and summary already exists")
            return {"title": self.title, "summary": self.summary}

        system_prompt = prompt_extract_title_and_summary

        messages = [
            openai_routes.ChatMessage(role="system", content=system_prompt),
            openai_routes.ChatMessage(
                role="user",
                content=f"URL: {self.url}\n\nContent:\n{self.content[:1000]}..."
            )  # Send first 1000 chars for context
        ]

        try:
            res = await openai_routes.generate_openai_chat(
                messages=messages,
                async_client=async_client,
                model=model,
                response_format={"type": "json_object"},
                return_raw=return_raw,
            )

            if return_raw:
                return res

            self.title = res.response.get("title", "No Title")
            self.summary = res.response.get("summary", "No Summary")

            return {"title": self.title, "summary": self.summary}

        except Exception as e:
            message = f"Error getting title and summary: {str(e)}"
            logger.error(message)
            self.error_logs.append(message)
            return {"error": message}

    async def get_embedding(
        self,
        is_replace_llm_metadata: bool = False,
        model="text-embedding-3-small",
        return_raw: bool = False,
        debug_prn: bool = False,
    ) -> Union[ResponseGetData, List[float]]:
        # Get client either from parameter or from Dependencies
        async_client = self.Dependencies.async_openai_client if self.Dependencies and hasattr(
            self.Dependencies, 'async_embedding_client') else None

        if async_client is None:
            logger.warning(
                "No OpenAI client provided and none available in Dependencies")
            self.error_logs.append("No OpenAI client available")
            return []

        if not is_replace_llm_metadata and self.embedding:
            if debug_prn:
                print(f"🛢️  {self.url} embedding already retrieved")
            return self.embedding

        try:
            res = await openai_routes.generate_openai_embedding(
                text=self.content,
                async_client=async_client,
                model=model,
                return_raw=return_raw,
                debug_prn=debug_prn,
            )

            if return_raw:
                return res

            self.embedding = res if isinstance(res, list) else []
            return self.embedding

        except Exception as e:
            message = f"Error creating embedding: {str(e)}"
            logger.error(message)
            self.error_logs.append(message)
            return []

    async def generate_metadata(
        self,
        is_replace_llm_metadata: bool = False,
        text_model="gpt-4o-mini-2024-07-18",
        embedding_model="text-embedding-3-small",
        debug_prn: bool = False,
        output_path: str = None,
    ):
        """
        Generate metadata (title, summary, embedding) for this chunk.

        Args:
            is_replace_llm_metadata (bool): Whether to replace existing metadata
            async_text_client (AsyncOpenAI): Client for text generation
            async_embedding_model (AsyncOpenAI): Client for embedding generation
            text_model (str): Model name for text generation
            embedding_model (str): Model name for embedding generation
            debug_prn (bool): Whether to print debug info
            output_path (str): Path to save the result to

        Returns:
            self: The current instance with updated metadata
        """
        # Get title and summary
        await self.get_title_and_summary(
            is_replace_llm_metadata=is_replace_llm_metadata,
            model=text_model,
            debug_prn=debug_prn,
        )

        # Get embedding
        await self.get_embedding(
            is_replace_llm_metadata=is_replace_llm_metadata,
            model=embedding_model,
            debug_prn=debug_prn,
        )

        # Save to disk if output path provided
        if output_path:
            try:
                supabase_routes.save_chunk_to_disk(output_path=output_path,
                                                   data=self.to_json())
                if debug_prn:
                    logger.info(f"Saved chunk to {output_path}")
            except Exception as e:
                error_msg = f"Failed to save chunk to disk: {str(e)}"
                logger.error(error_msg)
                self.error_logs.append(error_msg)

        return self

    def to_json(self):
        return {
            "url": self.url,
            "source": self.source,
            "chunk_number": self.chunk_number,
            "title": self.title or "No Title",
            "summary": self.summary or "No Summary",
            "content": self.content,
            "metadata": self.Metadata and self.Metadata.to_json(),
            "embedding": self.embedding or [0] * 1536,
        }
