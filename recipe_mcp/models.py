"""Data models for recipe extraction."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class Ingredient(BaseModel):
    """Represents a recipe ingredient."""
    
    name: str = Field(..., description="Name of the ingredient")
    quantity: Optional[str] = Field(None, description="Quantity/amount")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    preparation: Optional[str] = Field(None, description="Preparation notes (chopped, diced, etc.)")
    raw_text: str = Field(..., description="Original ingredient text as written")


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
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="Extraction timestamp")


class Recipe(BaseModel):
    """Complete recipe data model."""
    
    metadata: RecipeMetadata = Field(..., description="Recipe metadata")
    ingredients: List[Ingredient] = Field(..., description="List of ingredients")
    instructions: List[str] = Field(..., description="Cooking instructions")
    nutrition: Optional[NutritionInfo] = Field(None, description="Nutritional information")
    notes: List[str] = Field(default_factory=list, description="Additional notes")
    equipment: List[str] = Field(default_factory=list, description="Required equipment")
    
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


class ExtractionResult(BaseModel):
    """Result of a recipe extraction operation."""
    
    success: bool = Field(..., description="Whether extraction was successful")
    recipe: Optional[Recipe] = Field(None, description="Extracted recipe data")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    extraction_time: float = Field(..., description="Time taken for extraction in seconds")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }