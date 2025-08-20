"""MCP Server implementation for recipe extraction."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from pydantic import BaseModel, Field, HttpUrl

from .models import Recipe, ExtractionResult
from .extractor import NYTCookingExtractor


logger = logging.getLogger(__name__)


class ExtractRecipeArgs(BaseModel):
    """Arguments for recipe extraction."""
    
    url: HttpUrl = Field(..., description="NYT Cooking recipe URL to extract")
    include_nutrition: bool = Field(
        default=True, 
        description="Whether to extract nutritional information"
    )
    include_reviews: bool = Field(
        default=False,
        description="Whether to extract review information"
    )
    timeout: int = Field(
        default=30,
        description="Timeout in seconds for extraction"
    )


class RecipeMCPServer:
    """MCP Server for NYT Cooking recipe extraction."""
    
    def __init__(self, headless: bool = True, debug: bool = False):
        """Initialize the MCP server.
        
        Args:
            headless: Whether to run browser in headless mode
            debug: Enable debug logging
        """
        self.app = FastMCP("Recipe MCP Server")
        self.headless = headless
        self.debug = debug
        self.extractor: Optional[NYTCookingExtractor] = None
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        
        self._setup_tools()
    
    def _setup_tools(self):
        """Set up MCP tools."""
        
        @self.app.tool()
        async def extract_recipe(args: ExtractRecipeArgs) -> ExtractionResult:
            """Extract recipe data from NYT Cooking URL.
            
            This tool extracts complete recipe information from NYT Cooking URLs,
            including ingredients, instructions, metadata, and optionally nutrition
            information. Requires a valid NYT Cooking subscription.
            
            Args:
                args: Extraction parameters including URL and options
                
            Returns:
                ExtractionResult with recipe data or error information
            """
            if not self.extractor:
                return ExtractionResult(
                    success=False,
                    error="Extractor not initialized",
                    extraction_time=0.0
                )
            
            try:
                result = await self.extractor.extract_recipe(
                    url=str(args.url),
                    include_nutrition=args.include_nutrition,
                    include_reviews=args.include_reviews,
                    timeout=args.timeout
                )
                return result
                
            except Exception as e:
                logger.exception("Failed to extract recipe")
                return ExtractionResult(
                    success=False,
                    error=f"Extraction failed: {str(e)}",
                    extraction_time=0.0
                )
        
        @self.app.tool()
        async def validate_nyt_url(url: HttpUrl) -> Dict[str, Any]:
            """Validate if URL is a supported NYT Cooking recipe URL.
            
            This tool checks if the provided URL is a valid NYT Cooking recipe
            URL that can be processed by the extraction tool.
            
            Args:
                url: URL to validate
                
            Returns:
                Dictionary with validation result and details
            """
            url_str = str(url)
            
            # Check if it's a NYT Cooking URL
            if not url_str.startswith("https://cooking.nytimes.com/recipes/"):
                return {
                    "valid": False,
                    "reason": "Not a NYT Cooking recipe URL",
                    "expected_format": "https://cooking.nytimes.com/recipes/{recipe-id}-{recipe-name}"
                }
            
            # Basic format validation
            parts = url_str.split("/")
            if len(parts) < 5:
                return {
                    "valid": False,
                    "reason": "Invalid URL format",
                    "expected_format": "https://cooking.nytimes.com/recipes/{recipe-id}-{recipe-name}"
                }
            
            recipe_part = parts[4]
            if not recipe_part or "-" not in recipe_part:
                return {
                    "valid": False,
                    "reason": "Invalid recipe identifier format",
                    "expected_format": "Recipe ID should contain numbers and recipe name"
                }
            
            return {
                "valid": True,
                "url": url_str,
                "recipe_id": recipe_part.split("-")[0] if "-" in recipe_part else None
            }
        
        @self.app.tool()
        async def get_server_status() -> Dict[str, Any]:
            """Get the current status of the recipe extraction server.
            
            Returns information about server health, extractor status,
            and configuration.
            
            Returns:
                Dictionary with server status information
            """
            return {
                "status": "running",
                "extractor_initialized": self.extractor is not None,
                "headless_mode": self.headless,
                "debug_mode": self.debug,
                "supported_sites": ["cooking.nytimes.com"]
            }
    
    async def start(self):
        """Start the MCP server and initialize components."""
        logger.info("Starting Recipe MCP Server")
        
        # Initialize the extractor
        self.extractor = NYTCookingExtractor(
            headless=self.headless,
            debug=self.debug
        )
        await self.extractor.start()
        
        logger.info("Recipe MCP Server started successfully")
    
    async def stop(self):
        """Stop the MCP server and cleanup resources."""
        logger.info("Stopping Recipe MCP Server")
        
        if self.extractor:
            await self.extractor.stop()
            self.extractor = None
        
        logger.info("Recipe MCP Server stopped")
    
    @asynccontextmanager
    async def lifespan(self):
        """Context manager for server lifecycle."""
        await self.start()
        try:
            yield
        finally:
            await self.stop()
    
    def run(self, host: str = "localhost", port: int = 3000):
        """Run the MCP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        async def main():
            async with self.lifespan():
                await self.app.run(host=host, port=port)
        
        asyncio.run(main())


async def main():
    """Main entry point for the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Recipe MCP Server")
    parser.add_argument(
        "--host", 
        default="localhost", 
        help="Host to bind to (default: localhost)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=3000, 
        help="Port to bind to (default: 3000)"
    )
    parser.add_argument(
        "--no-headless", 
        action="store_true", 
        help="Run browser in non-headless mode"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    server = RecipeMCPServer(
        headless=not args.no_headless,
        debug=args.debug
    )
    
    try:
        server.run(host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    asyncio.run(main())