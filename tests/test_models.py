"""Tests for recipe data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from recipe_mcp.models import (
    Ingredient,
    Recipe,
    RecipeMetadata,
    NutritionInfo,
    ExtractionResult
)


class TestIngredient:
    """Tests for Ingredient model."""
    
    def test_ingredient_creation(self):
        """Test basic ingredient creation."""
        ingredient = Ingredient(
            name="flour",
            quantity="2",
            unit="cups",
            preparation="sifted",
            raw_text="2 cups flour, sifted"
        )
        
        assert ingredient.name == "flour"
        assert ingredient.quantity == "2"
        assert ingredient.unit == "cups"
        assert ingredient.preparation == "sifted"
        assert ingredient.raw_text == "2 cups flour, sifted"
    
    def test_ingredient_minimal(self):
        """Test ingredient with minimal data."""
        ingredient = Ingredient(
            name="salt",
            raw_text="salt"
        )
        
        assert ingredient.name == "salt"
        assert ingredient.quantity is None
        assert ingredient.unit is None
        assert ingredient.preparation is None
        assert ingredient.raw_text == "salt"


class TestRecipeMetadata:
    """Tests for RecipeMetadata model."""
    
    def test_metadata_creation(self):
        """Test recipe metadata creation."""
        metadata = RecipeMetadata(
            source_url="https://cooking.nytimes.com/recipes/1234-test-recipe",
            title="Test Recipe",
            author="Test Chef",
            description="A test recipe",
            prep_time="10 minutes",
            cook_time="20 minutes",
            servings="4"
        )
        
        assert str(metadata.source_url) == "https://cooking.nytimes.com/recipes/1234-test-recipe"
        assert metadata.title == "Test Recipe"
        assert metadata.author == "Test Chef"
        assert metadata.description == "A test recipe"
        assert metadata.prep_time == "10 minutes"
        assert metadata.cook_time == "20 minutes"
        assert metadata.servings == "4"
        assert isinstance(metadata.extracted_at, datetime)
    
    def test_metadata_minimal(self):
        """Test metadata with minimal required fields."""
        metadata = RecipeMetadata(
            source_url="https://cooking.nytimes.com/recipes/1234-test-recipe",
            title="Test Recipe"
        )
        
        assert str(metadata.source_url) == "https://cooking.nytimes.com/recipes/1234-test-recipe"
        assert metadata.title == "Test Recipe"
        assert metadata.author is None
        assert metadata.tags == []
    
    def test_metadata_invalid_url(self):
        """Test metadata with invalid URL."""
        with pytest.raises(ValidationError):
            RecipeMetadata(
                source_url="not-a-url",
                title="Test Recipe"
            )


class TestRecipe:
    """Tests for Recipe model."""
    
    def test_recipe_creation(self):
        """Test complete recipe creation."""
        metadata = RecipeMetadata(
            source_url="https://cooking.nytimes.com/recipes/1234-test-recipe",
            title="Test Recipe"
        )
        
        ingredients = [
            Ingredient(name="flour", raw_text="2 cups flour"),
            Ingredient(name="sugar", raw_text="1 cup sugar")
        ]
        
        instructions = [
            "Mix flour and sugar",
            "Bake for 20 minutes"
        ]
        
        recipe = Recipe(
            metadata=metadata,
            ingredients=ingredients,
            instructions=instructions
        )
        
        assert recipe.metadata.title == "Test Recipe"
        assert len(recipe.ingredients) == 2
        assert len(recipe.instructions) == 2
        assert recipe.notes == []
        assert recipe.equipment == []
    
    def test_recipe_to_google_keep_format(self):
        """Test conversion to Google Keep format."""
        metadata = RecipeMetadata(
            source_url="https://cooking.nytimes.com/recipes/1234-test-recipe",
            title="Test Recipe",
            prep_time="10 minutes",
            cook_time="20 minutes",
            servings="4"
        )
        
        ingredients = [
            Ingredient(name="flour", raw_text="2 cups flour"),
            Ingredient(name="sugar", raw_text="1 cup sugar")
        ]
        
        instructions = [
            "Mix flour and sugar",
            "Bake for 20 minutes"
        ]
        
        recipe = Recipe(
            metadata=metadata,
            ingredients=ingredients,
            instructions=instructions,
            notes=["Let cool before serving"]
        )
        
        keep_format = recipe.to_google_keep_format()
        
        assert keep_format["title"] == "Recipe: Test Recipe"
        assert "**Test Recipe**" in keep_format["content"]
        assert "• 2 cups flour" in keep_format["content"]
        assert "• 1 cup sugar" in keep_format["content"]
        assert "1. Mix flour and sugar" in keep_format["content"]
        assert "2. Bake for 20 minutes" in keep_format["content"]
        assert "Prep: 10 minutes | Cook: 20 minutes" in keep_format["content"]
        assert "Servings: 4" in keep_format["content"]
        assert "• Let cool before serving" in keep_format["content"]
        assert "Source: https://cooking.nytimes.com/recipes/1234-test-recipe" in keep_format["content"]
        assert keep_format["labels"] == ["recipe"]


class TestNutritionInfo:
    """Tests for NutritionInfo model."""
    
    def test_nutrition_creation(self):
        """Test nutrition info creation."""
        nutrition = NutritionInfo(
            calories=250,
            protein="10g",
            carbohydrates="30g",
            fat="8g"
        )
        
        assert nutrition.calories == 250
        assert nutrition.protein == "10g"
        assert nutrition.carbohydrates == "30g"
        assert nutrition.fat == "8g"
        assert nutrition.fiber is None


class TestExtractionResult:
    """Tests for ExtractionResult model."""
    
    def test_extraction_success(self):
        """Test successful extraction result."""
        metadata = RecipeMetadata(
            source_url="https://cooking.nytimes.com/recipes/1234-test-recipe",
            title="Test Recipe"
        )
        
        recipe = Recipe(
            metadata=metadata,
            ingredients=[],
            instructions=[]
        )
        
        result = ExtractionResult(
            success=True,
            recipe=recipe,
            extraction_time=1.5
        )
        
        assert result.success is True
        assert result.recipe is not None
        assert result.error is None
        assert result.warnings == []
        assert result.extraction_time == 1.5
    
    def test_extraction_failure(self):
        """Test failed extraction result."""
        result = ExtractionResult(
            success=False,
            error="Network timeout",
            extraction_time=30.0
        )
        
        assert result.success is False
        assert result.recipe is None
        assert result.error == "Network timeout"
        assert result.extraction_time == 30.0