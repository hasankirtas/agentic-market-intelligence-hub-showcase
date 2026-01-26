"""
Base parser class for site-specific parsers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from bs4 import BeautifulSoup


class BaseParser(ABC):
    """
    Abstract base class for site-specific parsers.
    All parsers must implement parse() method.
    """
    
    def __init__(self, site_name: str):
        """
        Initialize parser.
        
        Args:
            site_name: Name of the site (e.g., "vercel", "netlify")
        """
        self.site_name = site_name
    
    @abstractmethod
    def parse(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse HTML and extract structured data.
        
        Args:
            html: Raw HTML content
            url: Source URL
        
        Returns:
            Dict with extracted data:
            - pricing: Dict with tier pricing
            - tiers: List of tier information
            - limits: Dict with service limits
            - features: List of features
        """
        pass
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML string to BeautifulSoup object.
        
        Args:
            html: Raw HTML string
        
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'html.parser')
    
    def _extract_text(self, element) -> str:
        """
        Extract text from BeautifulSoup element.
        
        Args:
            element: BeautifulSoup element
        
        Returns:
            Cleaned text string
        """
        if element is None:
            return ""
        return element.get_text(strip=True)
    
    def _extract_price(self, text: str) -> float:
        """
        Extract numeric price from text.
        
        Args:
            text: Text containing price (e.g., "$20/month", "Free")
        
        Returns:
            Price as float (0.0 for "Free")
        """
        import re
        # Remove common currency symbols and text
        text = text.lower().replace("free", "0").replace("$", "").replace("€", "").replace("£", "")
        # Extract first number
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            return float(match.group(1))
        return 0.0

