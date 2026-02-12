"""
Hevy reCAPTCHA Token Generator using Playwright

This module provides automated reCAPTCHA v3 token generation for Hevy API authentication.
Uses Playwright to launch a headless browser, visit the Hevy login page, and extract
the reCAPTCHA v3 Enterprise token.

Key features:
- Headless Chrome automation
- Short-term token caching (15 seconds) to prevent token reuse
- Automatic browser instance reuse for performance
- Cache invalidation after login attempts to avoid 400 errors
"""

import logging
import time
from typing import Optional
from playwright.async_api import async_playwright, Browser
from os import getenv

### reCAPTCHA configuration
RECAPTCHA_SITE_KEY = getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_TTL = 90  # reCAPTCHA tokens expire after 90 seconds (API limit)
RECAPTCHA_CACHE_DURATION = 15  # Cache tokens for only 15 seconds to prevent reuse (tokens are single-use)

### Global browser instance and token cache
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


async def _generate_recaptcha_token() -> str:
    """
    Generate a fresh reCAPTCHA token using Playwright.
    
    Launches a headless Chrome browser, navigates to Hevy login page,
    and extracts the reCAPTCHA token from the window object.
    
    Returns:
        str: Fresh reCAPTCHA v3 Enterprise token
        
    Raises:
        Exception: If browser launch or token extraction fails
    """
    global _browser
    
    playwright = None
    page = None
    
    try:
        ### Launch Playwright
        logging.debug("Launching Playwright browser...")
        playwright = await async_playwright().start()
        
        ### Reuse browser instance if available, otherwise create new one
        if _browser is None or not _browser.is_connected():
            _browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ]
            )
            logging.debug("Browser launched successfully")
        
        ### Create new page
        page = await _browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        ### Navigate to Hevy login page
        await page.goto("https://www.hevy.com/login", wait_until="networkidle", timeout=30000)
        
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
        logging.error(f"Error generating reCAPTCHA token: {e}")
        
        ### Clean up resources on error (silently ignore cleanup failures)
        if page:
            try:
                await page.close()
            except:
                pass
        
        if _browser:
            try:
                await _browser.close()
                _browser = None
            except:
                pass
        
        if playwright:
            try:
                await playwright.stop()
            except:
                pass
        
        raise Exception(f"Failed to generate reCAPTCHA token: {e}")
