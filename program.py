"""
Configuration for crawler and database connections.

This module handles the initialization of browser configurations
and database connections used by the crawler.
"""

# Standard library imports
import os
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Try to import third-party dependencies, but handle import errors gracefully
try:
    # Third-party imports
    from crawl4ai import BrowserConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    # Create a placeholder class if crawl4ai is not available
    class BrowserConfig:
        """
        Placeholder BrowserConfig class when crawl4ai is not installed.
        """
        def __init__(self, browser_type=None, headless=None, verbose=None, extra_args=None, **kwargs):
            self.browser_type = browser_type
            self.headless = headless
            self.verbose = verbose
            self.extra_args = extra_args or []
            self.__dict__.update(kwargs)
    
    CRAWL4AI_AVAILABLE = False
    logger.warning("crawl4ai module is not installed. Browser functionality will be limited.")

try:
    # Third-party imports
    from supabase import AsyncClient as Async_SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    # Create a placeholder class if supabase is not available
    class Async_SupabaseClient:
        """
        Placeholder Async_SupabaseClient class when supabase is not installed.
        """
        def __init__(self, supabase_url=None, supabase_key=None, **kwargs):
            self.supabase_url = supabase_url
            self.supabase_key = supabase_key
            self.__dict__.update(kwargs)
    
    SUPABASE_AVAILABLE = False
    logger.warning("supabase module is not installed. Database functionality will be limited.")

# Create browser configuration
browser_config = BrowserConfig(
    browser_type="chromium",
    headless=True,
    verbose=True,
    extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
)

# Create Supabase client if credentials are available
async_supabase_client: Optional[Async_SupabaseClient] = None

if SUPABASE_AVAILABLE:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if supabase_url and supabase_key:
        try:
            async_supabase_client = Async_SupabaseClient(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
    else:
        logger.warning("Supabase credentials not found in environment variables")
