#!/usr/bin/env python3
import asyncio
import sys
from playwright.async_api import async_playwright

async def main():
    try:
        print("Launching Playwright browser test...")
        async with async_playwright() as playwright:
            # Launch chromium browser in headless mode
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to a test URL
            print("Navigating to example.com...")
            await page.goto("https://example.com")
            
            # Get page title
            title = await page.title()
            print(f"Page title: {title}")
            
            # Capture a screenshot
            print("Taking screenshot...")
            await page.screenshot(path="screenshot.png")
            
            # Get page content
            content = await page.content()
            print(f"Page content length: {len(content)} bytes")
            print(f"Content preview: {content[:200]}...")
            
            # Close browser
            await browser.close()
            print("Browser test completed successfully!")
            return True
    except Exception as e:
        print(f"Error during browser test: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)