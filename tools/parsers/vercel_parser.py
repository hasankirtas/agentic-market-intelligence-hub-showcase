"""
Vercel pricing page parser.
"""
from typing import Dict, Any
from .base_parser import BaseParser


class VercelParser(BaseParser):
    """
    Parser for Vercel pricing page.
    Extracts pricing tiers, limits, and features.
    """
    
    def __init__(self):
        super().__init__("vercel")
    
    def parse(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse Vercel pricing page.
        
        Args:
            html: Raw HTML content
            url: Source URL
        
        Returns:
            Dict with pricing, tiers, limits, features
        """
        soup = self._parse_html(html)
        
        pricing = {}
        tiers = []
        
        # Vercel pricing structure (CSS selectors may need adjustment based on actual page)
        # Common selectors for Vercel pricing page
        tier_sections = soup.select('[data-tier], .pricing-tier, [class*="tier"]')
        
        if not tier_sections:
            # Fallback: look for pricing cards
            tier_sections = soup.select('.pricing-card, [class*="pricing"]')
        
        for tier_section in tier_sections:
            tier_name = self._extract_tier_name(tier_section)
            if not tier_name:
                continue
            
            price_text = self._extract_tier_price(tier_section)
            price = self._extract_price(price_text)
            
            limits = self._extract_tier_limits(tier_section)
            features = self._extract_tier_features(tier_section)
            
            tier_data = {
                "name": tier_name,
                "price": price,
                "currency": "USD",
                "billing": "monthly",  # Vercel typically monthly
                "limits": limits,
                "features": features
            }
            
            tiers.append(tier_data)
            pricing[tier_name.lower()] = {
                "price": price,
                "currency": "USD"
            }
        
        return {
            "pricing": pricing,
            "tiers": tiers,
            "limits": self._extract_global_limits(soup),
            "features": self._extract_global_features(soup),
            "source": "vercel",
            "url": url
        }
    
    def _extract_tier_name(self, element) -> str:
        """Extract tier name from element."""
        # Try various selectors
        name_elem = (
            element.select_one('h2, h3, [class*="tier-name"], [class*="plan-name"]') or
            element.select_one('[data-tier-name]')
        )
        if name_elem:
            return self._extract_text(name_elem).lower()
        return ""
    
    def _extract_tier_price(self, element) -> str:
        """Extract price text from element."""
        price_elem = (
            element.select_one('[class*="price"], [class*="pricing"]') or
            element.select_one('[data-price]')
        )
        if price_elem:
            return self._extract_text(price_elem)
        return "Free"
    
    def _extract_tier_limits(self, element) -> Dict[str, Any]:
        """Extract tier-specific limits."""
        limits = {}
        # Look for limit indicators
        limit_elements = element.select('[class*="limit"], [class*="quota"]')
        for limit_elem in limit_elements:
            text = self._extract_text(limit_elem)
            # Parse common limit formats
            if "bandwidth" in text.lower():
                limits["bandwidth"] = text
            elif "build" in text.lower():
                limits["builds"] = text
            elif "function" in text.lower():
                limits["functions"] = text
        return limits
    
    def _extract_tier_features(self, element) -> list:
        """Extract tier-specific features."""
        features = []
        feature_elements = element.select('li, [class*="feature"]')
        for feat_elem in feature_elements:
            text = self._extract_text(feat_elem)
            if text and len(text) > 3:  # Filter out empty/short items
                features.append(text)
        return features[:10]  # Limit to first 10 features
    
    def _extract_global_limits(self, soup) -> Dict[str, Any]:
        """Extract global service limits."""
        return {}  # Vercel limits are typically tier-specific
    
    def _extract_global_features(self, soup) -> list:
        """Extract global features."""
        return []  # Features are typically tier-specific

