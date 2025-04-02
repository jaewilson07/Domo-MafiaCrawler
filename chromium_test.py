#!/usr/bin/env python3
import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Import playwright only when needed to avoid import errors
        from playwright.async_api import async_playwright
        
        logger.info("Starting browser test with Playwright...")
        
        # Launch the browser with specific options to work around missing system dependencies
        browser_launch_options = {
            "headless": True,
            # Skip browser executable path validation
            "chromium_sandbox": False,
            # Try to ignore missing system dependencies
            "ignore_default_args": ["--disable-dev-shm-usage"],
            "args": [
                "--no-sandbox",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--single-process",
            ]
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(**browser_launch_options)
            page = await browser.new_page()
            
            # Navigate to a test page
            logger.info("Navigating to example.com...")
            await page.goto("https://example.com", timeout=60000)
            
            # Get and log the page title
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Get page content
            content = await page.content()
            logger.info(f"Page content length: {len(content)} bytes")
            logger.info(f"First 200 characters: {content[:200]}")
            
            # Close the browser
            await browser.close()
            
            logger.info("Browser test completed successfully!")
            return True
    except ImportError as e:
        logger.error(f"Failed to import Playwright: {e}")
        return False
    except Exception as e:
        logger.error(f"Browser test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)