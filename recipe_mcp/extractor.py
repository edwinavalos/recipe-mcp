"""Recipe extraction implementation using Playwright."""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup

from .models import (
    Recipe, 
    Ingredient, 
    RecipeMetadata, 
    NutritionInfo, 
    ExtractionResult
)


logger = logging.getLogger(__name__)


class NYTCookingExtractor:
    """Extractor for NYT Cooking recipes using Playwright."""
    
    def __init__(self, headless: bool = True, debug: bool = False):
        """Initialize the extractor.
        
        Args:
            headless: Run browser in headless mode
            debug: Enable debug logging
        """
        self.headless = headless
        self.debug = debug
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
    
    async def start(self):
        """Start the browser and initialize Playwright."""
        logger.info("Starting NYT Cooking extractor")
        
        self.playwright = await async_playwright().start()
        
        # Launch browser with appropriate settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-bgsync",
                "--disable-extensions-http-throttling",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
            ]
        )
        
        # Create browser context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        logger.info("NYT Cooking extractor started successfully")
    
    async def stop(self):
        """Stop the browser and cleanup resources."""
        logger.info("Stopping NYT Cooking extractor")
        
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        logger.info("NYT Cooking extractor stopped")
    
    async def extract_recipe(
        self,
        url: str,
        include_nutrition: bool = True,
        include_reviews: bool = False,
        timeout: int = 30
    ) -> ExtractionResult:
        """Extract recipe from NYT Cooking URL.
        
        Args:
            url: Recipe URL to extract
            include_nutrition: Whether to extract nutrition info
            include_reviews: Whether to extract review info
            timeout: Timeout in seconds
            
        Returns:
            ExtractionResult with recipe data or error
        """
        start_time = time.time()
        
        if not self.context:
            return ExtractionResult(
                success=False,
                error="Extractor not started",
                extraction_time=time.time() - start_time
            )
        
        # Validate URL
        if not self._is_valid_nyt_url(url):
            return ExtractionResult(
                success=False,
                error=f"Invalid NYT Cooking URL: {url}",
                extraction_time=time.time() - start_time
            )
        
        page = None
        try:
            logger.info(f"Extracting recipe from: {url}")
            
            # Create new page
            page = await self.context.new_page()
            
            # Navigate to recipe page
            response = await page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            
            if not response or response.status >= 400:
                return ExtractionResult(
                    success=False,
                    error=f"Failed to load page: HTTP {response.status if response else 'No response'}",
                    extraction_time=time.time() - start_time
                )
            
            # Wait for recipe content to load
            await page.wait_for_selector('[data-testid="recipe-header"]', timeout=10000)
            
            # Extract recipe data
            recipe_data = await self._extract_recipe_data(
                page, 
                include_nutrition=include_nutrition,
                include_reviews=include_reviews
            )
            
            if not recipe_data:
                return ExtractionResult(
                    success=False,
                    error="Failed to extract recipe data",
                    extraction_time=time.time() - start_time
                )
            
            # Create recipe metadata
            metadata = RecipeMetadata(
                source_url=url,
                title=recipe_data.get("title", "Unknown Recipe"),
                author=recipe_data.get("author"),
                description=recipe_data.get("description"),
                prep_time=recipe_data.get("prep_time"),
                cook_time=recipe_data.get("cook_time"),
                total_time=recipe_data.get("total_time"),
                servings=recipe_data.get("servings"),
                tags=recipe_data.get("tags", []),
                rating=recipe_data.get("rating"),
                review_count=recipe_data.get("review_count")
            )
            
            # Parse ingredients
            ingredients = []
            for ing_text in recipe_data.get("ingredients", []):
                ingredient = self._parse_ingredient(ing_text)
                ingredients.append(ingredient)
            
            # Create nutrition info if available
            nutrition = None
            if include_nutrition and recipe_data.get("nutrition"):
                nutrition = NutritionInfo(**recipe_data["nutrition"])
            
            # Create recipe
            recipe = Recipe(
                metadata=metadata,
                ingredients=ingredients,
                instructions=recipe_data.get("instructions", []),
                nutrition=nutrition,
                notes=recipe_data.get("notes", []),
                equipment=recipe_data.get("equipment", [])
            )
            
            logger.info(f"Successfully extracted recipe: {recipe.metadata.title}")
            
            return ExtractionResult(
                success=True,
                recipe=recipe,
                extraction_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.exception("Failed to extract recipe")
            return ExtractionResult(
                success=False,
                error=f"Extraction error: {str(e)}",
                extraction_time=time.time() - start_time
            )
        
        finally:
            if page:
                await page.close()
    
    def _is_valid_nyt_url(self, url: str) -> bool:
        """Check if URL is a valid NYT Cooking recipe URL."""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc == "cooking.nytimes.com" and
                parsed.path.startswith("/recipes/")
            )
        except Exception:
            return False
    
    async def _extract_recipe_data(
        self, 
        page: Page, 
        include_nutrition: bool = True,
        include_reviews: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Extract recipe data from the page.
        
        Args:
            page: Playwright page object
            include_nutrition: Extract nutrition information
            include_reviews: Extract review information
            
        Returns:
            Dictionary with extracted recipe data
        """
        try:
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            recipe_data = {}
            
            # Extract title
            title_elem = soup.find('h1', {'data-testid': 'recipe-title'})
            if title_elem:
                recipe_data['title'] = title_elem.get_text(strip=True)
            
            # Extract author
            author_elem = soup.find('span', {'data-testid': 'recipe-author'})
            if author_elem:
                recipe_data['author'] = author_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = soup.find('div', {'data-testid': 'recipe-summary'})
            if desc_elem:
                recipe_data['description'] = desc_elem.get_text(strip=True)
            
            # Extract timing information
            timing_section = soup.find('section', {'data-testid': 'recipe-timing'})
            if timing_section:
                timing_items = timing_section.find_all('div', class_='recipe-time-item')
                for item in timing_items:
                    label = item.find('dt')
                    value = item.find('dd')
                    if label and value:
                        label_text = label.get_text(strip=True).lower()
                        if 'prep' in label_text:
                            recipe_data['prep_time'] = value.get_text(strip=True)
                        elif 'cook' in label_text:
                            recipe_data['cook_time'] = value.get_text(strip=True)
                        elif 'total' in label_text:
                            recipe_data['total_time'] = value.get_text(strip=True)
            
            # Extract servings
            servings_elem = soup.find('[data-testid="recipe-servings"]')
            if servings_elem:
                recipe_data['servings'] = servings_elem.get_text(strip=True)
            
            # Extract ingredients
            ingredients = []
            ingredient_sections = soup.find_all('[data-testid="recipe-ingredient"]')
            for ingredient_elem in ingredient_sections:
                ingredient_text = ingredient_elem.get_text(strip=True)
                if ingredient_text:
                    ingredients.append(ingredient_text)
            
            recipe_data['ingredients'] = ingredients
            
            # Extract instructions
            instructions = []
            instruction_sections = soup.find_all('[data-testid="recipe-instruction"]')
            for instruction_elem in instruction_sections:
                instruction_text = instruction_elem.get_text(strip=True)
                if instruction_text:
                    instructions.append(instruction_text)
            
            recipe_data['instructions'] = instructions
            
            # Extract tags
            tags = []
            tag_elements = soup.find_all('a', class_='tag-link')
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            
            recipe_data['tags'] = tags
            
            # Extract nutrition info if requested
            if include_nutrition:
                nutrition_data = await self._extract_nutrition_info(soup)
                if nutrition_data:
                    recipe_data['nutrition'] = nutrition_data
            
            # Extract review info if requested
            if include_reviews:
                review_data = await self._extract_review_info(soup)
                if review_data:
                    recipe_data.update(review_data)
            
            return recipe_data
            
        except Exception as e:
            logger.exception("Failed to extract recipe data from page")
            return None
    
    async def _extract_nutrition_info(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract nutrition information from the page."""
        try:
            nutrition_section = soup.find('section', {'data-testid': 'nutrition-summary'})
            if not nutrition_section:
                return None
            
            nutrition_data = {}
            
            # Look for common nutrition fields
            nutrition_items = nutrition_section.find_all('div', class_='nutrition-item')
            for item in nutrition_items:
                label = item.find('dt') or item.find('.nutrition-label')
                value = item.find('dd') or item.find('.nutrition-value')
                
                if label and value:
                    label_text = label.get_text(strip=True).lower()
                    value_text = value.get_text(strip=True)
                    
                    if 'calories' in label_text:
                        try:
                            nutrition_data['calories'] = int(value_text.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif 'protein' in label_text:
                        nutrition_data['protein'] = value_text
                    elif 'carb' in label_text:
                        nutrition_data['carbohydrates'] = value_text
                    elif 'fat' in label_text:
                        nutrition_data['fat'] = value_text
                    elif 'fiber' in label_text:
                        nutrition_data['fiber'] = value_text
                    elif 'sugar' in label_text:
                        nutrition_data['sugar'] = value_text
                    elif 'sodium' in label_text:
                        nutrition_data['sodium'] = value_text
            
            return nutrition_data if nutrition_data else None
            
        except Exception as e:
            logger.debug(f"Failed to extract nutrition info: {e}")
            return None
    
    async def _extract_review_info(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract review information from the page."""
        try:
            review_data = {}
            
            # Extract rating
            rating_elem = soup.find('[data-testid="recipe-rating"]')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating_data = rating_text.split()
                    if rating_data:
                        review_data['rating'] = float(rating_data[0])
                except (ValueError, IndexError):
                    pass
            
            # Extract review count
            review_count_elem = soup.find('[data-testid="recipe-review-count"]')
            if review_count_elem:
                count_text = review_count_elem.get_text(strip=True)
                try:
                    # Extract number from text like "1,234 reviews"
                    count_str = ''.join(filter(str.isdigit, count_text))
                    if count_str:
                        review_data['review_count'] = int(count_str)
                except (ValueError, IndexError):
                    pass
            
            return review_data if review_data else None
            
        except Exception as e:
            logger.debug(f"Failed to extract review info: {e}")
            return None
    
    def _parse_ingredient(self, ingredient_text: str) -> Ingredient:
        """Parse ingredient text into structured data.
        
        Args:
            ingredient_text: Raw ingredient text
            
        Returns:
            Ingredient object with parsed components
        """
        # This is a simplified parser - could be enhanced with more sophisticated NLP
        text = ingredient_text.strip()
        
        # Try to extract quantity, unit, and name
        words = text.split()
        
        quantity = None
        unit = None
        name = text
        preparation = None
        
        # Look for quantity at the beginning
        if words and self._looks_like_quantity(words[0]):
            quantity = words[0]
            remaining_words = words[1:]
            
            # Look for unit after quantity
            if remaining_words and self._looks_like_unit(remaining_words[0]):
                unit = remaining_words[0]
                name_words = remaining_words[1:]
            else:
                name_words = remaining_words
            
            if name_words:
                name = ' '.join(name_words)
        
        # Look for preparation notes in parentheses or after comma
        if '(' in text and ')' in text:
            start = text.find('(')
            end = text.find(')', start)
            if start < end:
                preparation = text[start+1:end].strip()
                name = (text[:start] + text[end+1:]).strip()
        elif ',' in text:
            parts = text.split(',', 1)
            if len(parts) == 2 and len(parts[1].strip()) < 50:  # Likely preparation note
                name = parts[0].strip()
                preparation = parts[1].strip()
        
        return Ingredient(
            name=name,
            quantity=quantity,
            unit=unit,
            preparation=preparation,
            raw_text=ingredient_text
        )
    
    def _looks_like_quantity(self, word: str) -> bool:
        """Check if word looks like a quantity."""
        # Handle fractions, decimals, and ranges
        word = word.replace('½', '0.5').replace('¼', '0.25').replace('¾', '0.75')
        word = word.replace('⅓', '0.33').replace('⅔', '0.67').replace('⅛', '0.125')
        
        # Remove common punctuation
        word = word.strip('.,;')
        
        try:
            float(word)
            return True
        except ValueError:
            # Check for fractions like "1/2"
            if '/' in word:
                parts = word.split('/')
                if len(parts) == 2:
                    try:
                        float(parts[0])
                        float(parts[1])
                        return True
                    except ValueError:
                        pass
            
            # Check for ranges like "2-3"
            if '-' in word:
                parts = word.split('-')
                if len(parts) == 2:
                    try:
                        float(parts[0])
                        float(parts[1])
                        return True
                    except ValueError:
                        pass
        
        return False
    
    def _looks_like_unit(self, word: str) -> bool:
        """Check if word looks like a measurement unit."""
        common_units = {
            'cup', 'cups', 'c', 'c.',
            'tablespoon', 'tablespoons', 'tbsp', 'tbsp.', 'tbs', 'tbs.',
            'teaspoon', 'teaspoons', 'tsp', 'tsp.', 'tsp',
            'pound', 'pounds', 'lb', 'lb.', 'lbs', 'lbs.',
            'ounce', 'ounces', 'oz', 'oz.',
            'gram', 'grams', 'g', 'g.',
            'kilogram', 'kilograms', 'kg', 'kg.',
            'liter', 'liters', 'l', 'l.',
            'milliliter', 'milliliters', 'ml', 'ml.',
            'pint', 'pints', 'pt', 'pt.',
            'quart', 'quarts', 'qt', 'qt.',
            'gallon', 'gallons', 'gal', 'gal.',
            'inch', 'inches', 'in', 'in.',
            'clove', 'cloves',
            'bunch', 'bunches',
            'head', 'heads',
            'piece', 'pieces',
            'slice', 'slices',
            'can', 'cans',
            'jar', 'jars',
            'bottle', 'bottles',
            'package', 'packages', 'pkg', 'pkg.',
            'bag', 'bags'
        }
        
        return word.lower().strip('.,;') in common_units