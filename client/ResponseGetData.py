"""
Response data handling classes for various API integrations.
Provides a consistent interface for different response types.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, TypeVar, Union
from dataclasses import dataclass, field

# Type aliases for library types that might not be available at runtime
# This prevents import errors if the libraries aren't installed
AsyncSlackApp = Any  # from slack_bolt.async_app import AsyncApp
AsyncSlackResponse = Any  # from slack_sdk.web.async_client import AsyncSlackResponse

# Generic type for the response return type
T = TypeVar('T', bound='ResponseGetData')


@dataclass
class ResponseGetData(ABC):
    """
    Abstract base class for standardized API response handling.
    
    Attributes:
        is_success: Whether the API request was successful
        status: HTTP status code or equivalent
        response: The response data payload
    """
    is_success: bool
    status: int
    response: Any

    @classmethod
    @abstractmethod
    def from_res(cls: type[T], res: Any, **kwargs) -> T:
        """
        Create a response object from the raw API response.
        
        Args:
            res: The raw response from the API
            **kwargs: Additional parameters specific to each implementation
            
        Returns:
            An instance of the response class
        """
        pass


@dataclass
class ResponseGetDataOpenAi(ResponseGetData):
    """
    Response handler for OpenAI API responses.
    
    Additional Attributes:
        raw: The raw response object for debugging
    """
    raw: Any = field(default=None, repr=False)

    @classmethod
    def from_res(cls, res: Any, **kwargs) -> 'ResponseGetDataOpenAi':
        """
        Create response object from OpenAI API response.
        
        Args:
            res: OpenAI API response object
            **kwargs: Additional parameters (unused)
            
        Returns:
            Standardized response object with OpenAI data
        """
        try:
            return cls(is_success=True,
                       status=200,
                       response=getattr(res, 'choices', []),
                       raw=res)
        except Exception as e:
            return cls(is_success=False,
                       status=500,
                       response=f"Error processing OpenAI response: {str(e)}",
                       raw=res)


@dataclass
class ResponseGetDataCrawler(ResponseGetData):
    """
    Response handler for web crawler results.
    
    Additional Attributes:
        url: The URL that was crawled
        html: Raw HTML content
        links: List of links extracted from the page
        markdown: Markdown representation of the page content
        raw: The raw crawler response object
    """
    source: str = ""
    url: str = ""
    html: Any = field(default=None, repr=False)
    links: List[Dict] = field(default_factory=list, repr=False)
    markdown: Any = field(default=None, repr=False)
    raw: Any = field(default=None, repr=False)

    @classmethod
    def from_res(cls, res: Any, **kwargs) -> 'ResponseGetDataCrawler':
        """
        Create response object from crawler results.
        
        Args:
            res: Crawler result object or list of results
            **kwargs: Additional parameters (unused)
            
        Returns:
            Standardized response object with crawled data
        """

        try:
            # Make sure res is properly formatted
            if not res:
                return cls(is_success=False,
                           status=400,
                           response="No crawler results received",
                           url="")

            # Handle both single result and list of results
            result = res[0] if isinstance(res, (list, tuple)) else res

            return cls(
                source=getattr(result, 'session_id', ''),
                is_success=getattr(result, 'success', False),
                status=getattr(result, 'status_code', 200),
                response=getattr(result, 'cleaned_html', ""),
                url=getattr(result, 'url', ""),
                html=getattr(result, 'html', None),
                links=getattr(result, 'links', []),
                markdown=getattr(result, 'markdown', None),
                raw=res,
            )
        except Exception as e:
            return cls(is_success=False,
                       status=500,
                       response=f"Error processing crawler response: {str(e)}",
                       url=getattr(res, 'url', "") if res else "",
                       raw=res)


@dataclass
class ResponseGetDataSlack(ResponseGetData):
    """
    Response handler for Slack API responses.
    
    Additional Attributes:
        channel_id: Slack channel ID
        message_id: Slack message timestamp
        app: Reference to the Slack app instance
    """
    channel_id: Optional[str] = None
    message_id: Optional[float] = None
    app: Optional[AsyncSlackApp] = field(repr=False, default=None)

    @classmethod
    def from_res(cls,
                 res: AsyncSlackResponse,
                 async_app: Optional[AsyncSlackApp] = None,
                 **kwargs) -> 'ResponseGetDataSlack':
        """
        Create response object from Slack API response.
        
        Args:
            res: Slack API response object
            async_app: Slack app instance
            **kwargs: Additional parameters to include in the response
            
        Returns:
            Standardized response object with Slack data
        """
        try:
            return cls(is_success=res.get("ok", False),
                       response=getattr(res, 'data', res),
                       status=getattr(res, 'status_code', 200),
                       app=async_app,
                       **kwargs)
        except Exception as e:
            return cls(is_success=False,
                       status=500,
                       response=f"Error processing Slack response: {str(e)}",
                       app=async_app)


@dataclass
class ResponseGetDataSupabase(ResponseGetData):
    """
    Response handler for Supabase API responses.
    
    Additional Attributes:
        raw: The raw Supabase response object
    """
    raw: Any = field(repr=False, default=None)

    @classmethod
    def from_res(cls, res: Any, **kwargs) -> 'ResponseGetDataSupabase':
        """
        Create response object from Supabase API response.
        
        Args:
            res: Supabase response object
            **kwargs: Additional parameters (unused)
            
        Returns:
            Standardized response object with Supabase data
        """
        try:
            is_success = False

            if hasattr(res, 'data') and res.data:
                is_success = True

            return cls(is_success=is_success,
                       response=getattr(res, 'data', None),
                       status=200 if is_success else 400,
                       raw=res)
        except Exception as e:
            return cls(
                is_success=False,
                status=500,
                response=f"Error processing Supabase response: {str(e)}",
                raw=res)
