#!/usr/bin/env python3
import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_playwright():
    """
    Install Playwright and its browsers.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Installing Playwright package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        
        logger.info("Installing Playwright browsers...")
        # Install browsers (skip system dependencies since we're using the system-installed browsers)
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        
        logger.info("Playwright installation completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during Playwright installation: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during installation: {e}")
        return False

def check_playwright_installation():
    """
    Check if Playwright is properly installed.
    Returns True if Playwright can be imported, False otherwise.
    """
    try:
        import playwright
        from playwright.sync_api import sync_playwright
        
        logger.info("Playwright is installed.")
        
        # Test browser launch
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://example.com")
            title = page.title()
            browser.close()
            
        logger.info(f"Browser test successful! Page title: {title}")
        return True
    except ImportError:
        logger.error("Playwright is not installed. Run install_playwright() first.")
        return False
    except Exception as e:
        logger.error(f"Error testing Playwright installation: {e}")
        return False

if __name__ == "__main__":
    # Check if we should force reinstallation
    force_install = len(sys.argv) > 1 and sys.argv[1] == "--force"
    
    if force_install:
        logger.info("Forcing Playwright reinstallation...")
        success = install_playwright()
    else:
        # Check if Playwright is already installed
        try:
            import playwright
            logger.info("Playwright is already installed.")
            # Still check if it works properly
            success = check_playwright_installation()
            if not success:
                logger.info("Reinstalling Playwright due to failed check...")
                success = install_playwright()
        except ImportError:
            logger.info("Playwright not found. Installing...")
            success = install_playwright()
    
    # Final status report
    if success:
        logger.info("Playwright setup completed successfully.")
        sys.exit(0)
    else:
        logger.error("Playwright setup failed.")
        sys.exit(1)