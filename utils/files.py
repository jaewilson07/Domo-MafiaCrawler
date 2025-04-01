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
from typing import Any, Dict, Tuple, Union, Optional

# Configure logging at module level
logger = logging.getLogger(__name__)

# Try to import third-party dependencies safely
# This allows the module to be imported even if frontmatter is not installed
try:
    # Third-party imports
    # python-frontmatter package provides tools for working with YAML frontmatter in text files
    import frontmatter
    FRONTMATTER_AVAILABLE = True
except ImportError:
    FRONTMATTER_AVAILABLE = False
    # Create a robust placeholder if frontmatter is not available
    class MockFrontmatter:
        """
        Fallback implementation when python-frontmatter package is not available.
        
        This class provides a minimal implementation of the frontmatter reader
        to ensure graceful degradation when the package is not installed.
        
        Note:
            For full frontmatter functionality, install python-frontmatter:
            pip install python-frontmatter
        """
        @staticmethod
        def read_file(file_path):
            """
            Read a file and return content without parsing frontmatter.
            
            This is a simplified version that doesn't actually parse frontmatter
            but returns the whole file as the body with empty attributes.
            
            Args:
                file_path: Path to the file to read
                
            Returns:
                Dict with 'body' containing file content and empty 'attributes'
            """
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic check for frontmatter delimiters
                if content.startswith('---'):
                    logger.warning(
                        f"File {file_path} appears to contain frontmatter, but python-frontmatter "
                        "package is not installed. Frontmatter will not be parsed correctly."
                    )
                    
                return {"body": content, "attributes": {}}
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {str(e)}")
                return {"body": "", "attributes": {}}
            
        def dumps(self, data):
            """
            Mock method for serializing frontmatter.
            
            Args:
                data: A dict with 'content' and 'metadata' keys
                
            Returns:
                String with frontmatter format
            """
            logger.warning("python-frontmatter not installed, formatting may be incomplete")
            metadata = data.get('metadata', {})
            content = data.get('content', '')
            
            if not metadata:
                return content
                
            # Basic frontmatter formatting
            try:
                import yaml
                yaml_str = yaml.dump(metadata, default_flow_style=False)
                return f"---\n{yaml_str}---\n\n{content}"
            except ImportError:
                # Even more basic fallback if yaml is not available
                meta_str = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
                return f"---\n{meta_str}\n---\n\n{content}"
    
    # Use the mock implementation
    Frontmatter = MockFrontmatter()

# This logger has already been defined at the top of the module
# No need to redefine it here


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
        if FRONTMATTER_AVAILABLE:
            data = frontmatter.parse(file_path)
        else:
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


def ensure_template_files_exist():
    """
    Creates the necessary template files for the web application if they don't exist.
    This ensures the Flask app can run without errors even on the first execution.
    
    Creates:
        - index.html: Home page with crawler form
        - crawler.html: Crawler status page
        - about.html: About page
        - error.html: Error display page
    """
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    
    # Ensure directories exist
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    # Create CSS file in static directory
    css_path = os.path.join(static_dir, "style.css")
    if not os.path.exists(css_path):
        with open(css_path, "w", encoding="utf-8") as f:
            f.write("""
/* Basic styling for the crawler app */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    margin: 0;
    padding: 0;
    background-color: #f8f9fa;
}

.container {
    width: 80%;
    margin: auto;
    overflow: hidden;
    padding: 20px;
}

header {
    background: #343a40;
    color: #fff;
    padding: 20px 0;
    margin-bottom: 30px;
}

header h1 {
    margin: 0;
    padding-left: 20px;
}

nav {
    background: #495057;
    color: #fff;
    padding: 10px 0;
}

nav ul {
    padding: 0;
    list-style: none;
    display: flex;
}

nav li {
    padding: 0 20px;
}

nav a {
    color: #fff;
    text-decoration: none;
}

nav a:hover {
    color: #ccc;
}

.main-content {
    background: #fff;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

form {
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="text"], 
input[type="url"], 
textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

button {
    display: inline-block;
    background: #343a40;
    color: #fff;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background: #495057;
}

.alert {
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 4px;
}

.alert-success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.alert-error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.footer {
    background: #343a40;
    color: #fff;
    text-align: center;
    padding: 10px;
    margin-top: 30px;
}
            """)
    
    # Create index.html template
    index_path = os.path.join(templates_dir, "index.html")
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Crawler Tool</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <div class="container">
            <h1>Web Crawler Tool</h1>
        </div>
    </header>
    
    <nav>
        <div class="container">
            <ul>
                <li><a href="{{ url_for('index') }}">Home</a></li>
                <li><a href="{{ url_for('crawler') }}">Crawler Status</a></li>
                <li><a href="{{ url_for('about') }}">About</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
        <div class="main-content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <h2>Start a New Crawl</h2>
            <form action="{{ url_for('crawler') }}" method="post">
                <div class="form-group">
                    <label for="url">URL to Crawl:</label>
                    <input type="url" id="url" name="url" required 
                           placeholder="https://example.com">
                </div>
                
                <div class="form-group">
                    <label for="session_id">Session ID (optional):</label>
                    <input type="text" id="session_id" name="session_id" 
                           placeholder="custom_session_1">
                </div>
                
                <button type="submit">Start Crawling</button>
            </form>
        </div>
    </div>
    
    <footer class="footer">
        <div class="container">
            <p>&copy; 2025 Web Crawler Tool</p>
        </div>
    </footer>
</body>
</html>""")
    
    # Create crawler.html template
    crawler_path = os.path.join(templates_dir, "crawler.html")
    if not os.path.exists(crawler_path):
        with open(crawler_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crawler Status</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <div class="container">
            <h1>Crawler Status</h1>
        </div>
    </header>
    
    <nav>
        <div class="container">
            <ul>
                <li><a href="{{ url_for('index') }}">Home</a></li>
                <li><a href="{{ url_for('crawler') }}">Crawler Status</a></li>
                <li><a href="{{ url_for('about') }}">About</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
        <div class="main-content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <h2>Recent Crawl Jobs</h2>
            
            <div class="job-list">
                <p>No recent crawl jobs available.</p>
            </div>
            
            <p><a href="{{ url_for('index') }}">Start a new crawl</a></p>
        </div>
    </div>
    
    <footer class="footer">
        <div class="container">
            <p>&copy; 2025 Web Crawler Tool</p>
        </div>
    </footer>
</body>
</html>""")
    
    # Create about.html template
    about_path = os.path.join(templates_dir, "about.html")
    if not os.path.exists(about_path):
        with open(about_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About Web Crawler</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <div class="container">
            <h1>About Web Crawler Tool</h1>
        </div>
    </header>
    
    <nav>
        <div class="container">
            <ul>
                <li><a href="{{ url_for('index') }}">Home</a></li>
                <li><a href="{{ url_for('crawler') }}">Crawler Status</a></li>
                <li><a href="{{ url_for('about') }}">About</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
        <div class="main-content">
            <h2>Web Crawler Tool</h2>
            
            <p>This web crawler tool allows you to extract content from websites for analysis and data extraction.</p>
            
            <h3>Features:</h3>
            <ul>
                <li>Simple web interface for configuring crawl operations</li>
                <li>Extracts text content in a format readable by humans and AI</li>
                <li>Supports advanced crawling options</li>
                <li>RESTful API for integration with other applications</li>
            </ul>
            
            <h3>Technologies:</h3>
            <ul>
                <li>Flask: Web framework</li>
                <li>Trafilatura: Content extraction</li>
                <li>BeautifulSoup: HTML parsing</li>
                <li>Requests: HTTP handling</li>
            </ul>
        </div>
    </div>
    
    <footer class="footer">
        <div class="container">
            <p>&copy; 2025 Web Crawler Tool</p>
        </div>
    </footer>
</body>
</html>""")
    
    # Create error.html template
    error_path = os.path.join(templates_dir, "error.html")
    if not os.path.exists(error_path):
        with open(error_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <div class="container">
            <h1>Error</h1>
        </div>
    </header>
    
    <nav>
        <div class="container">
            <ul>
                <li><a href="{{ url_for('index') }}">Home</a></li>
                <li><a href="{{ url_for('crawler') }}">Crawler Status</a></li>
                <li><a href="{{ url_for('about') }}">About</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
        <div class="main-content">
            <div class="alert alert-error">
                <h2>An Error Occurred</h2>
                <p>{{ error }}</p>
            </div>
            
            <p><a href="{{ url_for('index') }}">Return to home page</a></p>
        </div>
    </div>
    
    <footer class="footer">
        <div class="container">
            <p>&copy; 2025 Web Crawler Tool</p>
        </div>
    </footer>
</body>
</html>""")
    
    logger.info("Template files created successfully")


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
