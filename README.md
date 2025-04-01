# Web Crawler Tool

A flexible Python web crawling tool that provides powerful and efficient website data extraction capabilities. This project is designed for developers and data enthusiasts who need to extract and process web content programmatically.

## Features

- Command-line interface for easy website crawling
- Web interface for interactive use
- Multiple output formats (JSON, Markdown, HTML, Text)
- Advanced error handling and graceful fallbacks
- Configurable crawl depth and page limits
- Content extraction with different levels of detail
- Minimal dependencies with gradual enhancement

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Optional enhanced dependencies:

```bash
pip install requests beautifulsoup4 trafilatura
```

## Usage

### Command Line Interface

Basic usage:

```bash
python crawler.py --url https://example.com --depth 2 --output results.json
```

Advanced options:

```bash
python crawler.py --url https://example.com \
                 --depth 3 \
                 --max-pages 50 \
                 --format markdown \
                 --output results.md \
                 --user-agent "CustomBot/1.0" \
                 --extract-images \
                 --extract-links \
                 --delay 1.5
```

For all available options:

```bash
python crawler.py --help
```

### Web Interface

Start the web interface:

```bash
python main.py
```

Then open your browser to http://localhost:5000

## API Integration

The project includes a Supabase integration module that allows for storing and retrieving crawled data in a structured database.

```python
from routes.supabase import get_document_from_supabase, store_data_in_supabase_table

# Retrieve and store data
await store_data_in_supabase_table(supabase_client, "documents", crawled_data)
documents = await get_document_from_supabase(supabase_client, "https://example.com")
```

## Architecture

The project is organized into several modules:

- `crawler.py`: Core crawling functionality
- `main.py`: Web interface using Flask
- `routes/`: API route handlers 
- `utils/`: Utility functions
- `client/`: Client-side error handling and data models

## License

This project is available under the MIT License.