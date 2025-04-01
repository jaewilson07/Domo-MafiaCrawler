# Project Dependencies

## Core Dependencies

- Flask: Web framework for the user interface
- gunicorn: WSGI server for running the web application

## Crawler Enhancements (Optional but Recommended)

- requests: For making HTTP requests
- beautifulsoup4: For parsing HTML
- trafilatura: For improved content extraction

## Database Integrations (Optional)

- supabase: For storing and retrieving crawled data
- python-frontmatter: For parsing frontmatter in markdown files

## Installation

To install all dependencies:

```bash
pip install flask gunicorn requests beautifulsoup4 trafilatura supabase python-frontmatter
```

Or to install only essential dependencies:

```bash
pip install flask gunicorn
```