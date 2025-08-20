"""MCP Server implementation for recipe extraction with compliance integration."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from pydantic import BaseModel, Field, HttpUrl, field_validator

from .models import Recipe, ExtractionResult, ComplianceStatus
from .extractor import NYTCookingExtractor
from .compliance import ensure_compliance, get_compliance_status, get_daily_usage


logger = logging.getLogger(__name__)


class ExtractRecipeArgs(BaseModel):
    """Arguments for recipe extraction."""
    
    url: HttpUrl = Field(..., description="Recipe URL to extract (NYT Cooking supported)")
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
    
    @field_validator('url')
    @classmethod
    def validate_supported_url(cls, v):
        """Validate that the URL is from a supported site."""
        url_str = str(v)
        if not url_str.startswith("https://cooking.nytimes.com/recipes/"):
            raise ValueError("Only NYT Cooking recipe URLs are currently supported")
        return v


class ValidateUrlArgs(BaseModel):
    """Arguments for URL validation."""
    
    url: HttpUrl = Field(..., description="URL to validate")


class UsageStatsResponse(BaseModel):
    """Response for usage statistics."""
    
    date: str = Field(..., description="Date of usage statistics")
    usage_count: int = Field(..., description="Number of extractions today")
    daily_limit: int = Field(..., description="Daily extraction limit")
    remaining: int = Field(..., description="Remaining extractions today")
    session_id: str = Field(..., description="Current session ID")


class ComplianceStatusResponse(BaseModel):
    """Response for compliance status."""
    
    status: ComplianceStatus = Field(..., description="Current compliance status")
    daily_usage: UsageStatsResponse = Field(..., description="Daily usage statistics")
    server_health: str = Field(..., description="Server health status")


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
        @ensure_compliance()
        async def extract_recipe(args: ExtractRecipeArgs) -> ExtractionResult:
            """Extract recipe data from supported recipe websites.
            
            This tool extracts complete recipe information from supported recipe URLs,
            including ingredients, instructions, metadata, and optionally nutrition
            information. Currently supports NYT Cooking (requires subscription).
            
            Compliance features:
            - Daily extraction limits to respect site resources
            - Rate limiting to prevent overuse
            - Session tracking for compliance monitoring
            
            Args:
                args: Extraction parameters including URL and options
                
            Returns:
                ExtractionResult with recipe data, compliance info, or error information
            """
            if not self.extractor:
                return ExtractionResult(
                    success=False,
                    error="Extractor not initialized",
                    extraction_time=0.0
                )
            
            try:
                logger.info(f"Starting compliant extraction from: {args.url}")
                result = await self.extractor.extract_recipe(
                    url=str(args.url),
                    include_nutrition=args.include_nutrition,
                    include_reviews=args.include_reviews,
                    timeout=args.timeout
                )
                
                if result.success:
                    logger.info(f"Successfully extracted recipe: {result.recipe.title if result.recipe else 'Unknown'}")
                
                return result
                
            except Exception as e:
                logger.exception("Failed to extract recipe")
                return ExtractionResult(
                    success=False,
                    error=f"Extraction failed: {str(e)}",
                    extraction_time=0.0
                )
        
        @self.app.tool()
        async def validate_url(args: ValidateUrlArgs) -> Dict[str, Any]:
            """Validate if URL is a supported recipe URL.
            
            This tool checks if the provided URL is from a supported recipe site
            and has the correct format for extraction. Currently supports:
            - NYT Cooking (cooking.nytimes.com)
            
            Args:
                args: Validation arguments with URL
                
            Returns:
                Dictionary with validation result, supported site info, and format requirements
            """
            url_str = str(args.url)
            
            # Check supported sites
            supported_sites = {
                "cooking.nytimes.com": {
                    "name": "NYT Cooking",
                    "pattern": "https://cooking.nytimes.com/recipes/",
                    "format": "https://cooking.nytimes.com/recipes/{recipe-id}-{recipe-name}",
                    "requires_subscription": True
                }
            }
            
            # Check if it's a supported site
            site_info = None
            for domain, info in supported_sites.items():
                if domain in url_str:
                    site_info = info
                    break
            
            if not site_info:
                return {
                    "valid": False,
                    "reason": "Unsupported recipe site",
                    "supported_sites": list(supported_sites.keys()),
                    "url": url_str
                }
            
            # Site-specific validation
            if "cooking.nytimes.com" in url_str:
                if not url_str.startswith("https://cooking.nytimes.com/recipes/"):
                    return {
                        "valid": False,
                        "reason": "Not a NYT Cooking recipe URL",
                        "expected_format": site_info["format"],
                        "site": site_info["name"]
                    }
                
                # Basic format validation
                parts = url_str.split("/")
                if len(parts) < 5:
                    return {
                        "valid": False,
                        "reason": "Invalid URL format",
                        "expected_format": site_info["format"],
                        "site": site_info["name"]
                    }
                
                recipe_part = parts[4]
                if not recipe_part or "-" not in recipe_part:
                    return {
                        "valid": False,
                        "reason": "Invalid recipe identifier format",
                        "expected_format": "Recipe ID should contain numbers and recipe name",
                        "site": site_info["name"]
                    }
                
                return {
                    "valid": True,
                    "url": url_str,
                    "site": site_info["name"],
                    "recipe_id": recipe_part.split("-")[0] if "-" in recipe_part else None,
                    "requires_subscription": site_info["requires_subscription"]
                }
            
            return {
                "valid": False,
                "reason": "Unknown validation error",
                "url": url_str
            }
        
        @self.app.tool()
        async def get_compliance_status() -> ComplianceStatusResponse:
            """Get current compliance status and usage statistics.
            
            This tool provides information about the current compliance status,
            including daily usage limits, rate limiting status, and server health.
            Useful for monitoring extraction usage and ensuring compliance with
            site terms of service.
            
            Returns:
                ComplianceStatusResponse with detailed compliance information
            """
            try:
                usage_stats = await get_daily_usage()
                
                # Determine compliance status
                status = ComplianceStatus.COMPLIANT
                if usage_stats["remaining"] <= 0:
                    status = ComplianceStatus.RATE_LIMITED
                
                return ComplianceStatusResponse(
                    status=status,
                    daily_usage=UsageStatsResponse(**usage_stats),
                    server_health="healthy" if self.extractor else "extractor_not_initialized"
                )
            except Exception as e:
                logger.exception("Failed to get compliance status")
                return ComplianceStatusResponse(
                    status=ComplianceStatus.UNKNOWN,
                    daily_usage=UsageStatsResponse(
                        date="unknown",
                        usage_count=0,
                        daily_limit=50,
                        remaining=0,
                        session_id="error"
                    ),
                    server_health=f"error: {str(e)}"
                )
        
        @self.app.tool()
        async def get_daily_usage() -> UsageStatsResponse:
            """Get daily usage statistics for recipe extraction.
            
            This tool provides detailed information about current daily usage,
            including how many extractions have been performed today, the daily
            limit, and how many extractions remain.
            
            Returns:
                UsageStatsResponse with current usage statistics
            """
            try:
                usage_stats = await get_daily_usage()
                return UsageStatsResponse(**usage_stats)
            except Exception as e:
                logger.exception("Failed to get daily usage")
                return UsageStatsResponse(
                    date="unknown",
                    usage_count=0,
                    daily_limit=50,
                    remaining=0,
                    session_id="error"
                )
        
        @self.app.tool()
        async def get_server_status() -> Dict[str, Any]:
            """Get the current status of the recipe extraction server.
            
            Returns comprehensive information about server health, extractor status,
            configuration, and supported features.
            
            Returns:
                Dictionary with detailed server status information
            """
            try:
                compliance_status = await get_compliance_status()
                
                return {
                    "status": "running",
                    "server_health": "healthy",
                    "extractor_initialized": self.extractor is not None,
                    "configuration": {
                        "headless_mode": self.headless,
                        "debug_mode": self.debug
                    },
                    "supported_sites": [
                        {
                            "domain": "cooking.nytimes.com",
                            "name": "NYT Cooking",
                            "requires_subscription": True
                        }
                    ],
                    "compliance": {
                        "daily_usage": compliance_status["usage_count"],
                        "daily_limit": compliance_status["daily_limit"],
                        "remaining_today": compliance_status["remaining"]
                    },
                    "features": [
                        "recipe_extraction",
                        "url_validation", 
                        "compliance_monitoring",
                        "usage_statistics",
                        "rate_limiting"
                    ]
                }
            except Exception as e:
                logger.exception("Failed to get server status")
                return {
                    "status": "running",
                    "server_health": "degraded",
                    "error": str(e),
                    "extractor_initialized": self.extractor is not None
                }
    
    async def start(self):
        """Start the MCP server and initialize components."""
        logger.info("Starting Recipe MCP Server with compliance framework")
        
        # Initialize the extractor
        self.extractor = NYTCookingExtractor(
            headless=self.headless,
            debug=self.debug
        )
        await self.extractor.start()
        
        # Log compliance initialization
        compliance_status = await get_compliance_status()
        logger.info(f"Compliance framework initialized - Daily usage: {compliance_status['usage_count']}/{compliance_status['daily_limit']}")
        
        logger.info("Recipe MCP Server started successfully with compliance monitoring")
    
    async def stop(self):
        """Stop the MCP server and cleanup resources."""
        logger.info("Stopping Recipe MCP Server")
        
        if self.extractor:
            await self.extractor.stop()
            self.extractor = None
        
        # Log final compliance status
        try:
            compliance_status = await get_compliance_status()
            logger.info(f"Final compliance status - Daily usage: {compliance_status['usage_count']}/{compliance_status['daily_limit']}")
        except Exception as e:
            logger.warning(f"Could not get final compliance status: {e}")
        
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