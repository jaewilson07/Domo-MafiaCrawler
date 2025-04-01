# Third-party imports
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False


def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    The results is not directly readable, better to be summarized by LLM before consume
    by the user.

    Some common website to crawl information from:
    MLB scores: https://www.mlb.com/scores/YYYY-MM-DD
    
    Args:
        url (str): The URL of the website to extract content from.
        
    Returns:
        str: The extracted text content from the website.
        
    Raises:
        ImportError: If trafilatura is not installed.
        ValueError: If the URL is invalid or cannot be accessed.
    """
    if not TRAFILATURA_AVAILABLE:
        raise ImportError(
            "trafilatura is not installed. Install it with: pip install trafilatura"
        )
        
    # Send a request to the website
    downloaded = trafilatura.fetch_url(url)
    
    if downloaded is None:
        raise ValueError(f"Could not download content from URL: {url}")
        
    text = trafilatura.extract(downloaded)
    
    if text is None:
        return "No content could be extracted from the webpage."
        
    return text