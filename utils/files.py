"""
File Utility Module

This module provides utility functions for file operations, including 
creating directories, reading/writing files, and handling file formats.

The module focuses on robust error handling and consistent file operations 
to minimize errors when manipulating files and directories.
"""

import os
import json
import shutil
import logging
from typing import Any, Dict, Tuple, Union, Optional

# Try to import frontmatter safely
# This allows the module to be imported even if frontmatter is not installed
try:
    from frontmatter import Frontmatter
    FRONTMATTER_AVAILABLE = True
except ImportError:
    # Create a simple placeholder if frontmatter is not available
    class MockFrontmatter:
        @staticmethod
        def read_file(file_path):
            """Simple frontmatter reader that returns empty data if not available."""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"body": content, "attributes": {}}
            except Exception as e:
                logging.error(f"Error reading file {file_path}: {str(e)}")
                return {"body": "", "attributes": {}}
    
    Frontmatter = MockFrontmatter()
    FRONTMATTER_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class FileError(Exception):
    """Custom exception for file operations."""
    def __init__(self, message: str, path: Optional[str] = None, exception: Optional[Exception] = None):
        self.path = path
        self.exception = exception
        if path:
            message = f"{message} (Path: {path})"
        if exception:
            message = f"{message} - {str(exception)}"
        super().__init__(message)


def upsert_folder(folder_path: str, debug_prn: bool = False, replace_folder: bool = False) -> str:
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
        if replace_folder and os.path.exists(abs_path) and os.path.isdir(abs_path):
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
        raise FileError("Failed to create directory", path=folder_path, exception=e)


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
    if not FRONTMATTER_AVAILABLE:
        logger.warning("frontmatter module is not installed. Limited functionality available.")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileError(f"File does not exist", path=file_path)
            
        # Read file with frontmatter
        data = Frontmatter.read_file(file_path)
        
        # Ensure body and attributes are present
        body = data.get("body", "")
        attributes = data.get("attributes", {})
        
        return body, attributes
        
    except FileError:
        # Re-raise FileError exceptions
        raise
    except Exception as e:
        logger.error(f"Error reading markdown file {file_path}: {str(e)}")
        raise FileError("Failed to read markdown file", path=file_path, exception=e)


def get_file_extension(path: str) -> str:
    """
    Get the extension of a file path.
    
    Args:
        path (str): File path
        
    Returns:
        str: File extension with dot (e.g., '.json')
    """
    _, extension = os.path.splitext(path)
    return extension


def change_file_extension(file_path: str, extension: str) -> str:
    """
    Returns a new file path with the changed extension.
    Unlike the original version, this doesn't rename the file, it just returns the new path.
    
    Args:
        file_path (str): The path to the file.
        extension (str): The new extension (with or without dot).
        
    Returns:
        str: New file path with the changed extension.
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
    
    Args:
        output_path (str): Path where the file should be saved.
        data (Any): The data to save (string, bytes, dict, etc.).
        is_binary (bool, optional): Force binary mode writing.
        encoding (str, optional): Character encoding for text files.
        replace_folder (bool, optional): Replace existing folder if True.
        
    Returns:
        int: Number of bytes written
        
    Raises:
        FileError: If there's an error saving the file
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
                    logger.debug("Data not JSON serializable, writing as raw binary")
            
            # Standard binary write
            with open(output_path, "wb") as f:
                byte_count = f.write(data if isinstance(data, bytes) else str(data).encode(encoding))
                return byte_count
        
        # Handle text data
        logger.debug(f"Saving text data to {output_path}")
        with open(output_path, "w", encoding=encoding) as f:
            text_data = str(data)
            f.write(text_data)
            return len(text_data.encode(encoding))  # Return byte count
            
    except Exception as e:
        logger.error(f"Error saving data to {output_path}: {str(e)}")
        raise FileError("Failed to save data to disk", path=output_path, exception=e)
