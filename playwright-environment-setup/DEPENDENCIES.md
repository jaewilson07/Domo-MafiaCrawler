# Project Dependencies

## Web Interface Dependencies
- flask>=3.1.0: Web framework for the user interface
- gunicorn>=23.0.0: WSGI server for running the web application
- flask-sqlalchemy>=3.1.1: SQL database integration for Flask

## Core Crawler Dependencies
- requests>=2.32.3: For making HTTP requests
- beautifulsoup4>=4.13.3: For parsing HTML
- trafilatura>=2.0.0: For improved content extraction
- python-frontmatter>=1.1.0: For parsing frontmatter in markdown files
- crawl4ai>=0.5.0: For advanced web crawling capabilities

## Browser Automation Dependencies
- playwright>=1.42.0: For browser automation and headless browsing

### Browser Automation Setup Notes
Playwright requires specific system dependencies to run headless browsers. If you encounter errors with missing dependencies or GLIBC version mismatches, consider using one of these approaches:

1. **Docker container setup** (recommended for production):
   ```bash
   # Example Dockerfile
   FROM mcr.microsoft.com/playwright:v1.42.0-jammy
   
   # Add your project files
   COPY . /app
   WORKDIR /app
   
   # Install dependencies
   RUN pip install -e .
   ```

2. **Reuse Chromium installed in system**:
   ```python
   # Example code to use system-installed Chromium
   from playwright.sync_api import sync_playwright
   
   with sync_playwright() as p:
       browser = p.chromium.launch(
           executable_path="/usr/bin/chromium",
           args=["--no-sandbox"]
       )
       # Use browser...
   ```

3. **Use API-based approaches instead**:
   For environments where browser automation is challenging, consider:
   - Using HTTP client libraries like `requests` with `BeautifulSoup`
   - Using serverless browser services like Browserless.io

## Integration Dependencies
- openai>=1.70.0: For AI-powered text analysis and summarization
- psycopg2-binary>=2.9.10: PostgreSQL database adapter
- supabase>=2.15.0: For storing and retrieving crawled data
- email-validator>=2.2.0: For validating email addresses
- routes>=2.5.1: For URL routing and navigation

## Installation Methods

### Installing with pip

```bash
pip install flask gunicorn flask-sqlalchemy requests beautifulsoup4 trafilatura python-frontmatter crawl4ai playwright openai psycopg2-binary supabase email-validator routes
# Install Playwright browsers
python -m playwright install
```

### Installing with the project's pyproject.toml

```bash
# Install the project in development mode
pip install -e .
```

### Minimal Installation (Web Interface Only)

```bash
pip install flask gunicorn flask-sqlalchemy
```

### Basic Crawler Installation

```bash
pip install requests beautifulsoup4 trafilatura python-frontmatter
```

### Full Installation with Optional Dependencies

```bash
pip install flask gunicorn flask-sqlalchemy requests beautifulsoup4 trafilatura python-frontmatter crawl4ai playwright openai psycopg2-binary supabase email-validator routes

# Install Playwright browsers
python -m playwright install

# Development dependencies
pip install pytest black isort flake8
```