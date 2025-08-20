# Recipe MCP Server API Documentation

This document describes the MCP tools and resources available in the Recipe MCP Server.

## Tools

### extract_recipe

Extracts recipe data from a NYT Cooking URL.

**Arguments:**
- `url` (string, required): NYT Cooking recipe URL to extract
- `include_nutrition` (boolean, optional, default=true): Whether to extract nutritional information
- `include_reviews` (boolean, optional, default=false): Whether to extract review information  
- `timeout` (integer, optional, default=30): Timeout in seconds for extraction

**Returns:**
- `ExtractionResult` object containing:
  - `success` (boolean): Whether extraction was successful
  - `recipe` (Recipe, optional): Extracted recipe data if successful
  - `error` (string, optional): Error message if extraction failed
  - `warnings` (array): Non-fatal warnings during extraction
  - `extraction_time` (number): Time taken for extraction in seconds

**Example:**
```json
{
  "tool": "extract_recipe",
  "arguments": {
    "url": "https://cooking.nytimes.com/recipes/1018069-chocolate-chip-cookies",
    "include_nutrition": true,
    "include_reviews": false,
    "timeout": 30
  }
}
```

### validate_nyt_url

Validates if a URL is a supported NYT Cooking recipe URL.

**Arguments:**
- `url` (string, required): URL to validate

**Returns:**
- Object containing:
  - `valid` (boolean): Whether the URL is valid
  - `reason` (string, optional): Reason if URL is invalid
  - `expected_format` (string, optional): Expected URL format
  - `recipe_id` (string, optional): Extracted recipe ID if valid

**Example:**
```json
{
  "tool": "validate_nyt_url", 
  "arguments": {
    "url": "https://cooking.nytimes.com/recipes/1018069-chocolate-chip-cookies"
  }
}
```

### get_server_status

Returns the current status of the recipe extraction server.

**Arguments:** None

**Returns:**
- Object containing:
  - `status` (string): Server status ("running", "stopped", etc.)
  - `extractor_initialized` (boolean): Whether the extractor is ready
  - `headless_mode` (boolean): Whether browser runs in headless mode
  - `debug_mode` (boolean): Whether debug logging is enabled
  - `supported_sites` (array): List of supported recipe sites

**Example:**
```json
{
  "tool": "get_server_status",
  "arguments": {}
}
```

## Data Models

### Recipe

Complete recipe data structure.

**Fields:**
- `metadata` (RecipeMetadata): Recipe metadata and source information
- `ingredients` (array of Ingredient): List of recipe ingredients
- `instructions` (array of string): Step-by-step cooking instructions
- `nutrition` (NutritionInfo, optional): Nutritional information
- `notes` (array of string): Additional recipe notes
- `equipment` (array of string): Required cooking equipment

### RecipeMetadata

Metadata about a recipe.

**Fields:**
- `source_url` (string): Original recipe URL
- `title` (string): Recipe title
- `author` (string, optional): Recipe author
- `description` (string, optional): Recipe description
- `prep_time` (string, optional): Preparation time
- `cook_time` (string, optional): Cooking time
- `total_time` (string, optional): Total time
- `servings` (string, optional): Number of servings
- `difficulty` (string, optional): Difficulty level
- `cuisine` (string, optional): Cuisine type
- `tags` (array of string): Recipe tags
- `rating` (number, optional): Recipe rating
- `review_count` (integer, optional): Number of reviews
- `published_date` (datetime, optional): Publication date
- `extracted_at` (datetime): Extraction timestamp

### Ingredient

Represents a recipe ingredient with parsed components.

**Fields:**
- `name` (string): Name of the ingredient
- `quantity` (string, optional): Quantity/amount
- `unit` (string, optional): Unit of measurement
- `preparation` (string, optional): Preparation notes (chopped, diced, etc.)
- `raw_text` (string): Original ingredient text as written

### NutritionInfo

Nutritional information for a recipe.

**Fields:**
- `calories` (integer, optional): Calories per serving
- `protein` (string, optional): Protein content
- `carbohydrates` (string, optional): Carbohydrate content
- `fat` (string, optional): Fat content
- `fiber` (string, optional): Fiber content
- `sugar` (string, optional): Sugar content
- `sodium` (string, optional): Sodium content

## Error Handling

The server handles various error conditions:

- **Invalid URLs**: Returns validation error for non-NYT Cooking URLs
- **Network timeouts**: Configurable timeout for page loading
- **Page load failures**: HTTP errors and missing content
- **Parsing errors**: Graceful degradation when recipe structure changes
- **Browser issues**: Automatic browser restart and retry logic

## Rate Limiting

The server respects NYT Cooking's servers by:
- Using realistic browser headers and behavior
- Implementing reasonable delays between requests
- Avoiding aggressive scraping patterns
- Running in headless mode by default for efficiency

## Legal Compliance

This server is designed for personal use by NYT Cooking subscribers only. It:
- Requires a valid subscription for access
- Respects robots.txt and terms of service
- Does not redistribute copyrighted content
- Focuses on personal recipe management use cases