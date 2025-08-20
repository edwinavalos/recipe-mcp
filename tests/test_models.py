"""Tests for recipe data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from recipe_mcp.models import (
    Ingredient,
    Recipe,
    ExtractionResult,
    ComplianceInfo,
    ComplianceStatus,
    ExtractionMethod
)


class TestIngredient:
    """Tests for Ingredient model."""
    
    def test_ingredient_creation(self):
        """Test basic ingredient creation."""
        ingredient = Ingredient(
            text="2 cups flour, sifted",
            quantity="2",
            unit="cups",
            item="flour",
            preparation="sifted"
        )
        
        assert ingredient.text == "2 cups flour, sifted"
        assert ingredient.quantity == "2"
        assert ingredient.unit == "cups"
        assert ingredient.item == "flour"
        assert ingredient.preparation == "sifted"
    
    def test_ingredient_minimal(self):
        """Test ingredient with minimal data."""
        ingredient = Ingredient(
            text="salt",
            item="salt"
        )
        
        assert ingredient.text == "salt"
        assert ingredient.item == "salt"
        assert ingredient.quantity is None
        assert ingredient.unit is None
        assert ingredient.preparation is None
    
    def test_ingredient_auto_item_extraction(self):
        """Test automatic item extraction from text."""
        ingredient = Ingredient(
            text="2 cups all-purpose flour"
        )
        
        assert ingredient.text == "2 cups all-purpose flour"
        assert "flour" in ingredient.item.lower()


class TestComplianceInfo:
    """Tests for ComplianceInfo model."""
    
    def test_compliance_info_creation(self):
        """Test compliance info creation."""
        compliance_info = ComplianceInfo(
            status=ComplianceStatus.COMPLIANT,
            daily_usage_count=5,
            daily_limit=50,
            session_id="test-session-123"
        )
        
        assert compliance_info.status == ComplianceStatus.COMPLIANT
        assert compliance_info.daily_usage_count == 5
        assert compliance_info.daily_limit == 50
        assert compliance_info.session_id == "test-session-123"
        assert compliance_info.warnings == []
    
    def test_compliance_info_rate_limited(self):
        """Test rate limited compliance info."""
        compliance_info = ComplianceInfo(
            status=ComplianceStatus.RATE_LIMITED,
            daily_usage_count=50,
            daily_limit=50,
            session_id="test-session-123",
            warnings=["Daily limit reached"]
        )
        
        assert compliance_info.status == ComplianceStatus.RATE_LIMITED
        assert compliance_info.daily_usage_count == 50
        assert compliance_info.warnings == ["Daily limit reached"]


class TestRecipe:
    """Tests for Recipe model."""
    
    def test_recipe_creation(self):
        """Test complete recipe creation."""
        ingredients = [
            Ingredient(text="2 cups flour", item="flour"),
            Ingredient(text="1 cup sugar", item="sugar")
        ]
        
        instructions = [
            "Mix flour and sugar",
            "Bake for 20 minutes"
        ]
        
        recipe = Recipe(
            title="Test Recipe",
            url="https://cooking.nytimes.com/recipes/1234-test-recipe",
            ingredients=ingredients,
            instructions=instructions,
            source="nyt_cooking"
        )
        
        assert recipe.title == "Test Recipe"
        assert recipe.url == "https://cooking.nytimes.com/recipes/1234-test-recipe"
        assert len(recipe.ingredients) == 2
        assert len(recipe.instructions) == 2
        assert recipe.source == "nyt_cooking"
        assert isinstance(recipe.extracted_at, datetime)
        assert recipe.extraction_method == ExtractionMethod.BROWSER_AUTOMATION
        assert recipe.compliance_status == ComplianceStatus.UNKNOWN
    
    def test_recipe_with_metadata(self):
        """Test recipe with full metadata."""
        recipe = Recipe(
            title="Chocolate Chip Cookies",
            url="https://cooking.nytimes.com/recipes/1234-cookies",
            ingredients=[
                Ingredient(text="2 cups flour", item="flour"),
                Ingredient(text="1 cup butter", item="butter")
            ],
            instructions=["Mix ingredients", "Bake for 12 minutes"],
            prep_time="15 minutes",
            cook_time="12 minutes",
            servings=24,
            author="Test Chef",
            description="Delicious homemade cookies",
            tags=["dessert", "cookies"],
            source="nyt_cooking",
            rating=4.5,
            review_count=150
        )
        
        assert recipe.title == "Chocolate Chip Cookies"
        assert recipe.author == "Test Chef"
        assert recipe.description == "Delicious homemade cookies"
        assert recipe.prep_time == "15 minutes"
        assert recipe.cook_time == "12 minutes"
        assert recipe.servings == 24
        assert recipe.tags == ["dessert", "cookies"]
        assert recipe.rating == 4.5
        assert recipe.review_count == 150


class TestExtractionResult:
    """Tests for ExtractionResult model."""
    
    def test_extraction_success(self):
        """Test successful extraction result."""
        recipe = Recipe(
            title="Test Recipe",
            url="https://cooking.nytimes.com/recipes/1234-test-recipe",
            ingredients=[],
            instructions=[],
            source="nyt_cooking"
        )
        
        compliance_info = ComplianceInfo(
            status=ComplianceStatus.COMPLIANT,
            daily_usage_count=5,
            daily_limit=50,
            session_id="test-session"
        )
        
        result = ExtractionResult(
            success=True,
            recipe=recipe,
            extraction_time=1.5,
            compliance_info=compliance_info
        )
        
        assert result.success is True
        assert result.recipe is not None
        assert result.recipe.title == "Test Recipe"
        assert result.error is None
        assert result.warnings == []
        assert result.extraction_time == 1.5
        assert result.compliance_info is not None
        assert result.compliance_info.status == ComplianceStatus.COMPLIANT
    
    def test_extraction_failure(self):
        """Test failed extraction result."""
        compliance_info = ComplianceInfo(
            status=ComplianceStatus.RATE_LIMITED,
            daily_usage_count=50,
            daily_limit=50,
            session_id="test-session",
            warnings=["Daily limit exceeded"]
        )
        
        result = ExtractionResult(
            success=False,
            error="Daily extraction limit exceeded",
            extraction_time=0.1,
            compliance_info=compliance_info
        )
        
        assert result.success is False
        assert result.recipe is None
        assert result.error == "Daily extraction limit exceeded"
        assert result.compliance_info.status == ComplianceStatus.RATE_LIMITED
        assert result.compliance_info.warnings == ["Daily limit exceeded"]
        assert result.extraction_time == 0.1