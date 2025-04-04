import re
import logging
import unicodedata
from urllib.parse import urlparse
from typing import List, Any, Optional
import json

# Configure logger
logger = logging.getLogger(__name__)


def extract_domain(url: str) -> str:
    """Extract the domain from a given URL."""

    parsed_url = urlparse(url)
    return str(parsed_url.netloc)


def keep_alphanumeric(text: str) -> str:
    """
    Remove all non-alphanumeric characters from a string.

    This function preserves alphanumeric characters, underscores,
    hyphens, and whitespace while removing all other characters.

    Args:
        text: The string to sanitize

    Returns:
        A sanitized string containing only alphanumeric characters,
        underscores, hyphens, and whitespace

    Examples:
        >>> keep_alphanumeric("Hello, World!")
        "Hello World"
        >>> keep_alphanumeric("File (1).txt")
        "File 1txt"
    """
    if not text:
        return ""

    pattern = r"[^0-9a-zA-Z_\-\s]+"
    return re.sub(pattern, "", text)


def to_snake_case(text: str) -> str:
    """
    Convert a string to snake_case format.

    This function replaces spaces with underscores and converts
    the entire string to lowercase.

    Args:
        text: The string to convert

    Returns:
        A snake_case formatted string

    Examples:
        >>> to_snake_case("Hello World")
        "hello_world"
        >>> to_snake_case("User Name")
        "user_name"
    """
    if not text:
        return ""

    return text.replace(" ", "_").lower()


def remove_accents(text: str) -> str:
    """
    Remove accents and diacritical marks from a string.

    This function normalizes the string using NFD normalization
    and then removes all diacritical marks (category Mn in Unicode).

    Args:
        text: The string to process

    Returns:
        The string with all accents and diacritical marks removed

    Examples:
        >>> remove_accents("résumé")
        "resume"
        >>> remove_accents("café")
        "cafe"
    """
    if not text:
        return ""

    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def create_safe_file_name(text: str) -> str:
    """
    Convert a string to a clean, safe filename.

    This function applies a series of transformations to create a filename
    that is safe to use across operating systems by removing accents,
    converting to snake_case, and keeping only alphanumeric characters.

    Args:
        text: The string to convert

    Returns:
        A sanitized string suitable for use as a filename

    Examples:
        >>> create_safe_file_name("Hello, World!")
        "hello_world"
        >>> create_safe_file_name("résumé.doc")
        "resume_doc"
    """
    if not text:
        return ""

    return keep_alphanumeric(to_snake_case(remove_accents(text)))


def sanitize_frontmatter_value(value: Any) -> Optional[str]:
    """
    Replace unsafe characters in values for YAML frontmatter with underscores.

    Args:
        value: The value to sanitize.

    Returns:
        A safe string representation of the value.
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)  # Serialize complex types as JSON
    if isinstance(value, str):
        # Replace unsafe characters with underscores
        unsafe_chars = ["\n", "\r", ":", "#"]
        for char in unsafe_chars:
            value = value.replace(char, "_")
        return value.strip()
    return str(value)  # Convert other types to string


def convert_url_to_file_name(url: str) -> str:
    """
    Convert a URL to a safe file path while preserving structure.

    This function extracts the domain and path from a URL and converts
    them to a safe file path format, preserving the hierarchical structure
    but replacing unsafe characters.

    Args:
        url: The URL to convert

    Returns:
        A sanitized string suitable for use as a file path

    Examples:
        >>> convert_url_to_file_name("https://example.com/page/1")
        "example_com/page_1"
        >>> convert_url_to_file_name("https://www.site.org/")
        "site_org/index"
    """
    if not url:
        return ""

    try:
        # Parse the URL into components
        parsed_url = urlparse(url)

        # Extract and clean the domain (netloc)
        domain = parsed_url.netloc.replace("www.", "").replace(".", "_")

        # Extract and clean the path
        path = parsed_url.path[1:].replace("/", "_")

        # Use 'index' for empty paths (root of domain)
        if not path:
            path = "index"

        logger.debug(f"Processing URL path: {path}")

        # Apply safe filename conversion to both parts
        clean_parts: List[str] = [create_safe_file_name(val) for val in [domain, path]]

        # Join the parts with a directory separator
        result_path = "/".join(clean_parts)

        # Remove leading and trailing underscores
        if result_path.startswith("_"):
            result_path = result_path[1:]

        if result_path.endswith("_"):
            result_path = result_path[:-1]

        return result_path

    except Exception as e:
        logger.error(f"Error converting URL to filename: {e}")
        # Fallback to a simple hash of the URL if parsing fails
        return create_safe_file_name(url)
