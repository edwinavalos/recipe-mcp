"""Data models for recipe extraction."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict, model_validator
from enum import Enum


class ComplianceStatus(str, Enum):
    """Compliance status enumeration."""
    COMPLIANT = "compliant"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class ExtractionMethod(str, Enum):
    """Method used for extraction."""
    BROWSER_AUTOMATION = "browser_automation"
    API = "api"
    RSS = "rss"
    CACHED = "cached"


class Ingredient(BaseModel):
    """Represents a recipe ingredient with enhanced parsing."""
    
    text: str = Field(..., description="Original ingredient text as written")
    quantity: Optional[str] = Field(None, description="Parsed quantity/amount")
    unit: Optional[str] = Field(None, description="Parsed unit of measurement")
    item: Optional[str] = Field(None, description="Parsed ingredient name")
    section: Optional[str] = Field(None, description="Section for grocery list grouping")
    preparation: Optional[str] = Field(None, description="Preparation notes (chopped, diced, etc.)")
    
    @model_validator(mode='before')
    @classmethod
    def extract_item_if_missing(cls, data):
        """Extract item name from text if not provided."""
        if isinstance(data, dict):
            if not data.get('item') and data.get('text'):
                data['item'] = cls._extract_item_from_text(data['text'])
        return data
    
    @staticmethod
    def _extract_item_from_text(text: str) -> str:
        """Simple item extraction from ingredient text."""
        # Remove common quantity patterns and units
        import re
        # Remove fractions and numbers at start
        text = re.sub(r'^[\d\/\s\-]+', '', text)
        # Remove common units
        units = ['cup', 'cups', 'tbsp', 'tsp', 'oz', 'lb', 'lbs', 'g', 'kg', 'ml', 'l']
        for unit in units:
            text = re.sub(f'^{unit}\\s+', '', text, flags=re.IGNORECASE)
        # Remove preparation notes in parentheses
        text = re.sub(r'\([^)]*\)', '', text)
        return text.strip() or "Unknown ingredient"


class NutritionInfo(BaseModel):
    """Nutritional information for a recipe."""
    
    calories: Optional[int] = None
    protein: Optional[str] = None
    carbohydrates: Optional[str] = None
    fat: Optional[str] = None
    fiber: Optional[str] = None
    sugar: Optional[str] = None
    sodium: Optional[str] = None


class RecipeMetadata(BaseModel):
    """Metadata about a recipe."""
    
    source_url: HttpUrl = Field(..., description="Original recipe URL")
    title: str = Field(..., description="Recipe title")
    author: Optional[str] = Field(None, description="Recipe author")
    description: Optional[str] = Field(None, description="Recipe description")
    prep_time: Optional[str] = Field(None, description="Preparation time")
    cook_time: Optional[str] = Field(None, description="Cooking time")
    total_time: Optional[str] = Field(None, description="Total time")
    servings: Optional[str] = Field(None, description="Number of servings")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    tags: List[str] = Field(default_factory=list, description="Recipe tags")
    rating: Optional[float] = Field(None, description="Recipe rating")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Extraction timestamp")


class Recipe(BaseModel):
    """Complete recipe data model with compliance tracking."""
    
    title: str = Field(..., description="Recipe title")
    url: str = Field(..., description="Original recipe URL")
    ingredients: List[Ingredient] = Field(..., description="List of ingredients")
    instructions: List[str] = Field(..., description="Cooking instructions")
    prep_time: Optional[str] = Field(None, description="Preparation time")
    cook_time: Optional[str] = Field(None, description="Cooking time")
    servings: Optional[int] = Field(None, description="Number of servings")
    nutrition: Optional[Dict[str, Any]] = Field(None, description="Nutritional information")
    tags: List[str] = Field(default_factory=list, description="Recipe tags")
    source: str = Field(..., description="Source identifier (e.g., 'nyt_cooking')")
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Extraction timestamp")
    
    # Enhanced metadata
    author: Optional[str] = Field(None, description="Recipe author")
    description: Optional[str] = Field(None, description="Recipe description")
    total_time: Optional[str] = Field(None, description="Total cooking time")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    rating: Optional[float] = Field(None, description="Recipe rating")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    
    # Compliance tracking
    extraction_method: ExtractionMethod = Field(default=ExtractionMethod.BROWSER_AUTOMATION)
    compliance_status: ComplianceStatus = Field(default=ComplianceStatus.UNKNOWN)
    extraction_session_id: Optional[str] = Field(None, description="Session ID for compliance tracking")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    def to_google_keep_format(self) -> Dict[str, Any]:
        """Convert recipe to Google Keep-friendly format."""
        ingredients_text = "\n".join([
            f"• {ingredient.raw_text}" for ingredient in self.ingredients
        ])
        
        instructions_text = "\n".join([
            f"{i+1}. {instruction}" 
            for i, instruction in enumerate(self.instructions)
        ])
        
        note_content = f"""**{self.metadata.title}**

**Ingredients:**
{ingredients_text}

**Instructions:**
{instructions_text}"""
        
        if self.metadata.prep_time or self.metadata.cook_time:
            times = []
            if self.metadata.prep_time:
                times.append(f"Prep: {self.metadata.prep_time}")
            if self.metadata.cook_time:
                times.append(f"Cook: {self.metadata.cook_time}")
            note_content += f"\n\n**Time:** {' | '.join(times)}"
        
        if self.metadata.servings:
            note_content += f"\n**Servings:** {self.metadata.servings}"
        
        if self.notes:
            note_content += f"\n\n**Notes:**\n" + "\n".join([f"• {note}" for note in self.notes])
        
        note_content += f"\n\n**Source:** {self.metadata.source_url}"
        
        return {
            "title": f"Recipe: {self.metadata.title}",
            "content": note_content,
            "labels": ["recipe"] + self.metadata.tags,
        }


class ComplianceInfo(BaseModel):
    """Compliance information for the extraction."""
    
    status: ComplianceStatus = Field(..., description="Current compliance status")
    daily_usage_count: int = Field(..., description="Number of extractions today")
    daily_limit: int = Field(..., description="Daily extraction limit")
    session_id: str = Field(..., description="Session ID for tracking")
    rate_limit_reset: Optional[datetime] = Field(None, description="When rate limit resets")
    warnings: List[str] = Field(default_factory=list, description="Compliance warnings")


class ExtractionResult(BaseModel):
    """Result of a recipe extraction operation with compliance tracking."""
    
    success: bool = Field(..., description="Whether extraction was successful")
    recipe: Optional[Recipe] = Field(None, description="Extracted recipe data")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    extraction_time: float = Field(..., description="Time taken for extraction in seconds")
    compliance_info: Optional[ComplianceInfo] = Field(None, description="Compliance tracking information")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }