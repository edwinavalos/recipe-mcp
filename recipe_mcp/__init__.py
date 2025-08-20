"""Recipe MCP Server

A Model Context Protocol server for extracting recipes from supported recipe sites
using browser automation with compliance monitoring and rate limiting.

Supported sites:
- NYT Cooking (requires subscription)

Features:
- Recipe extraction with structured data
- Compliance monitoring and rate limiting
- Daily usage tracking
- Respectful web scraping practices
"""

__version__ = "0.1.0"
__author__ = "Edwin Avalos"
__email__ = "edwinavalos@example.com"

from .models import (
    Recipe, 
    Ingredient, 
    ExtractionResult,
    ComplianceInfo,
    ComplianceStatus,
    ExtractionMethod
)
from .server import RecipeMCPServer
from .compliance import ComplianceMonitor, ensure_compliance

__all__ = [
    "Recipe",
    "Ingredient", 
    "ExtractionResult",
    "ComplianceInfo",
    "ComplianceStatus",
    "ExtractionMethod",
    "RecipeMCPServer",
    "ComplianceMonitor",
    "ensure_compliance",
]