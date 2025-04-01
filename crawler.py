#!/usr/bin/env python3
"""
crawler.py - A lightweight web crawler with flexible output formats

This script provides a simple command-line interface to crawl websites.
It allows for configuration of crawling parameters and outputs results
in various structured formats. It uses standard Python libraries for
easy deployment without external dependencies.

Usage:
    python crawler.py --url URL [options]

Example:
    python crawler.py --url https://example.com --depth 2 --output results.json
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import re
import html.parser
import urllib.parse
import urllib.robotparser
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
import traceback
from urllib.request import Request, urlopen

# Try to import optional dependencies
try:
    import requests
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    # Use html.parser if BeautifulSoup is not available
    BEAUTIFULSOUP_AVAILABLE = False

# Try importing trafilatura for improved text extraction
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

try:
    from client.MafiaError import MafiaError, generate_error_message
except ImportError:
    # Create a simple implementation if MafiaError is not available
    def generate_error_message(message=None, exception=None):
        """Generate formatted error message."""
        parts = []
        if message:
            parts.append(f"Error: {message}")
        if exception:
            parts.append(f"Exception: {type(exception).__name__}: {str(exception)}")
            if hasattr(exception, "__traceback__"):
                parts.append(f"Traceback: {traceback.format_exc()}")
        return " | ".join(parts) if parts else "Unknown error"

    class MafiaError(Exception):
        """Simple error class."""
        def __init__(self, message=None, exception=None):
            self.message = message
            self.exception = exception
            super().__init__(generate_error_message(message, exception))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("web_crawler")


class HTMLParserWithLinks(html.parser.HTMLParser):
    """Simple HTML parser for when BeautifulSoup is not available."""
    
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.links = []
        self.text_content = []
        self.current_data = []
    
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "a":
            for attr in attrs:
                if attr[0].lower() == "href":
                    self.links.append(attr[1])
    
    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False
            self.title = "".join(self.current_data).strip()
            self.current_data = []
        elif tag.lower() in ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6"]:
            content = "".join(self.current_data).strip()
            if content:
                self.text_content.append(content)
            self.current_data = []
    
    def handle_data(self, data):
        if self.in_title:
            self.current_data.append(data)
        else:
            self.current_data.append(data)


class WebCrawler:
    """
    A simple web crawler with configurable parameters.
    """
    
    def __init__(self, 
                 max_pages: int = 10, 
                 same_domain: bool = True,
                 delay: float = 1.0,
                 user_agent: str = "PythonWebCrawler/1.0",
                 timeout: int = 30,
                 headers: Optional[Dict[str, str]] = None,
                 respect_robots: bool = True,
                 include_regex: Optional[str] = None,
                 exclude_regex: Optional[str] = None,
                 extract_images: bool = False,
                 extract_links: bool = True):
        """
        Initialize the crawler with configuration parameters.
        
        Args:
            max_pages: Maximum number of pages to crawl
            same_domain: Whether to only crawl pages from the same domain
            delay: Delay between requests in seconds
            user_agent: User agent string to use for requests
            timeout: Request timeout in seconds
            headers: Additional headers to include in requests
            respect_robots: Whether to respect robots.txt
            include_regex: Regular expression pattern for URLs to include
            exclude_regex: Regular expression pattern for URLs to exclude
            extract_images: Whether to extract image URLs
            extract_links: Whether to extract links from pages
        """
        self.max_pages = max_pages
        self.same_domain = same_domain
        self.delay = delay
        self.user_agent = user_agent
        self.timeout = timeout
        self.headers = headers or {}
        self.respect_robots = respect_robots
        self.include_regex = re.compile(include_regex) if include_regex else None
        self.exclude_regex = re.compile(exclude_regex) if exclude_regex else None
        self.extract_images = extract_images
        self.extract_links = extract_links
        
        # Add User-Agent to headers
        self.headers.setdefault("User-Agent", user_agent)
        
        # Initialize state variables
        self.visited_urls: Set[str] = set()
        self.robot_parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}
        
    def get_domain(self, url: str) -> str:
        """Extract the domain from a URL."""
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc
        
    def is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid and should be crawled."""
        # Basic URL validation
        if not url or not url.startswith(("http://", "https://")):
            return False
            
        # Skip already visited URLs
        if url in self.visited_urls:
            return False
            
        # Check domain restriction
        if self.same_domain and self.current_domain:
            if self.get_domain(url) != self.current_domain:
                return False
                
        # Check inclusion/exclusion patterns
        if self.include_regex and not self.include_regex.search(url):
            return False
            
        if self.exclude_regex and self.exclude_regex.search(url):
            return False
            
        # Check robots.txt
        if self.respect_robots:
            domain = self.get_domain(url)
            if domain not in self.robot_parsers:
                rp = urllib.robotparser.RobotFileParser()
                robots_url = f"{urllib.parse.urlparse(url).scheme}://{domain}/robots.txt"
                try:
                    rp.set_url(robots_url)
                    rp.read()
                    self.robot_parsers[domain] = rp
                except Exception:
                    # If robots.txt can't be read, assume crawling is allowed
                    self.robot_parsers[domain] = None
                    
            rp = self.robot_parsers[domain]
            if rp and not rp.can_fetch(self.user_agent, url):
                return False
                
        return True
        
    def normalize_url(self, url: str, base_url: str) -> str:
        """Normalize relative URLs to absolute URLs."""
        return urllib.parse.urljoin(base_url, url)
        
    def fetch_page(self, url: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Fetch a page and extract its content and links.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple containing (success, result_data)
        """
        try:
            # Mark URL as visited
            self.visited_urls.add(url)
            
            result = {
                "url": url,
                "title": "",
                "content": "",
                "links": [],
                "images": [],
                "status_code": None,
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # Fetch the page
            if BEAUTIFULSOUP_AVAILABLE:
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
                
                result["status_code"] = response.status_code
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                    return False, result
                    
                html_content = response.text
                
            else:
                # Fallback to urllib if requests is not available
                request = Request(url)
                for key, value in self.headers.items():
                    request.add_header(key, value)
                    
                with urlopen(request, timeout=self.timeout) as response:
                    result["status_code"] = response.status
                    
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                        return False, result
                        
                    html_content = response.read().decode('utf-8', errors='replace')
            
            # Parse the page with trafilatura if available (better content extraction)
            if TRAFILATURA_AVAILABLE:
                extracted_text = trafilatura.extract(html_content, include_links=True)
                if extracted_text:
                    result["content"] = extracted_text
                    
                extracted_title = trafilatura.extract_metadata(html_content).title
                if extracted_title:
                    result["title"] = extracted_title
            
            # Parse the page with BeautifulSoup or the fallback parser
            if BEAUTIFULSOUP_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title if not already done
                if not result.get("title") and soup.title:
                    result["title"] = soup.title.string.strip() if soup.title.string else ""
                
                # Extract content if not already done with trafilatura
                if not result.get("content"):
                    # Simple content extraction - paragraphs and headings
                    paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    result["content"] = "\n".join(tag.get_text().strip() for tag in paragraphs if tag.get_text().strip())
                
                # Extract links if requested
                if self.extract_links:
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        abs_url = self.normalize_url(href, url)
                        links.append({
                            "url": abs_url,
                            "text": link.get_text().strip(),
                            "title": link.get('title', '')
                        })
                    result["links"] = links
                
                # Extract images if requested
                if self.extract_images:
                    images = []
                    for img in soup.find_all('img', src=True):
                        src = img['src']
                        abs_src = self.normalize_url(src, url)
                        images.append({
                            "url": abs_src,
                            "alt": img.get('alt', ''),
                            "title": img.get('title', '')
                        })
                    result["images"] = images
                    
            else:
                # Use the simple parser as fallback
                parser = HTMLParserWithLinks()
                parser.feed(html_content)
                
                # Extract data
                if not result.get("title"):
                    result["title"] = parser.title
                    
                if not result.get("content"):
                    result["content"] = "\n".join(parser.text_content)
                    
                if self.extract_links:
                    links = []
                    for href in parser.links:
                        abs_url = self.normalize_url(href, url)
                        links.append({
                            "url": abs_url,
                            "text": "",
                            "title": ""
                        })
                    result["links"] = links
            
            result["success"] = True
            return True, result
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return False, {
                "url": url,
                "title": "",
                "content": f"Error: {str(e)}",
                "links": [],
                "images": [],
                "status_code": 500,
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def crawl(self, start_url: str, max_depth: int = 1) -> List[Dict[str, Any]]:
        """
        Crawl a website starting from a URL up to a maximum depth.
        
        Args:
            start_url: URL to start crawling from
            max_depth: Maximum crawl depth
            
        Returns:
            List of crawled pages data
        """
        # Initialize state for this crawl
        self.visited_urls = set()
        self.current_domain = self.get_domain(start_url)
        
        # Queue of URLs to crawl: (url, depth)
        urls_to_crawl = [(start_url, 0)]
        crawled_results = []
        
        logger.info(f"Starting crawl at {start_url} with max depth {max_depth}")
        
        while urls_to_crawl and len(crawled_results) < self.max_pages:
            # Get next URL and its depth
            url, depth = urls_to_crawl.pop(0)
            
            # Skip if URL already visited or invalid
            if url in self.visited_urls or not self.is_valid_url(url):
                continue
                
            logger.debug(f"Crawling {url} (depth {depth})")
            
            # Fetch the page
            success, result = self.fetch_page(url)
            
            # Add result if fetch was successful
            if success:
                crawled_results.append(result)
                
                # Enqueue child URLs if below max depth
                if depth < max_depth and self.extract_links:
                    for link in result["links"]:
                        link_url = link["url"]
                        if self.is_valid_url(link_url):
                            urls_to_crawl.append((link_url, depth + 1))
            
            # Respect the crawl delay
            if self.delay > 0:
                await asyncio.sleep(self.delay)
                
        logger.info(f"Crawling complete. Processed {len(crawled_results)} pages")
        return crawled_results


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Web crawler",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--url", 
        type=str, 
        required=True,
        help="URL to crawl"
    )
    parser.add_argument(
        "--depth", 
        type=int, 
        default=1,
        help="Maximum crawl depth"
    )
    parser.add_argument(
        "--max-pages", 
        type=int, 
        default=10,
        help="Maximum number of pages to crawl"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=30,
        help="Timeout in seconds for each request"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="output.json",
        help="Output file path"
    )
    parser.add_argument(
        "--format", 
        type=str, 
        choices=["json", "html", "markdown", "text"],
        default="json",
        help="Output format"
    )
    parser.add_argument(
        "--user-agent", 
        type=str,
        default="PythonWebCrawler/1.0",
        help="User agent string"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=1.0,
        help="Delay between requests in seconds"
    )
    parser.add_argument(
        "--headers", 
        type=str,
        help="Custom headers as JSON string"
    )
    parser.add_argument(
        "--allow-external", 
        action="store_true",
        help="Allow crawling external domains"
    )
    parser.add_argument(
        "--include-regex", 
        type=str,
        help="Regular expression pattern for URLs to include"
    )
    parser.add_argument(
        "--exclude-regex", 
        type=str,
        help="Regular expression pattern for URLs to exclude"
    )
    parser.add_argument(
        "--extract-images", 
        action="store_true",
        help="Extract image URLs"
    )
    parser.add_argument(
        "--extract-links", 
        action="store_true",
        default=True,
        help="Extract links from pages"
    )
    parser.add_argument(
        "--no-robots", 
        action="store_true",
        help="Ignore robots.txt"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def run_crawler(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Run the crawler asynchronously.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments
        
    Returns:
        List[Dict[str, Any]]: Crawling results
    """
    try:
        # Set logging level based on verbosity
        if args.verbose:
            logger.setLevel(logging.DEBUG)
        
        # Parse headers if provided
        headers = {}
        if args.headers:
            try:
                headers = json.loads(args.headers)
            except json.JSONDecodeError:
                raise MafiaError("Invalid JSON format for headers")
        
        # Create crawler instance
        crawler = WebCrawler(
            max_pages=args.max_pages,
            same_domain=not args.allow_external,
            delay=args.delay,
            user_agent=args.user_agent,
            timeout=args.timeout,
            headers=headers,
            respect_robots=not args.no_robots,
            include_regex=args.include_regex,
            exclude_regex=args.exclude_regex,
            extract_images=args.extract_images,
            extract_links=args.extract_links
        )
        
        # Start crawling
        logger.info(f"Starting crawl of {args.url} with depth {args.depth}")
        start_time = datetime.now()
        
        results = await crawler.crawl(args.url, max_depth=args.depth)
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        logger.info(f"Crawling completed. Processed {len(results)} pages in {elapsed:.2f} seconds")
        return results
        
    except Exception as e:
        raise MafiaError(f"Error during crawling: {str(e)}", exception=e)


def save_results(results: List[Dict[str, Any]], args: argparse.Namespace) -> None:
    """
    Save crawling results based on specified format and location.
    
    Args:
        results (List[Dict[str, Any]]): Crawling results
        args (argparse.Namespace): Parsed command-line arguments
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save results based on format
        if args.format == "json":
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif args.format == "html":
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("<!DOCTYPE html>\n<html><head><meta charset='utf-8'><title>Crawling Results</title>")
                f.write("<style>body{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px}</style>")
                f.write("</head><body>\n")
                f.write(f"<h1>Crawling Results for {args.url}</h1>\n")
                
                for result in results:
                    f.write(f"<article>\n")
                    f.write(f"<h2>{result.get('title', 'Untitled')}</h2>\n")
                    f.write(f"<p>URL: <a href='{result['url']}'>{result['url']}</a></p>\n")
                    
                    # Add status and timestamp
                    f.write(f"<p>Status: {result['status_code']} | Time: {result['timestamp']}</p>\n")
                    
                    # Main content
                    f.write(f"<div class='content'>{result['content']}</div>\n")
                    
                    # Links section if there are any
                    if result.get('links'):
                        f.write("<h3>Links</h3>\n<ul>\n")
                        for link in result['links'][:10]:  # Limit to 10 links
                            f.write(f"<li><a href='{link['url']}'>{link['text'] or link['url']}</a></li>\n")
                        if len(result['links']) > 10:
                            f.write(f"<li>...and {len(result['links']) - 10} more links</li>\n")
                        f.write("</ul>\n")
                    
                    # Images section if there are any
                    if result.get('images'):
                        f.write("<h3>Images</h3>\n<ul>\n")
                        for img in result['images'][:5]:  # Limit to 5 images
                            f.write(f"<li><a href='{img['url']}'>{img['alt'] or img['url']}</a></li>\n")
                        if len(result['images']) > 5:
                            f.write(f"<li>...and {len(result['images']) - 5} more images</li>\n")
                        f.write("</ul>\n")
                    
                    f.write("</article>\n<hr>\n")
                
                f.write("</body></html>")
                
        elif args.format == "markdown":
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(f"# Crawling Results for {args.url}\n\n")
                
                for result in results:
                    f.write(f"## {result.get('title', 'Untitled')}\n\n")
                    f.write(f"URL: {result['url']}\n\n")
                    f.write(f"Status: {result['status_code']} | Time: {result['timestamp']}\n\n")
                    
                    # Main content
                    f.write(f"{result['content']}\n\n")
                    
                    # Links section if there are any
                    if result.get('links'):
                        f.write("### Links\n\n")
                        for link in result['links'][:10]:  # Limit to 10 links
                            f.write(f"- [{link['text'] or link['url']}]({link['url']})\n")
                        if len(result['links']) > 10:
                            f.write(f"- ...and {len(result['links']) - 10} more links\n")
                        f.write("\n")
                    
                    # Images section if there are any
                    if result.get('images'):
                        f.write("### Images\n\n")
                        for img in result['images'][:5]:  # Limit to 5 images
                            f.write(f"- [{img['alt'] or img['url']}]({img['url']})\n")
                        if len(result['images']) > 5:
                            f.write(f"- ...and {len(result['images']) - 5} more images\n")
                        f.write("\n")
                    
                    f.write("---\n\n")
                    
        elif args.format == "text":
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(f"CRAWLING RESULTS FOR {args.url}\n")
                f.write("=" * 80 + "\n\n")
                
                for result in results:
                    f.write(f"TITLE: {result.get('title', 'Untitled')}\n")
                    f.write(f"URL: {result['url']}\n")
                    f.write(f"STATUS: {result['status_code']} | TIME: {result['timestamp']}\n\n")
                    
                    # Main content
                    f.write(f"{result['content']}\n\n")
                    
                    # Links section if there are any
                    if result.get('links'):
                        f.write("LINKS:\n")
                        for link in result['links'][:10]:  # Limit to 10 links
                            f.write(f"- {link['text'] or ''} : {link['url']}\n")
                        if len(result['links']) > 10:
                            f.write(f"- ...and {len(result['links']) - 10} more links\n")
                        f.write("\n")
                    
                    f.write("-" * 80 + "\n\n")
        
        logger.info(f"Results saved to {args.output} in {args.format} format")
        
    except Exception as e:
        # Use MafiaError for consistent error reporting
        raise MafiaError(f"Error saving results: {str(e)}", exception=e)


def main() -> None:
    """
    Main function to execute the crawler.
    """
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Run the crawler asynchronously
        results = asyncio.run(run_crawler(args))
        
        # Save the results
        save_results(results, args)
        
        sys.exit(0)
        
    except MafiaError as me:
        logger.error(str(me))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
        sys.exit(130)
    except Exception as e:
        # Catch any unhandled exceptions and format with MafiaError
        error = MafiaError("Unhandled exception", exception=e)
        logger.error(str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()