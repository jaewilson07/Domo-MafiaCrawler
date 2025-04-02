# Web Crawler Tool

A flexible Python web crawling tool that provides powerful and efficient website data extraction capabilities. This project is designed for developers and data enthusiasts who need to extract and process web content programmatically.

## Features

- Command-line interface for easy website crawling
- Web interface for configuration and monitoring
- Robust error handling with graceful fallbacks for missing dependencies
- Content extraction with different levels of detail
- Support for text extraction and summarization
- Optional OpenAI integration for enhanced content processing
- Metadata generation and embedding creation

## Installation

1. Clone this repository
2. Install dependencies:

```bash
# Create a Python virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install using pip
pip install -e .
```

### Dependencies

The project uses a tiered dependency approach:

- **Core dependencies**: Flask, Requests, Trafilatura, BeautifulSoup4
- **Optional enhancements**: python-frontmatter, OpenAI API
- **Database integration**: Flask-SQLAlchemy, Supabase (optional)

## Usage

### Command Line Interface

The crawler can be used directly from the command line:

```bash
# Basic usage
python routes/crawler.py --url https://example.com --output results.md

# Get help with all options
python routes/crawler.py --help
```

### Web Interface

Start the web interface for easier configuration:

```bash
# Start with Flask development server
python main.py

# OR use Gunicorn for production
gunicorn --bind 0.0.0.0:5000 main:app
```

Then open your browser to http://localhost:5000

### Python API

The crawler can also be used programmatically in your Python code:

```python
import web_scraper

# Extract text content from a website
content = web_scraper.get_website_text_content("https://example.com")
print(content)

# For more advanced usage with processing and metadata
from implementation.scraper import process_url

results = await process_url(
    url="https://example.com",
    source="my-crawler-session",
    export_folder="./output",
    database_table_name="crawled_pages"
)
```

## Architecture

The project is organized into several modules:

- `routes/crawler.py`: Command-line crawling interface
- `main.py`: Web interface using Flask
- `web_scraper.py`: Simple standalone text extraction
- `implementation/scraper.py`: Advanced processing pipeline
- `utils/`: Utility functions for chunking, file handling, etc.
- `client/`: Client-side error handling and data models

## Error Handling

The tool is designed to gracefully handle missing dependencies:

- Works with minimal dependencies if optional packages are not available
- Provides informative error messages and fallbacks
- Implements robust error recovery for network and parsing issues

## Dependencies Management

Dependencies are declared in `pyproject.toml` and include:

- Required dependencies for core functionality
- Optional dependencies for enhanced features
- Fallback mechanisms for when dependencies are missing

## License

This project is available under the MIT License.