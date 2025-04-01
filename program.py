browser_config = BrowserConfig(
    browser_type="chromium",
    headless=True,
    verbose=True,
    extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
)