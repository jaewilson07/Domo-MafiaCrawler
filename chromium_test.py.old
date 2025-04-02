#!/usr/bin/env python3
"""
Chromium browser test script with environment compatibility checking.

This script tests if Playwright can properly initialize a browser in the current environment.
It includes additional checks and workarounds for common issues in restricted environments.
"""
import asyncio
import sys
import os
import platform
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_glibc_version():
    """
    Check the GLIBC version on the system.
    
    Returns:
        tuple: (major, minor) version numbers, or None if unavailable
    """
    try:
        # Try to get the GLIBC version from the system
        process = subprocess.Popen(['ldd', '--version'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True)
        stdout, stderr = process.communicate()
        
        # Parse the output to get the version
        if stdout:
            lines = stdout.strip().split('\n')
            for line in lines:
                if 'GLIBC' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('2.'):
                            version = part
                            major, minor = map(int, version.split('.')[:2])
                            return (major, minor)
        
        # Alternative method if ldd doesn't work
        process = subprocess.Popen(['/lib/x86_64-linux-gnu/libc.so.6'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True)
        stdout, stderr = process.communicate()
        
        if stdout:
            lines = stdout.strip().split('\n')
            for line in lines:
                if 'GLIBC' in line and 'version' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('2.'):
                            version = part
                            major, minor = map(int, version.split('.')[:2])
                            return (major, minor)
        
        return None
        
    except Exception as e:
        logger.warning(f"Could not determine GLIBC version: {e}")
        return None

def check_environment_compatibility():
    """
    Check if the current environment is compatible with Playwright browser automation.
    
    Returns:
        dict: Dictionary with compatibility information
    """
    compatibility = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "glibc_version": None,
        "is_compatible": None,
        "issues": [],
        "recommendations": []
    }
    
    # Check GLIBC version
    if platform.system() == 'Linux':
        glibc_version = check_glibc_version()
        if glibc_version:
            compatibility["glibc_version"] = f"{glibc_version[0]}.{glibc_version[1]}"
            
            # Chromium from Playwright requires GLIBC >= 2.32
            if glibc_version[0] < 2 or (glibc_version[0] == 2 and glibc_version[1] < 32):
                compatibility["is_compatible"] = False
                compatibility["issues"].append(
                    f"GLIBC version {compatibility['glibc_version']} is too old (need >= 2.32)")
                compatibility["recommendations"].append(
                    "Use a Docker container with a newer Ubuntu/Debian version")
            else:
                compatibility["is_compatible"] = True
        else:
            compatibility["issues"].append("Could not determine GLIBC version")
            compatibility["recommendations"].append("Try using a Docker container")
    
    # Check if we're in a restricted environment
    if os.environ.get('REPLIT', '') or os.environ.get('REPL_ID', ''):
        compatibility["environment"] = "Replit"
        compatibility["is_compatible"] = False
        compatibility["issues"].append("Replit may have limitations for browser automation")
        compatibility["recommendations"].append(
            "Consider using an API-based approach instead of browser automation")
        compatibility["recommendations"].append(
            "If browser automation is essential, consider external services like browserless.io")
    
    return compatibility

async def test_browser_import():
    """Test if we can import the Playwright package."""
    try:
        import playwright
        from playwright.async_api import async_playwright
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

async def test_browser_launch():
    """Test if we can launch a browser."""
    try:
        from playwright.async_api import async_playwright
        
        # Launch options to work around common issues
        browser_launch_options = {
            "headless": True,
            "chromium_sandbox": False,
            "args": [
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--single-process",
            ]
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(**browser_launch_options)
            await browser.close()
            return True, None
    except Exception as e:
        return False, str(e)

async def browser_test():
    """Run a full browser test by navigating to a page."""
    try:
        from playwright.async_api import async_playwright
        
        logger.info("Starting browser test with Playwright...")
        
        # Launch options to work around common issues
        browser_launch_options = {
            "headless": True,
            "chromium_sandbox": False,
            "args": [
                "--no-sandbox",
                "--disable-gpu",
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
            
            # Close the browser
            await browser.close()
            
            logger.info("Browser test completed successfully!")
            return True, None
    except Exception as e:
        return False, str(e)

async def main():
    """Main function to run all tests."""
    # First check environment compatibility
    compatibility = check_environment_compatibility()
    
    logger.info("Environment compatibility check results:")
    for key, value in compatibility.items():
        if isinstance(value, list):
            logger.info(f"- {key}:")
            for item in value:
                logger.info(f"  - {item}")
        else:
            logger.info(f"- {key}: {value}")
    
    # Test Playwright import
    import_success, import_error = await test_browser_import()
    if import_success:
        logger.info("✅ Playwright import test passed")
    else:
        logger.error(f"❌ Playwright import test failed: {import_error}")
        return False
    
    # Test browser launch
    launch_success, launch_error = await test_browser_launch()
    if launch_success:
        logger.info("✅ Browser launch test passed")
    else:
        logger.error(f"❌ Browser launch test failed: {launch_error}")
        return False
    
    # Only run full browser test if environment is potentially compatible
    if compatibility["is_compatible"] is not False:
        # Full browser test
        browser_success, browser_error = await browser_test()
        if browser_success:
            logger.info("✅ Full browser test passed")
            return True
        else:
            logger.error(f"❌ Full browser test failed: {browser_error}")
            return False
    else:
        logger.warning("Skipping full browser test due to environment incompatibility")
        logger.info("Recommended actions:")
        for rec in compatibility["recommendations"]:
            logger.info(f"- {rec}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)