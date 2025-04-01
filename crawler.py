#!/usr/bin/env python3
"""
crawler.py - A command-line web crawler using crawl4ai

This script provides a simple command-line interface to crawl websites
using the crawl4ai library. It allows for configuration of crawling parameters
and outputs results in a structured format.

Usage:
    python crawler.py --url URL [options]

Example:
    python crawler.py --url https://example.com --depth 2 --output results.json
"""

import os
import sys
import argparse
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the required crawl4ai modules
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crawler')


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Crawl websites using crawl4ai'
    )
    
    # Required arguments
    parser.add_argument(
        '--url', '-u',
        type=str,
        required=True,
        help='Target URL to crawl'
    )
    
    # Optional arguments
    parser.add_argument(
        '--depth', '-d',
        type=int,
        default=1,
        help='Maximum crawl depth (default: 1)'
    )
    
    parser.add_argument(
        '--max-pages', '-m',
        type=int,
        default=100,
        help='Maximum number of pages to crawl (default: 100)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output file path for crawled data (default: stdout)'
    )
    
    parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['json', 'csv', 'txt'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--delay', 
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '--allow-domains',
        type=str,
        nargs='+',
        default=None,
        help='List of domains to allow (default: domain of the URL)'
    )
    
    parser.add_argument(
        '--extract-content',
        action='store_true',
        default=False,
        help='Extract content from pages (default: False)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=False,
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def configure_crawler(args: argparse.Namespace) -> AsyncWebCrawler:
    """Configure the crawler based on command-line arguments."""
    # Create the crawler instance with default configuration
    crawler = AsyncWebCrawler(thread_safe=True)
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    return crawler


def save_results(results: List[Dict[str, Any]], args: argparse.Namespace) -> None:
    """Save crawling results based on specified format and location."""
    if not results:
        logger.warning("No results to save")
        return
    
    # Prepare output data
    output_data = {
        "metadata": {
            "url": args.url,
            "crawl_time": datetime.now().isoformat(),
            "pages_crawled": len(results),
            "max_depth": args.depth
        },
        "results": results
    }
    
    # Output to file or stdout
    if args.output:
        output_path = Path(args.output)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if args.format == 'json':
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
        elif args.format == 'csv':
            try:
                import csv
                with open(output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write header
                    if results:
                        writer.writerow(['url', 'title', 'content_length', 'status_code'])
                        # Write data
                        for result in results:
                            writer.writerow([
                                result.get('url', ''),
                                result.get('title', ''),
                                len(result.get('content', '')) if result.get('content') else 0,
                                result.get('status_code', '')
                            ])
            except ImportError:
                logger.error("CSV output requires the csv module")
                sys.exit(1)
        elif args.format == 'txt':
            with open(output_path, 'w') as f:
                for result in results:
                    f.write(f"URL: {result.get('url', '')}\n")
                    f.write(f"Title: {result.get('title', '')}\n")
                    f.write(f"Status: {result.get('status_code', '')}\n")
                    content = result.get('content')
                    if content:
                        f.write(f"Content length: {len(content)}\n")
                    f.write("\n" + "-"*50 + "\n\n")
        
        logger.info(f"Results saved to {output_path}")
    else:
        # Output to stdout
        print(json.dumps(output_data, indent=2))


async def run_crawler(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Run the crawler asynchronously."""
    # Configure the crawler
    crawler = configure_crawler(args)
    
    # Log start of crawling
    logger.info(f"Starting crawl of {args.url} with depth {args.depth}")
    
    run_config = CrawlerRunConfig(
        check_robots_txt=True,
        deep_crawl_strategy=None,
        verbose=args.verbose
    )
    
    # Start the crawl
    results_container = await crawler.arun(args.url, config=run_config)
    
    # Check if results_container has a 'results' attribute or is already a list
    if hasattr(results_container, 'results'):
        results = [r.dict() if hasattr(r, 'dict') else r for r in results_container.results]
    else:
        # If it's a list, convert each item to dict if possible
        results = [r.dict() if hasattr(r, 'dict') else r for r in results_container]
    
    logger.info(f"Crawling completed. Processed {len(results)} pages.")
    return results


def main() -> None:
    """Main function to execute the crawler."""
    # Parse command-line arguments
    args = parse_args()
    
    try:
        # Run the crawler using asyncio
        results = asyncio.run(run_crawler(args))
        
        # Save the results
        save_results(results, args)
        
    except Exception as e:
        logger.error(f"An error occurred during crawling: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
