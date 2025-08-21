# Recipe MCP Server

> !!!!! This is a WIP !!!!!! I'm verifying that this whole vibe coded thing does all it says it does so use at your own risk. One thing I'm confused about is that I expected to get paywalled for the recipe but I wasn't so maybe it just works. But this thing completely rewrote itself after getting into a weird asyncio obsession. It was a fun experiment, and cuts an hour long activity to no time that I struggle with focusing on with a toddler running havoc.

## The developers work flow

We usually get recipes from the NYT and we add it to the grocery list under a "Meals for the week" Top level item in a Google Keep list. Then on Saturday morning we put on cartoons for the kid, and build the menu for the menu for the week. Getting items notated down into our preferred tools is heavy on context switching which is what I'm bad at.

In Claude I ask it to read the urls in the grocery list "Meals for the week" section. It fetches the urls, gets the ingredients, adds the items to the ingredients list, and then sorts them into categories organized by the way we do our grocery shopping at the store. Next step is that I plan to take over the world, cause this was a cool thing I've wanted to do as a 'quick project' and I knocked it out in a day and a halfish of prompting infrequently. Shoutout to [omnara](https://github.com/omnara-ai/omnara) for letting me answer questions from Claude, or prompt it for the next steps while on a walk.

Who knows if the code sucks, at this point it works well enough for me, maybe for you too.

A Model Context Protocol (MCP) server for extracting recipes rom NYT Cooking using Playwright browser automation.

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

## Fair Use

It is my understanding that this is fair use under the [terms of service](https://help.nytimes.com/115014893428-Terms-of-Service). But please also read it yourself and make your own judgement. I haven't encountered a paywall on NYT links so far, but will monitor if it runs into things.


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

This is a repository for personal use. Contributions are not currently accepted. If you want to modify this, fork it, and let me know and I'll probably open it up after doing some significant due diligence on all the code. This was very very vibe coded.
