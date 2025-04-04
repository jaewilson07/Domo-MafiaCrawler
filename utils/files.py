"""
File Utility Module

This module provides utility functions for file operations, including 
creating directories, reading/writing files, and handling file formats.

The module focuses on robust error handling and consistent file operations 
to minimize errors when manipulating files and directories.

Core Functions:
- upsert_folder: Create or update a directory, optionally replacing existing folders
- read_md_from_disk: Read a markdown file with frontmatter support
- save_to_disk: Save data to disk with intelligent handling of different data types
- get_file_extension: Extract file extension from a path
- change_file_extension: Get a new file path with a changed extension

Error Handling:
All functions in this module use consistent error handling via the FileError class,
which provides detailed error messages including the file path and original exception.

Usage Examples:
```python
# Create a directory safely
try:
    folder_path = upsert_folder("./output/data")
    print(f"Directory created at: {folder_path}")
except FileError as e:
    print(f"Error: {str(e)}")

# Save data to disk with automatic format detection
data = {"title": "Example", "content": "This is example content"}
try:
    bytes_written = save_to_disk("./output/example.json", data)
    print(f"Saved {bytes_written} bytes to disk")
except FileError as e:
    print(f"Error saving data: {str(e)}")

# Read a markdown file with frontmatter
try:
    content, metadata = read_md_from_disk("./docs/example.md")
    print(f"Title: {metadata.get('title', 'Untitled')}")
    print(f"Content length: {len(content)} characters")
except FileError as e:
    print(f"Error reading file: {str(e)}")
```
"""

# Standard library imports
import os
import json
import shutil
import logging
from typing import Any, Dict, Tuple, Optional
import frontmatter

# Configure logging at module level
logger = logging.getLogger(__name__)


class FileError(Exception):
    """Custom exception for file operations."""

    def __init__(self,
                 message: str,
                 path: Optional[str] = None,
                 exception: Optional[Exception] = None):
        self.path = path
        self.exception = exception
        if path:
            message = f"{message} (Path: {path})"
        if exception:
            message = f"{message} - {str(exception)}"
        super().__init__(message)


def upsert_folder(folder_path: str,
                  debug_prn: bool = False,
                  replace_folder: bool = False) -> str:
    """
    Ensures a folder exists, optionally replacing it.
    
    Args:
        folder_path (str): Path to the file or folder to create.
                           If a file path is provided, its directory will be created.
        debug_prn (bool, optional): Print debug information if True.
        replace_folder (bool, optional): Remove existing folder if True.
        
    Returns:
        str: Absolute path to the created directory
        
    Raises:
        FileError: If there's an error creating the directory
    """
    try:
        # Extract directory path if folder_path includes a filename
        folder_path = os.path.dirname(folder_path)

        # Ensure folder_path is not empty (handling current directory case)
        if not folder_path:
            folder_path = "."

        # Get absolute path for consistent operations and logging
        abs_path = os.path.abspath(folder_path)

        # Replace existing folder if requested
        if replace_folder and os.path.exists(abs_path) and os.path.isdir(
                abs_path):
            if debug_prn:
                logger.info(f"Removing existing folder: {abs_path}")
            shutil.rmtree(abs_path)

        # Print debug information if requested
        if debug_prn:
            logger.info({
                "upsert_folder": abs_path,
                "exists": os.path.exists(abs_path),
            })

        # Create directory if it doesn't exist
        if not os.path.exists(abs_path):
            os.makedirs(abs_path)
            logger.debug(f"Created directory: {abs_path}")

        return abs_path

    except Exception as e:
        logger.error(f"Error creating directory {folder_path}: {str(e)}")
        raise FileError("Failed to create directory",
                        path=folder_path,
                        exception=e)


def read_md_from_disk(file_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Reads a markdown file with frontmatter.
    
    Args:
        file_path (str): Path to the markdown file.
        
    Returns:
        Tuple[str, Dict[str, Any]]: Tuple containing (content, frontmatter attributes)
        
    Raises:
        FileError: If there's an error reading the file or if frontmatter isn't available
    """

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileError(f"File does not exist", path=file_path)

        # Read file with frontmatter
        data = frontmatter.Frontmatter.read_file(file_path)

        return data['body'], data.get('attributes', {})

    except Exception as e:
        logger.error(f"Error reading markdown file {file_path}: {str(e)}")
        raise FileError("Failed to read markdown file",
                        path=file_path,
                        exception=e) from e


def get_file_extension(path: str) -> str:
    """
    Get the extension of a file path.
    
    This function extracts the file extension from a path, including the
    dot separator. If the file has no extension, an empty string is returned.
    
    Args:
        path (str): File path to extract extension from
        
    Returns:
        str: File extension with dot (e.g., '.json', '.txt', '.md')
            or empty string if no extension exists
            
    Examples:
        >>> get_file_extension('data/file.json')
        '.json'
        >>> get_file_extension('file.tar.gz')
        '.gz'
        >>> get_file_extension('README')
        ''
    """
    _, extension = os.path.splitext(path)
    return extension


def change_file_extension(file_path: str, extension: str) -> str:
    """
    Returns a new file path with the changed extension.
    
    This function creates a new file path by replacing the extension
    of the original path. It does not rename the file on disk but
    returns a new path string. The function handles paths with or
    without an existing extension.
    
    Args:
        file_path (str): The path to the file
        extension (str): The new extension (with or without dot)
        
    Returns:
        str: New file path with the changed extension
        
    Examples:
        >>> change_file_extension('data/file.txt', '.json')
        'data/file.json'
        >>> change_file_extension('data/file.txt', 'json')
        'data/file.json'
        >>> change_file_extension('README', '.md')
        'README.md'
        >>> change_file_extension('archive.tar.gz', '.zip')
        'archive.tar.zip'
    """
    # Ensure extension starts with dot
    if not extension.startswith('.'):
        extension = "." + extension

    # Split path and create new path with new extension
    base_name, _ = os.path.splitext(file_path)
    new_file_path = base_name + extension

    return new_file_path


def save_to_disk(
    output_path: str,
    data: Any,
    is_binary: bool = False,
    encoding: str = "utf-8",
    replace_folder: bool = False,
) -> int:
    """
    Saves data to disk with intelligent handling of different data types.
    
    This versatile function automatically detects the data type and saves it
    in the appropriate format. It handles dictionaries (saved as JSON),
    binary data, and text data with specialized processing for each type.
    
    Features:
    - Automatic detection of data types and appropriate handling
    - Directory creation if needed
    - Proper encoding and formatting of data
    - Consistent error handling with detailed error messages
    - JSON auto-formatting for dictionary data
    
    Args:
        output_path (str): Path where the file should be saved
        data (Any): The data to save (string, bytes, dict, list, etc.)
        is_binary (bool, optional): Force binary mode writing even for text data
        encoding (str, optional): Character encoding for text files
        replace_folder (bool, optional): Replace existing folder if True
        
    Returns:
        int: Number of bytes written to the file
        
    Raises:
        FileError: If there's an error during any part of the save process
        
    Examples:
        >>> # Save a dictionary as JSON
        >>> data = {"name": "Example", "values": [1, 2, 3]}
        >>> save_to_disk("output/config.json", data)
        
        >>> # Save text content
        >>> text = "Hello, world!"
        >>> save_to_disk("output/hello.txt", text)
        
        >>> # Save binary data
        >>> binary_data = b"\\x00\\x01\\x02\\x03"
        >>> save_to_disk("output/data.bin", binary_data)
        
        >>> # Force binary mode for text
        >>> save_to_disk("output/encoded.bin", "Special text", is_binary=True)
    """
    try:
        # Ensure directory exists
        upsert_folder(output_path, replace_folder=replace_folder)

        # Handle dictionary data - save as JSON
        if isinstance(data, dict):
            json_path = change_file_extension(output_path, ".json")
            logger.debug(f"Saving dictionary as JSON to {json_path}")

            with open(json_path, "w", encoding=encoding) as f:
                json.dump(data, f, indent=4)
                return f.tell()  # Return file position as byte count

        # Handle binary data
        if is_binary or isinstance(data, bytes):
            logger.debug(f"Saving binary data to {output_path}")

            # Handle JSON serializable data in binary mode
            if not isinstance(data, bytes):
                try:
                    json_path = change_file_extension(output_path, ".json")
                    json_data = json.dumps(data).encode(encoding)

                    with open(json_path, "wb") as f:
                        f.write(json_data)
                        return len(json_data)

                except (TypeError, json.JSONDecodeError):
                    # Not JSON serializable, continue to standard binary write
                    logger.debug(
                        "Data not JSON serializable, writing as raw binary")

            # Standard binary write
            with open(output_path, "wb") as f:
                byte_count = f.write(data if isinstance(data, bytes) else str(
                    data).encode(encoding))
                return byte_count

        # Handle text data
        logger.debug(f"Saving text data to {output_path}")
        with open(output_path, "w", encoding=encoding) as f:
            text_data = str(data)
            f.write(text_data)
            return len(text_data.encode(encoding))  # Return byte count

    except Exception as e:
        logger.error(f"Error saving data to {output_path}: {str(e)}")
        raise FileError("Failed to save data to disk",
                        path=output_path,
                        exception=e)
