"""Recipe MCP Server

A Model Context Protocol server for extracting recipes from NYT Cooking
using Playwright browser automation.
"""

__version__ = "0.1.0"
__author__ = "Edwin Avalos"
__email__ = "edwinavalos@example.com"

from .models import Recipe, Ingredient, RecipeMetadata
from .server import RecipeMCPServer

__all__ = [
    "Recipe",
    "Ingredient", 
    "RecipeMetadata",
    "RecipeMCPServer",
]