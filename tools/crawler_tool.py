"""
Crawl4AI wrapper tool.
Uses async Crawl4AI API for web scraping.
"""
import asyncio
from typing import Dict, Any, Optional
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from core.abstractions.base_tool import BaseTool
from core.resilience.decorators import resilient, RetryConfig, RateLimiterConfig
from core.logger import setup_logger
import random
import requests

logger = setup_logger(__name__)


class CrawlerTool(BaseTool):
    """
    Crawl4AI wrapper tool for web scraping.
    Uses async API for better performance.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize crawler tool.
        
        Args:
            name: Tool name
            config: Configuration dict with:
                   - use_playwright: bool (default: True)
                   - timeout: int (default: 60, in milliseconds)
                   - wait_for: str (optional, CSS selector to wait for)
        """
        super().__init__(name, config)
        self.use_playwright = config.get("use_playwright", True)
        logger.info(f"CrawlerTool initialized - use_playwright: {self.use_playwright} (type: {type(self.use_playwright)})")  # DEBUG
        self.timeout = config.get("timeout", 60) * 1000  # Convert to milliseconds
        self.wait_for = config.get("wait_for", None)
        self.crawler = None
    
    async def _initialize_crawler(self):
        """Initialize Crawl4AI crawler instance (async)."""
        if self.crawler is None and self.use_playwright:
            try:
                browser_config = BrowserConfig()
                self.crawler = AsyncWebCrawler(config=browser_config)
                logger.debug("CrawlerTool: Crawl4AI crawler initialized with Playwright")
            except Exception as e:
                logger.error(f"Failed to initialize crawler: {e}")
                raise
    
    async def _random_delay(self, min_seconds: float = 2.0, max_seconds: float = 8.0):
        """
        Add random delay for ethical scraping.
        
        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
        logger.debug(f"CrawlerTool: Random delay of {delay:.2f}s applied")
    
    async def _perform_http_crawl(self, url: str, timeout: int) -> Dict[str, Any]:
        """
        Perform a simple HTTP crawl using requests (fallback mechanism).
        
        Args:
            url: URL to crawl
            timeout: Timeout in milliseconds
            
        Returns:
            Dict representing the scan result
        """
        def _fetch():
            try:
                # Convert timeout to seconds (min 5s)
                timeout_sec = max(int(timeout/1000), 5)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
                }
                resp = requests.get(url, timeout=timeout_sec, headers=headers)
                ok = 200 <= resp.status_code < 400
                return {
                    "html": resp.text if ok else "",
                    "markdown": "",
                    "status_code": resp.status_code,
                    "success": ok,
                    "error": None if ok else f"HTTP {resp.status_code}",
                    "url": url
                }
            except Exception as http_err:
                return {
                    "html": "",
                    "markdown": "",
                    "status_code": 0,
                    "success": False,
                    "error": str(http_err),
                    "url": url
                }
        
        return await asyncio.to_thread(_fetch)

    @resilient(
        retry_config=RetryConfig(
            max_attempts=3,
            initial_delay=2.0,
            exponential_base=2.0
        ),
        rate_limiter_config=RateLimiterConfig(
            max_requests=10,
            time_window=60.0
        ),
        timeout=60.0
    )
    async def execute(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Crawl a URL and return raw HTML/content.
        
        Args:
            url: URL to crawl
            **kwargs: Additional options:
                    - use_playwright: bool (override config)
                    - timeout: int (override config)
                    - wait_for: str (override config)
        
        Returns:
            Dict with:
            - html: str - Raw HTML content
            - markdown: str - Markdown content (if available)
            - status_code: int - HTTP status code
            - success: bool - Whether crawl was successful
        """
        try:
            # Random delay for ethical scraping
            await self._random_delay()
            
            # Override config with kwargs if provided
            timeout = kwargs.get("timeout", self.timeout)
            if isinstance(timeout, int) and timeout < 1000:  # Assume seconds if < 1000
                timeout = timeout * 1000  # Convert to milliseconds
            wait_for = kwargs.get("wait_for", self.wait_for)
            
            # Configure crawler run
            crawler_config = CrawlerRunConfig(
                page_timeout=timeout,
                wait_for=wait_for if wait_for else None
            )
            
            # Decide whether to use Playwright (Crawl4AI) or fallback
            use_playwright = kwargs.get("use_playwright", self.use_playwright)
            
            if use_playwright:
                logger.info(f"CrawlerTool: Crawling URL with Playwright: {url}")
                try:
                    # Initialize crawler if needed (async)
                    await self._initialize_crawler()
                    
                    # Run crawler (async API)
                    result = await self.crawler.arun(
                        url=url,
                        config=crawler_config
                    )
                    
                    if result.success:
                        logger.info(f"CrawlerTool: Successfully crawled {url}")
                        return {
                            "html": result.html or "",
                            "markdown": result.markdown or "",
                            "status_code": result.status_code or 200,
                            "success": True,
                            "url": url
                        }
                    else:
                        logger.warning(f"CrawlerTool: Playwright crawl failed for {url}: {result.error_message}. Attempting simple HTTP fallback.")
                        # FALLBACK to HTTP
                        return await self._perform_http_crawl(url, timeout)

                except Exception as pw_err:
                    logger.error(f"CrawlerTool: Playwright exception for {url}: {pw_err}. Attempting simple HTTP fallback.")
                    # FALLBACK to HTTP
                    return await self._perform_http_crawl(url, timeout)
            else:
                # HTTP fallback without Playwright
                logger.info(f"CrawlerTool: Crawling URL without Playwright (HTTP mode): {url}")
                result = await self._perform_http_crawl(url, timeout)
                if result["success"]:
                    logger.info(f"CrawlerTool: Successfully crawled (HTTP) {url}")
                else:
                    logger.warning(f"CrawlerTool: HTTP crawl failed for {url}: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"CrawlerTool: Exception while crawling {url}: {e}")
            return {
                "html": "",
                "markdown": "",
                "status_code": 0,
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool parameter schema.
        
        Returns:
            JSON schema for tool parameters
        """
        return {
            "name": self.name,
            "description": "Crawl a URL and extract HTML content using Crawl4AI with Playwright rendering with HTTP fallback",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to crawl"
                    },
                    "use_playwright": {
                        "type": "boolean",
                        "description": "Use Playwright for JS rendering (default: True)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 60)"
                    },
                    "wait_for": {
                        "type": "string",
                        "description": "CSS selector to wait for before extracting content"
                    }
                },
                "required": ["url"]
            }
        }
    
    async def cleanup(self):
        """Cleanup crawler resources."""
        if self.crawler:
            try:
                # Async crawler cleanup
                await self.crawler.close()
                self.crawler = None
                logger.debug("CrawlerTool: Crawler cleaned up")
            except Exception as e:
                logger.warning(f"CrawlerTool: Error during cleanup: {e}")

