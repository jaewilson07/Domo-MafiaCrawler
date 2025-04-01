# Standard library imports
import os
import json
import logging
from dataclasses import dataclass, field
from typing import Union, List, Dict, Any, Optional
from urllib.parse import urlparse
import datetime as dt
from functools import partial

# Set up logger
logger = logging.getLogger(__name__)

# Try to import third-party dependencies safely
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")
    # Define a mock class for type checking
    class AsyncOpenAI:
        """Placeholder for AsyncOpenAI when the package is not available."""
        def __init__(self, *args, **kwargs):
            pass

# Local application imports
try:
    from routes import crawler as crawler_routes
    CRAWLER_ROUTES_AVAILABLE = True
except ImportError:
    CRAWLER_ROUTES_AVAILABLE = False
    logger.warning("crawler_routes module not available.")
    # Define placeholder classes for type checking
    class BrowserConfig:
        """Placeholder for BrowserConfig when crawler_routes is not available."""
        def __init__(self, *args, **kwargs):
            pass
            
    class CrawlerRunConfig:
        """Placeholder for CrawlerRunConfig when crawler_routes is not available."""
        def __init__(self, *args, **kwargs):
            pass
            
    # Create a module-like object to avoid attribute errors
    class CrawlerRoutes:
        BrowserConfig = BrowserConfig
        CrawlerRunConfig = CrawlerRunConfig
        default_browser_config = BrowserConfig()
        
    crawler_routes = CrawlerRoutes()

from routes import openai_provider as openai_routes
try:
    from routes.supabase import AsyncSupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("supabase module not available.")
    # Define a mock class for type checking
    class AsyncSupabaseClient:
        """Placeholder for AsyncSupabaseClient when the package is not available."""
        def __init__(self, *args, **kwargs):
            pass

# Utility imports with robust error handling
from utils import files as utfi
from utils import convert as utcv
try:
    import utils.chunking as utch
    CHUNKING_AVAILABLE = True
except ImportError:
    CHUNKING_AVAILABLE = False
    logger.warning("chunking module not available.")
    
try:
    import utils.concurrency as utco
    CONCURRENCY_AVAILABLE = True
except ImportError:
    CONCURRENCY_AVAILABLE = False
    logger.warning("concurrency module not available.")

try:
    import utils.storage as utst
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    logger.warning("storage module not available.")

from client.MafiaError import MafiaError

# Aliases to make code more readable
amme = MafiaError  # alias for MafiaError
amfi = utfi        # alias for utils.files
amcv = utcv        # alias for utils.convert
amcn = utch if CHUNKING_AVAILABLE else None  # alias for utils.chunking
amce = utco if CONCURRENCY_AVAILABLE else None  # alias for utils.concurrency
storage_routes = utst if STORAGE_AVAILABLE else None  # alias for utils.storage

prompt_extract_title_and_summary = """
You are an AI that extracts titles and summaries from documentation chunks.
Return a JSON object with 'title' and 'summary' keys.
For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
For the summary: Create a concise summary of the main points in this chunk.
Keep both title and summary concise but informative.  The text will be stored as markdown frontmatter so avoid the use of special characters.
"""


@dataclass
class CrawlerDependencies:
    async_supabase_client: AsyncSupabaseClient
    async_openai_client: AsyncOpenAI


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
    Dependencies: Optional[CrawlerDependencies] = field(default=None, repr=False)

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

        except PC_PathNotExist as e:
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
            content, frontmatter = utfi.read_md_from_disk(md_path)
            
            # Get values with defaults for required fields
            url = frontmatter.get("url", "unknown-url")
            source = frontmatter.get("session_id", "unknown-source") 
            chunk_number = frontmatter.get("chunk_number", 0)
            
            # Create the chunk
            res = cls(
                url=url,
                source=source,
                chunk_number=chunk_number,
                title=frontmatter.get("title", ""),
                summary=frontmatter.get("summary", ""),
                embedding=frontmatter.get("embedding", []),
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
        async_client: AsyncOpenAI = None,
        model="gpt-4o-mini-2024-07-18",
        debug_prn: bool = False,
        return_raw: bool = False,
    ) -> dict:
        # Get client either from parameter or from Dependencies
        if async_client is None and self.Dependencies and hasattr(self.Dependencies, 'async_openai_client'):
            async_client = self.Dependencies.async_openai_client
            
        if async_client is None:
            logger.warning("No OpenAI client provided and none available in Dependencies")
            self.error_logs.append("No OpenAI client available")
            return {"error": "No OpenAI client available"}

        if not is_replace_llm_metadata and self.title and self.summary:
            if debug_prn:
                print(f"🛢️ {self.url} title and summary already exists")
            return {"title": self.title, "summary": self.summary}

        system_prompt = prompt_extract_title_and_summary

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"URL: {self.url}\n\nContent:\n{self.content[:1000]}...",
            },  # Send first 1000 chars for context
        ]
        
        try:
            if not OPENAI_AVAILABLE or not openai_routes:
                raise ImportError("OpenAI not available")
                
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
        async_client: AsyncOpenAI = None,
        model="text-embedding-3-small",
        return_raw: bool = False,
        debug_prn: bool = False,
    ) -> List[float]:
        # Get client either from parameter or from Dependencies
        if async_client is None and self.Dependencies and hasattr(self.Dependencies, 'async_openai_client'):
            async_client = self.Dependencies.async_openai_client
            
        if async_client is None:
            logger.warning("No OpenAI client provided and none available in Dependencies")
            self.error_logs.append("No OpenAI client available")
            return []

        if not is_replace_llm_metadata and self.embedding:
            if debug_prn:
                print(f"🛢️  {self.url} embedding already retrieved")
            return self.embedding

        try:
            if not OPENAI_AVAILABLE or not openai_routes:
                raise ImportError("OpenAI not available")
                
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
        async_text_client: AsyncOpenAI = None,
        async_embedding_model: AsyncOpenAI = None,
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
            async_client=async_text_client,
            model=text_model,
            debug_prn=debug_prn,
        )
        
        # Get embedding
        await self.get_embedding(
            is_replace_llm_metadata=is_replace_llm_metadata,
            async_client=async_embedding_model,
            model=embedding_model,
            debug_prn=debug_prn,
        )

        # Save to disk if output path provided
        if output_path and STORAGE_AVAILABLE and storage_routes:
            try:
                storage_routes.save_chunk_to_disk(
                    output_path=output_path,
                    data=self.to_json()
                )
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
            "metadata": self.Metadata.to_json(),
            "embedding": self.embedding or [0] * 1536,
        }


async def process_chunk(
    url,
    chunk,
    chunk_number,
    source,
    async_supabase_client,
    database_table_name,
    export_folder,
    is_replace_llm_metadata: bool = False,
    debug_prn: bool = False,
    async_openai_client=None
):
    """
    Process a single chunk of content.
    
    Args:
        url (str): The URL the chunk is from
        chunk (str): The content of the chunk
        chunk_number (int): The chunk number
        source (str): The source identifier
        async_supabase_client: The Supabase client
        database_table_name (str): The database table to store the chunk in
        export_folder (str): The folder to export to
        is_replace_llm_metadata (bool): Whether to replace existing metadata
        debug_prn (bool): Whether to print debug info
        async_openai_client: The OpenAI client
        
    Returns:
        Crawler_ProcessedChunk: The processed chunk
    """
    if debug_prn:
        logger.info(f"Starting chunk processing: {url} - {chunk_number}")

    try:
        # Create a safe path for the chunk
        chunk_path = None
        if amcv and hasattr(amcv, 'convert_url_file_name'):
            chunk_path = f"{export_folder}/chunks/{amcv.convert_url_file_name(url)}/{chunk_number}.md"
        else:
            # Fallback to a basic path if convert_url_file_name is not available
            safe_url = url.replace("://", "_").replace("/", "_").replace(".", "_")
            chunk_path = f"{export_folder}/chunks/{safe_url}/{chunk_number}.md"
            
        # Create dependencies object if clients are available
        dependencies = None
        if async_supabase_client is not None or async_openai_client is not None:
            dependencies = CrawlerDependencies(
                async_supabase_client=async_supabase_client,
                async_openai_client=async_openai_client
            )

        # Use Crawler_ProcessedChunk directly as it's defined in this module
        chunk_obj = Crawler_ProcessedChunk.from_chunk(
            content=chunk,
            chunk_number=chunk_number,
            url=url,
            source=source,
            output_path=chunk_path,
            dependencies=dependencies
        )

        # Generate metadata
        await chunk_obj.generate_metadata(
            output_path=chunk_path,
            is_replace_llm_metadata=is_replace_llm_metadata,
            debug_prn=debug_prn,
            async_text_client=async_openai_client,
            async_embedding_model=async_openai_client
        )

        # Store in database if available
        if STORAGE_AVAILABLE and storage_routes and hasattr(storage_routes, 'store_data_in_supabase_table'):
            try:
                data = chunk_obj.to_json()
                # Remove source as it might be duplicated elsewhere in the schema
                if "source" in data:
                    data.pop("source")
                    
                await storage_routes.store_data_in_supabase_table(
                    async_supabase_client=async_supabase_client,
                    table_name=database_table_name,
                    data=data,
                )
                if debug_prn:
                    logger.info(f"Stored chunk in database: {url}-{chunk_number}")
            except Exception as db_error:
                error_msg = f"Error storing chunk in database: {str(db_error)}"
                logger.error(error_msg)
                chunk_obj.error_logs.append(error_msg)

        if debug_prn:
            logger.info(f"Successfully processed chunk: {url}-{chunk_number}")

        return chunk_obj
    
    except Exception as e:
        error_msg = f"Error processing chunk {url}-{chunk_number}: {str(e)}"
        logger.error(error_msg)
        return None


# %% ../../nbs/implementations/scrape_urls.ipynb 5
async def read_url(
    url,
    source,
    browser_config: crawler_routes.BrowserConfig,
    doc_path,
    crawler_config: crawler_routes.CrawlerRunConfig = None,
    debug_prn: bool = False,
):
    if os.path.exists(doc_path):
        content, _ = amfi.read_md_from_disk(doc_path)

        if debug_prn:
            print(
                f"🛢️  {url} - scraping not required, file retrieved from - {doc_path}"
            )

        return content

    storage_fn = partial(
        storage_routes.save_chunk_to_disk,
        output_path=doc_path,
    )

    res = await crawler_routes.scrape_url(url=url,
                                          session_id=source,
                                          browser_config=browser_config,
                                          crawler_config=crawler_config,
                                          storage_fn=storage_fn)
    if debug_prn:
        print(f"🛢️  {url} - page scraped to {doc_path}")

    return res.markdown


# %% ../../nbs/implementations/scrape_urls.ipynb 6
async def process_url(
    url: str,
    source: str,
    export_folder: str,
    database_table_name: str,
    async_supabase_client=None,
    async_openai_client=None,
    debug_prn: bool = False,
    browser_config: crawler_routes.BrowserConfig = None,
    crawler_config: crawler_routes.CrawlerRunConfig = None,
    is_replace_llm_metadata: bool = False,
    max_conccurent_requests=5,
):
    """
    Process a document URL and store chunks in parallel.
    
    Args:
        url (str): The URL to process
        source (str): The source identifier
        export_folder (str): The folder to export to
        database_table_name (str): The database table to store chunks in
        async_supabase_client: The Supabase client
        async_openai_client: The OpenAI client
        debug_prn (bool): Whether to print debug info
        browser_config: The browser configuration
        crawler_config: The crawler configuration
        is_replace_llm_metadata (bool): Whether to replace existing metadata
        max_conccurent_requests (int): Maximum number of concurrent requests
        
    Returns:
        list: The processed chunks, or False if error
    """
    # Use provided configs or defaults if available
    try:
        if crawler_routes and hasattr(crawler_routes, 'default_browser_config'):
            browser_config = browser_config or crawler_routes.default_browser_config
    except Exception as e:
        logger.warning(f"Could not get default browser config: {str(e)}")
    
    try:
        if storage_routes and hasattr(storage_routes, 'async_supabase_client'):
            async_supabase_client = async_supabase_client or storage_routes.async_supabase_client
    except Exception as e:
        logger.warning(f"Could not get default supabase client: {str(e)}")

    # Create document path
    doc_path = None
    try:
        if amcv and hasattr(amcv, 'convert_url_file_name'):
            doc_path = f"{export_folder}/{amcv.convert_url_file_name(url)}.md"
        else:
            # Fallback to a basic path
            safe_url = url.replace("://", "_").replace("/", "_").replace(".", "_")
            doc_path = f"{export_folder}/{safe_url}.md"
    except Exception as e:
        logger.error(f"Error creating document path: {str(e)}")
        doc_path = f"{export_folder}/document_{hash(url)}.md"

    # Create the export folder if it doesn't exist
    os.makedirs(os.path.dirname(doc_path), exist_ok=True)

    # Scrape URL and save results to doc_path
    try:
        if debug_prn:
            logger.info(f"Starting crawl: {url}")

        markdown = await read_url(
            url=url,
            source=source,
            browser_config=browser_config,
            doc_path=doc_path,
            debug_prn=debug_prn,
            crawler_config=crawler_config,
        )

    except Exception as e:
        error_msg = f"Error reading URL {url}: {str(e)}"
        logger.error(error_msg)
        return False

    if debug_prn:
        logger.info(f"Successfully crawled: {url}")

    # Chunk the text
    chunks = []
    try:
        if amcn and hasattr(amcn, 'chunk_text'):
            chunks = amcn.chunk_text(markdown)
        else:
            # Very basic chunking fallback
            chunks = [markdown[i:i+4000] for i in range(0, len(markdown), 4000)]
    except Exception as e:
        error_msg = f"Error chunking text from {url}: {str(e)}"
        logger.error(error_msg)
        # Try a very simple chunking approach as fallback
        chunks = [markdown]

    if debug_prn:
        logger.info(f"Generated {len(chunks)} chunks to process from {url}")

    # Process chunks in parallel
    try:
        if amce and hasattr(amce, 'gather_with_concurrency'):
            res = await amce.gather_with_concurrency(
                *[
                    process_chunk(
                        url=url,
                        chunk=chunk,
                        chunk_number=idx,
                        source=source,
                        async_supabase_client=async_supabase_client,
                        async_openai_client=async_openai_client,
                        database_table_name=database_table_name,
                        export_folder=export_folder,
                        debug_prn=debug_prn,
                        is_replace_llm_metadata=is_replace_llm_metadata,
                    ) for idx, chunk in enumerate(chunks)
                ],
                n=max_conccurent_requests,
            )
        else:
            # Sequential processing as fallback
            res = []
            for idx, chunk in enumerate(chunks):
                chunk_result = await process_chunk(
                    url=url,
                    chunk=chunk,
                    chunk_number=idx,
                    source=source,
                    async_supabase_client=async_supabase_client,
                    async_openai_client=async_openai_client,
                    database_table_name=database_table_name,
                    export_folder=export_folder,
                    debug_prn=debug_prn,
                    is_replace_llm_metadata=is_replace_llm_metadata,
                )
                res.append(chunk_result)
    except Exception as e:
        error_msg = f"Error processing chunks from {url}: {str(e)}"
        logger.error(error_msg)
        return False

    if debug_prn:
        logger.info(f"Completed processing all chunks from {url}")

    return res


# %% ../../nbs/implementations/scrape_urls.ipynb 7
async def process_rgd(
    rgd,
    source: str,
    export_folder: str,
    database_table_name: str = "site_pages",
    supabase_client=None,
    async_openai_client=None,
    debug_prn: bool = False,
    is_replace_llm_metadata: bool = False,
    max_conccurent_requests=5,
):
    """
    Process a ResponseGetDataCrawler object.
    
    Args:
        rgd: The ResponseGetDataCrawler object
        source (str): The source identifier
        export_folder (str): The folder to export to
        database_table_name (str): The database table to store chunks in
        supabase_client: The Supabase client
        async_openai_client: The OpenAI client
        debug_prn (bool): Whether to print debug info
        is_replace_llm_metadata (bool): Whether to replace existing metadata
        max_conccurent_requests (int): Maximum number of concurrent requests
        
    Returns:
        list: The processed chunks
    """
    try:
        if storage_routes and hasattr(storage_routes, 'async_supabase_client'):
            supabase_client = supabase_client or storage_routes.async_supabase_client
    except Exception as e:
        logger.warning(f"Could not get default supabase client: {str(e)}")

    if debug_prn:
        logger.info(f"Processing ResponseGetDataCrawler for: {rgd.url}")

    # Chunk the markdown
    chunks = []
    try:
        if not hasattr(rgd, 'markdown') or not rgd.markdown:
            error_msg = "ResponseGetDataCrawler has no markdown attribute or it is empty"
            logger.error(error_msg)
            return []
            
        if amcn and hasattr(amcn, 'chunk_text'):
            chunks = amcn.chunk_text(rgd.markdown)
        else:
            # Very basic chunking fallback
            chunks = [rgd.markdown[i:i+4000] for i in range(0, len(rgd.markdown), 4000)]
    except Exception as e:
        error_msg = f"Error chunking text from ResponseGetDataCrawler: {str(e)}"
        logger.error(error_msg)
        # Try a very simple chunking approach as fallback
        if hasattr(rgd, 'markdown') and rgd.markdown:
            chunks = [rgd.markdown]
        else:
            return []

    if debug_prn:
        logger.info(f"Generated {len(chunks)} chunks to process from ResponseGetDataCrawler")

    # Process chunks in parallel or sequentially
    try:
        if not hasattr(rgd, 'url') or not rgd.url:
            url = "unknown-url"
        else:
            url = rgd.url
            
        if amce and hasattr(amce, 'gather_with_concurrency'):
            res = await amce.gather_with_concurrency(
                *[
                    process_chunk(
                        url=url,
                        chunk=chunk,
                        chunk_number=idx,
                        source=source,
                        async_supabase_client=supabase_client,
                        async_openai_client=async_openai_client,
                        database_table_name=database_table_name,
                        export_folder=export_folder,
                        debug_prn=debug_prn,
                        is_replace_llm_metadata=is_replace_llm_metadata,
                    ) for idx, chunk in enumerate(chunks)
                ],
                n=max_conccurent_requests,
            )
        else:
            # Sequential processing as fallback
            res = []
            for idx, chunk in enumerate(chunks):
                chunk_result = await process_chunk(
                    url=url,
                    chunk=chunk,
                    chunk_number=idx,
                    source=source,
                    async_supabase_client=supabase_client,
                    async_openai_client=async_openai_client,
                    database_table_name=database_table_name,
                    export_folder=export_folder,
                    debug_prn=debug_prn,
                    is_replace_llm_metadata=is_replace_llm_metadata,
                )
                if chunk_result:
                    res.append(chunk_result)
    except Exception as e:
        error_msg = f"Error processing chunks from ResponseGetDataCrawler: {str(e)}"
        logger.error(error_msg)
        return []

    if debug_prn:
        logger.info(f"Completed processing ResponseGetDataCrawler")

    return res


# %% ../../nbs/implementations/scrape_urls.ipynb 8
async def process_urls(
    urls: List[str],
    source: str,
    export_folder: str = "./export",
    database_table_name: str = "site_pages",
    max_conccurent_requests: int = 5,
    debug_prn: bool = False,
    browser_config: crawler_routes.BrowserConfig = None,
    crawler_config: crawler_routes.CrawlerRunConfig = None,
    is_replace_llm_metadata: bool = False,
    async_openai_client=None,
    async_supabase_client=None,
):
    """
    Process multiple URLs in parallel.
    
    Args:
        urls (List[str]): List of URLs to process
        source (str): The source identifier
        export_folder (str): The folder to export to
        database_table_name (str): The database table to store chunks in
        max_conccurent_requests (int): Maximum number of concurrent requests
        debug_prn (bool): Whether to print debug info
        browser_config: The browser configuration
        crawler_config: The crawler configuration
        is_replace_llm_metadata (bool): Whether to replace existing metadata
        async_openai_client: The OpenAI client
        async_supabase_client: The Supabase client
        
    Returns:
        list: The results of processing each URL
    """
    if not urls:
        logger.warning("No URLs found to crawl")
        return []

    # Filter out None values
    valid_urls = [url for url in urls if url]
    
    if not valid_urls:
        logger.warning("No valid URLs found to crawl")
        return []
        
    # Create export folder if needed
    os.makedirs(export_folder, exist_ok=True)
    
    # Save URLs to file if utils.files is available
    urls_path = f"{export_folder}/urls/{source}.txt"
    try:
        if amfi and hasattr(amfi, 'upsert_folder'):
            amfi.upsert_folder(urls_path)
            
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(urls_path), exist_ok=True)
            
            with open(urls_path, "w+", encoding="utf-8") as f:
                f.write("\n".join(valid_urls))
                
            if debug_prn:
                logger.info(f"Saved {len(valid_urls)} URLs to {urls_path}")
    except Exception as e:
        error_msg = f"Error saving URLs to file: {str(e)}"
        logger.error(error_msg)

    # Process URLs in parallel or sequentially
    try:
        if amce and hasattr(amce, 'gather_with_concurrency'):
            res = await amce.gather_with_concurrency(
                *[
                    process_url(
                        url=url,
                        source=source,
                        debug_prn=debug_prn,
                        browser_config=browser_config,
                        export_folder=export_folder,
                        database_table_name=database_table_name,
                        is_replace_llm_metadata=is_replace_llm_metadata,
                        crawler_config=crawler_config,
                        async_openai_client=async_openai_client,
                        async_supabase_client=async_supabase_client
                    ) for url in valid_urls
                ],
                n=max_conccurent_requests,
            )
        else:
            # Sequential processing as fallback
            res = []
            for url in valid_urls:
                result = await process_url(
                    url=url,
                    source=source,
                    debug_prn=debug_prn,
                    browser_config=browser_config,
                    export_folder=export_folder,
                    database_table_name=database_table_name,
                    is_replace_llm_metadata=is_replace_llm_metadata,
                    crawler_config=crawler_config,
                    async_openai_client=async_openai_client,
                    async_supabase_client=async_supabase_client
                )
                if result:
                    res.append(result)
    except Exception as e:
        error_msg = f"Error processing URLs: {str(e)}"
        logger.error(error_msg)
        return []

    if debug_prn:
        logger.info(f"Completed processing {len(valid_urls)} URLs")

    return res
