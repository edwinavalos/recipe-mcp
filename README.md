# Recipe MCP Server

A Model Context Protocol (MCP) server for extracting recipes from NYT Cooking using Playwright browser automation.

## Project Overview

This MCP server provides programmatic access to NYT Cooking recipes for personal use by subscribers. It extracts recipe data including ingredients, instructions, and metadata using browser automation with Playwright.

## Features

- **Recipe Extraction**: Extract complete recipe data from NYT Cooking URLs
- **Ingredients Focus**: Specialized extraction of ingredients for integration with Google Keep
- **Browser Automation**: Playwright-based automation for reliable data extraction
- **MCP Protocol**: Full compliance with Model Context Protocol specification
- **FastMCP Framework**: Built on FastMCP for efficient server implementation

## Prerequisites

- Valid NYT Cooking subscription
- Python 3.9+
- Chrome/Chromium browser for Playwright

## Installation

```bash
# Clone the repository
git clone https://github.com/edwinavalos/recipe-mcp.git
cd recipe-mcp

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Usage

```bash
# Start the MCP server
python -m recipe_mcp

# The server will be available for MCP client connections
```

## Project Structure

```
recipe-mcp/
├── recipe_mcp/           # Main package
│   ├── __init__.py
│   ├── server.py         # MCP server implementation
│   ├── extractor.py      # Recipe extraction logic
│   └── models.py         # Data models
├── tests/                # Test suite
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Legal Compliance

This tool is designed for personal use by NYT Cooking subscribers only. It respects the terms of service and is intended for legitimate personal recipe management and meal planning purposes.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check

# Format code
ruff format
```

## Contributing

This is a private repository for personal use. Contributions are not currently accepted.

## License

Private - All rights reserved