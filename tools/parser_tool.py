"""
Site-specific parser tool with registry pattern.
Automatically selects the correct parser based on URL.
"""
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from core.abstractions.base_tool import BaseTool
from tools.parsers import (
    BaseParser,
    VercelParser,
    NetlifyParser,
    CloudflarePagesParser
)
from core.logger import setup_logger

logger = setup_logger(__name__)


class ParserTool(BaseTool):
    """
    Parser tool with registry pattern for site-specific parsers.
    Automatically selects parser based on URL domain.
    """
    
    # Parser registry: domain -> parser class
    PARSER_REGISTRY: Dict[str, type] = {
        "vercel.com": VercelParser,
        "www.vercel.com": VercelParser,
        "netlify.com": NetlifyParser,
        "www.netlify.com": NetlifyParser,
        # Cloudflare Pages (pricing hosted on root domain)
        "pages.cloudflare.com": CloudflarePagesParser,
        "www.pages.cloudflare.com": CloudflarePagesParser,
    }
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize parser tool.
        
        Args:
            name: Tool name
            config: Configuration dict (currently unused, reserved for future)
        """
        super().__init__(name, config)
        self._parsers: Dict[str, BaseParser] = {}
    
    def _get_parser_for_url(self, url: str) -> Optional[BaseParser]:
        """
        Get appropriate parser for URL.
        
        Args:
            url: URL to parse
        
        Returns:
            Parser instance or None if no parser found
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove 'www.' prefix for matching
            domain_key = domain.replace("www.", "")
            
            # Try exact match first
            if domain_key in self.PARSER_REGISTRY:
                parser_class = self.PARSER_REGISTRY[domain_key]
            elif domain in self.PARSER_REGISTRY:
                parser_class = self.PARSER_REGISTRY[domain]
            else:
                # Try partial match (e.g., "vercel.com" in "app.vercel.com")
                for registry_domain, parser_class in self.PARSER_REGISTRY.items():
                    if registry_domain in domain_key or domain_key in registry_domain:
                        break
                else:
                    logger.warning(f"No parser found for domain: {domain}")
                    return None
            
            # Cache parser instance
            if domain_key not in self._parsers:
                self._parsers[domain_key] = parser_class()
                logger.debug(f"Created parser for domain: {domain_key}")
            
            return self._parsers[domain_key]
            
        except Exception as e:
            logger.error(f"Error getting parser for URL {url}: {e}")
            return None
    
    async def execute(self, url: str, raw_html: str, **kwargs) -> Dict[str, Any]:
        """
        Parse HTML content using site-specific parser.
        
        Args:
            url: Source URL
            raw_html: Raw HTML content from crawler
            **kwargs: Additional options (unused, reserved for future)
        
        Returns:
            Dict with parsed data:
            - pricing: Dict with tier pricing
            - tiers: List of tier information
            - limits: Dict with service limits
            - features: List of features
            - source: Parser source name
            - success: bool
        """
        try:
            parser = self._get_parser_for_url(url)
            
            if not parser:
                logger.warning(f"No parser available for URL: {url}")
                return {
                    "pricing": {},
                    "tiers": [],
                    "limits": {},
                    "features": [],
                    "source": "unknown",
                    "url": url,
                    "success": False,
                    "error": f"No parser found for URL: {url}"
                }
            
            logger.info(f"Parsing {url} with {parser.site_name} parser")
            
            # Parse HTML
            parsed_data = parser.parse(raw_html, url)
            parsed_data["success"] = True
            
            logger.info(f"Successfully parsed {url}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return {
                "pricing": {},
                "tiers": [],
                "limits": {},
                "features": [],
                "source": "unknown",
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool parameter schema.
        
        Returns:
            JSON schema for tool parameters
        """
        return {
            "name": self.name,
            "description": "Parse HTML content using site-specific parser (Vercel, Netlify, Cloudflare Pages)",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Source URL"
                    },
                    "raw_html": {
                        "type": "string",
                        "description": "Raw HTML content to parse"
                    }
                },
                "required": ["url", "raw_html"]
            }
        }
    
    @classmethod
    def register_parser(cls, domain: str, parser_class: type):
        """
        Register a new parser for a domain.
        
        Args:
            domain: Domain name (e.g., "render.com")
            parser_class: Parser class (must extend BaseParser)
        """
        cls.PARSER_REGISTRY[domain] = parser_class
        logger.info(f"Registered parser for domain: {domain}")
