"""
LLM Tool - OpenAI integration for generating insights and analysis.
Extends COREUS BaseTool for LLM capabilities.
"""
from typing import Dict, Any, List, Optional
import json
from core.abstractions.base_tool import BaseTool
from core.logger import setup_logger
from core.resilience.decorators import with_retry, with_circuit_breaker, handle_errors

logger = setup_logger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. LLM functionality will be unavailable.")


class LLMTool(BaseTool):
    """
    LLM Tool - OpenAI integration for competitive intelligence analysis.
    
    Responsibilities:
    - Execute LLM prompts with structured output
    - Handle OpenAI API calls with error handling
    - Parse structured responses (JSON Schema + Function Calling)
    - Track token usage and costs
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize LLM Tool.
        
        Args:
            name: Tool identifier
            config: Configuration dict with:
                   - api_key: str (optional, uses OPENAI_API_KEY env var if not provided)
                   - model: str (default: "gpt-4o-mini")
                   - temperature: float (default: 0.2) - Low for analytical, consistent results
                   - max_tokens: int (default: 3000) - Increased for comprehensive structured output
        """
        super().__init__(name, config)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is required. Install with: pip install openai")
        
        self.api_key = config.get("api_key") or self._get_api_key_from_env()
        self.model = config.get("model", "gpt-4o-mini")
        self.temperature = config.get("temperature", 0.2)  # Low for analytical tasks
        self.max_tokens = config.get("max_tokens", 3000)  # Increased for comprehensive reports
        
        self.client = None
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get OpenAI API key from environment variable."""
        import os
        return os.getenv("OPENAI_API_KEY")
    
    async def initialize(self):
        """Initialize OpenAI client."""
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or provide in config.")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"LLMTool {self.name} initialized with model: {self.model}")
    
    @handle_errors(reraise=True, log_errors=True)
    @with_circuit_breaker(failure_threshold=5, timeout=60.0)
    @with_retry(max_attempts=3, initial_delay=1.0, exponential_base=2.0)
    async def execute(
        self,
        system_prompt: str,
        user_prompt: str,
        function_schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute LLM prompt with structured output support.
        
        Args:
            system_prompt: System message/prompt
            user_prompt: User message/prompt
            function_schema: Optional JSON Schema for structured output (function calling)
            **kwargs: Additional OpenAI API parameters
        
        Returns:
            Dict with:
            - content: str - LLM response text
            - function_call: Optional[Dict] - Function call result if function_schema provided
            - tokens: Dict - Token usage statistics
        """
        if not self.client:
            await self.initialize()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Prepare function calling if schema provided
        functions = None
        function_call = None
        if function_schema:
            functions = [function_schema]
            function_call = {"name": function_schema["name"]}
        
        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                functions=functions,
                function_call=function_call,
                **kwargs
            )
            
            # Extract response
            choice = response.choices[0]
            result = {
                "content": choice.message.content or "",
                "function_call": None,
                "tokens": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            # Parse function call if present
            if choice.message.function_call:
                function_name = choice.message.function_call.name
                function_args = choice.message.function_call.arguments
                try:
                    result["function_call"] = {
                        "name": function_name,
                        "arguments": json.loads(function_args)
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse function call arguments: {e}")
                    result["function_call"] = {
                        "name": function_name,
                        "arguments": function_args  # Return raw string if parsing fails
                    }
            
            # Update token usage tracking
            self._token_usage["prompt_tokens"] += result["tokens"]["prompt_tokens"]
            self._token_usage["completion_tokens"] += result["tokens"]["completion_tokens"]
            self._token_usage["total_tokens"] += result["tokens"]["total_tokens"]
            
            logger.debug(f"LLM call completed. Tokens: {result['tokens']['total_tokens']}")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def get_token_usage(self) -> Dict[str, int]:
        """Get cumulative token usage statistics."""
        return self._token_usage.copy()
    
    def reset_token_usage(self):
        """Reset token usage statistics."""
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get LLM Tool parameter schema.
        
        Returns:
            JSON schema for tool parameters
        """
        return {
            "name": self.name,
            "description": "LLM tool for generating insights and analysis using OpenAI",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_prompt": {
                        "type": "string",
                        "description": "System message/prompt for the LLM"
                    },
                    "user_prompt": {
                        "type": "string",
                        "description": "User message/prompt for the LLM"
                    },
                    "function_schema": {
                        "type": "object",
                        "description": "Optional JSON Schema for structured output (function calling)"
                    }
                },
                "required": ["system_prompt", "user_prompt"]
            }
        }

