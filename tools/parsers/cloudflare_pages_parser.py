"""
Cloudflare Pages pricing page parser.
"""
from typing import Dict, Any
from .base_parser import BaseParser


class CloudflarePagesParser(BaseParser):
    """
    Parser for Cloudflare Pages pricing page.
    Extracts pricing tiers, limits, and features.
    """
    
    def __init__(self):
        super().__init__("cloudflare_pages")
    
    def parse(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse Cloudflare Pages pricing page.
        
        Args:
            html: Raw HTML content
            url: Source URL
        
        Returns:
            Dict with pricing, tiers, limits, features
        """
        soup = self._parse_html(html)
        
        pricing = {}
        tiers = []
        
        # Cloudflare Pages pricing structure
        tier_sections = soup.select('[data-tier], .pricing-tier, [class*="tier"]')
        
        if not tier_sections:
            tier_sections = soup.select('.plan, [class*="plan"]')
        
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
                "billing": "monthly",
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
            "source": "cloudflare_pages",
            "url": url
        }
    
    def _extract_tier_name(self, element) -> str:
        """Extract tier name from element."""
        name_elem = (
            element.select_one('h2, h3, [class*="tier-name"]') or
            element.select_one('[data-tier-name]')
        )
        if name_elem:
            return self._extract_text(name_elem).lower()
        return ""
    
    def _extract_tier_price(self, element) -> str:
        """Extract price text from element."""
        price_elem = (
            element.select_one('[class*="price"]') or
            element.select_one('[data-price]')
        )
        if price_elem:
            return self._extract_text(price_elem)
        return "Free"
    
    def _extract_tier_limits(self, element) -> Dict[str, Any]:
        """Extract tier-specific limits."""
        limits = {}
        limit_elements = element.select('[class*="limit"], [class*="quota"]')
        for limit_elem in limit_elements:
            text = self._extract_text(limit_elem)
            if "request" in text.lower():
                limits["requests"] = text
            elif "build" in text.lower():
                limits["builds"] = text
        return limits
    
    def _extract_tier_features(self, element) -> list:
        """Extract tier-specific features."""
        features = []
        feature_elements = element.select('li, [class*="feature"]')
        for feat_elem in feature_elements:
            text = self._extract_text(feat_elem)
            if text and len(text) > 3:
                features.append(text)
        return features[:10]
    
    def _extract_global_limits(self, soup) -> Dict[str, Any]:
        """Extract global service limits."""
        return {}
    
    def _extract_global_features(self, soup) -> list:
        """Extract global features."""
        return []

