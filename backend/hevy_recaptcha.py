"""
Hevy reCAPTCHA Token Generator using Playwright

This module provides automated reCAPTCHA v3 token generation for Hevy API authentication.
Uses Playwright to launch a headless browser, visit the Hevy login page, and extract
the reCAPTCHA v3 Enterprise token.

Key features:
- Headless Chrome automation
- Short-term token caching (15 seconds) to prevent token reuse
- Automatic browser instance reuse for performance
- Retry logic to handle transient browser crashes (e.g. "Target crashed")
- Cache invalidation after login attempts to avoid 400 errors
"""

import asyncio
import logging
import time
from typing import Optional
from playwright.async_api import async_playwright, Browser, Playwright
from os import getenv

### reCAPTCHA configuration
RECAPTCHA_SITE_KEY = getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_TTL = 90  # reCAPTCHA tokens expire after 90 seconds (API limit)
RECAPTCHA_CACHE_DURATION = 15  # Cache tokens for only 15 seconds to prevent reuse (tokens are single-use)

### Max number of retries when the browser crashes during token generation
RECAPTCHA_MAX_RETRIES = 2

### Global Playwright/browser instances and token cache
_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None
_cached_token: Optional[str] = None
_token_timestamp: float = 0


async def get_recaptcha_token() -> str:
    """
    Get a valid reCAPTCHA token for Hevy API authentication.

    Uses short-term caching (15 seconds) to avoid unnecessary browser launches
    while preventing reuse of spent tokens. reCAPTCHA tokens are often single-use,
    so aggressive caching can cause 400 errors.

    Returns:
        str: Valid reCAPTCHA Enterprise token

    Raises:
        Exception: If token generation fails
    """
    global _cached_token, _token_timestamp

    ### Check if we have a valid cached token (15 second cache)
    current_time = time.time()
    if _cached_token and (current_time - _token_timestamp) < RECAPTCHA_CACHE_DURATION:
        age = int(current_time - _token_timestamp)
        logging.debug(f"Using cached reCAPTCHA token ({age}s old)")
        return _cached_token

    ### Need to get a new token
    logging.debug("Obtaining new reCAPTCHA token...")
    token = await _generate_recaptcha_token()

    ### Cache the token
    _cached_token = token
    _token_timestamp = current_time
    logging.debug(f"Cached reCAPTCHA token (expires in {RECAPTCHA_CACHE_DURATION}s)")

    return token


def invalidate_recaptcha_cache() -> None:
    """
    Invalidate the cached reCAPTCHA token.

    Called after login attempts to prevent token reuse. reCAPTCHA tokens are
    single-use, so reusing a spent token results in 400 errors from Hevy API.
    """
    global _cached_token, _token_timestamp

    if _cached_token:
        logging.debug("Invalidated reCAPTCHA token cache")
        _cached_token = None
        _token_timestamp = 0


async def _teardown_browser() -> None:
    """
    Close the global browser and Playwright instances and reset them to None.
    Errors during teardown are silently ignored so callers can always proceed.
    """
    global _playwright, _browser

    if _browser:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None

    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None


async def _generate_recaptcha_token() -> str:
    """
    Generate a fresh reCAPTCHA token using Playwright.

    Launches a headless Chrome browser, navigates to Hevy login page,
    and extracts the reCAPTCHA token from the window object.

    Retries up to RECAPTCHA_MAX_RETRIES times on transient failures such as
    browser crashes ("Target crashed") before giving up.

    Returns:
        str: Fresh reCAPTCHA v3 Enterprise token

    Raises:
        Exception: If browser launch or token extraction fails after all retries
    """
    global _playwright, _browser

    last_error: Optional[Exception] = None

    for attempt in range(1, RECAPTCHA_MAX_RETRIES + 1):
        page = None
        try:
            ### Ensure we have a live Playwright + browser pair
            if _playwright is None or _browser is None or not _browser.is_connected():
                ### Tear down any partially-alive state before (re)starting
                await _teardown_browser()

                logging.debug("Launching Playwright browser...")
                _playwright = await async_playwright().start()
                _browser = await _playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-software-rasterizer",
                        "--disable-extensions",
                        "--disable-background-networking",
                        "--disable-default-apps",
                        "--disable-sync",
                        "--metrics-recording-only",
                        "--mute-audio",
                        "--no-first-run",
                        "--disable-features=TranslateUI",
                        "--disable-hang-monitor",
                        "--disable-ipc-flooding-protection",
                        "--disable-renderer-backgrounding",
                        "--enable-features=NetworkService,NetworkServiceInProcess",
                    ],
                )
                logging.debug("Browser launched successfully")

            ### Create new page
            page = await _browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            ### Navigate to Hevy login page
            logging.debug("Navigating to Hevy login page...")
            try:
                await page.goto("https://www.hevy.com/login", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception as nav_error:
                logging.warning(f"Navigation warning: {nav_error}, continuing anyway...")
                ### Try to continue even if networkidle times out
                await page.wait_for_timeout(2000)

            ### Wait for reCAPTCHA to load and get token
            ## The token is stored in window.recaptchaToken by Hevy's frontend
            token = await page.evaluate(f"""
                () => {{
                    return new Promise((resolve, reject) => {{
                        const maxAttempts = 50;
                        let attempts = 0;
                        
                        const checkToken = () => {{
                            // Check for reCAPTCHA token in various possible locations
                            const token = window.recaptchaToken || 
                                         window.__recaptchaToken || 
                                         window.grecaptcha?.enterprise?.execute ||
                                         null;
                            
                            if (token && typeof token === 'string') {{
                                resolve(token);
                            }} else if (attempts >= maxAttempts) {{
                                // Try to execute reCAPTCHA if available
                                if (window.grecaptcha && window.grecaptcha.enterprise) {{
                                    window.grecaptcha.enterprise.execute(
                                        '{RECAPTCHA_SITE_KEY}',
                                        {{action: 'login'}}
                                    ).then(resolve).catch(reject);
                                }} else {{
                                    reject(new Error('reCAPTCHA token not found after 10 seconds'));
                                }}
                            }} else {{
                                attempts++;
                                setTimeout(checkToken, 200);
                            }}
                        }};
                        
                        checkToken();
                    }});
                }}
            """)

            if not token:
                raise Exception("Failed to obtain reCAPTCHA token")

            logging.debug("Successfully obtained reCAPTCHA token")

            ### Close the page (keep browser open for reuse)
            await page.close()

            return token

        except Exception as e:
            last_error = e
            logging.error(f"Error generating reCAPTCHA token (attempt {attempt}/{RECAPTCHA_MAX_RETRIES}): {e}")

            ### Always close the page on failure
            if page:
                try:
                    await page.close()
                except Exception:
                    pass

            ### Tear down the browser so the next attempt starts completely fresh
            await _teardown_browser()

            if attempt < RECAPTCHA_MAX_RETRIES:
                logging.info("Retrying reCAPTCHA token generation with a fresh browser...")
                await asyncio.sleep(1)

    raise Exception(f"Failed to generate reCAPTCHA token: {last_error}")
