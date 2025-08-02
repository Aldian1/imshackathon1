"""
Pydantic models for API request/response structures
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class PriceRange(str, Enum):
    """Price range options"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ANY = "any"


class CuisineType(str, Enum):
    """Cuisine type options"""
    ITALIAN = "italian"
    ARGENTINIAN = "argentinian"
    MEXICAN = "mexican"
    ASIAN = "asian"
    FAST_FOOD = "fast_food"
    PIZZA = "pizza"
    SUSHI = "sushi"
    BURGER = "burger"
    ANY = "any"


class DietaryRestriction(str, Enum):
    """Dietary restriction options"""
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    KETO = "keto"
    HALAL = "halal"


class SearchPreferences(BaseModel):
    """User preferences for food search"""
    cuisine_type: Optional[CuisineType] = Field(default=CuisineType.ANY, description="Type of cuisine preferred")
    price_range: Optional[PriceRange] = Field(default=PriceRange.ANY, description="Price range preference")
    dietary_restrictions: Optional[List[DietaryRestriction]] = Field(default=[], description="Dietary restrictions")
    max_delivery_time: Optional[int] = Field(default=60, description="Maximum delivery time in minutes")
    min_rating: Optional[float] = Field(default=0.0, ge=0.0, le=5.0, description="Minimum restaurant rating")
    max_delivery_fee: Optional[float] = Field(default=None, description="Maximum delivery fee in ARS")


class SearchRequest(BaseModel):
    """Request model for food search"""
    location: str = Field(..., description="Location for food delivery (e.g., 'Buenos Aires, Argentina')")
    preferences: Optional[SearchPreferences] = Field(default_factory=SearchPreferences, description="Search preferences")
    max_results: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum number of results to return")
    search_query: Optional[str] = Field(default="", description="Specific search query or food item")


class MenuItem(BaseModel):
    """Individual menu item"""
    name: str = Field(..., description="Item name")
    price: Optional[float] = Field(default=None, description="Item price in ARS")
    description: Optional[str] = Field(default="", description="Item description")
    image_url: Optional[str] = Field(default="", description="Item image URL")
    available: Optional[bool] = Field(default=True, description="Item availability")


class RestaurantResult(BaseModel):
    """Restaurant search result"""
    restaurant_name: str = Field(..., description="Restaurant name")
    cuisine_type: Optional[str] = Field(default="", description="Type of cuisine")
    estimated_price: Optional[float] = Field(default=None, description="Estimated total price in ARS")
    delivery_time: Optional[str] = Field(default="", description="Estimated delivery time")
    delivery_fee: Optional[float] = Field(default=None, description="Delivery fee in ARS")
    rating: Optional[float] = Field(default=None, description="Restaurant rating")
    url: str = Field(..., description="Direct link to restaurant page")
    image_url: Optional[str] = Field(default="", description="Restaurant image URL")
    address: Optional[str] = Field(default="", description="Restaurant address")
    menu_items: Optional[List[MenuItem]] = Field(default=[], description="Sample menu items")
    is_open: Optional[bool] = Field(default=True, description="Restaurant availability")
    promotions: Optional[List[str]] = Field(default=[], description="Current promotions")


class SearchMetadata(BaseModel):
    """Metadata about the search operation"""
    location: str = Field(..., description="Search location")
    total_found: int = Field(..., description="Total number of results found")
    search_time: str = Field(..., description="Time taken to complete search")
    search_timestamp: Optional[str] = Field(default="", description="When the search was performed")
    browser_session_id: Optional[str] = Field(default="", description="Browser session identifier")


class SearchResponse(BaseModel):
    """Response model for food search"""
    success: bool = Field(..., description="Whether the search was successful")
    results: List[RestaurantResult] = Field(..., description="List of restaurant results")
    search_metadata: SearchMetadata = Field(..., description="Search metadata")
    error_message: Optional[str] = Field(default=None, description="Error message if search failed")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")


class BrowserStatus(BaseModel):
    """Browser status information"""
    is_active: bool = Field(..., description="Whether browser is active")
    session_id: Optional[str] = Field(default=None, description="Current session ID")
    current_url: Optional[str] = Field(default=None, description="Current page URL")
    last_action: Optional[str] = Field(default=None, description="Last action performed")


class AgentConfig(BaseModel):
    """Configuration for the browser agent"""
    headless: Optional[bool] = Field(default=True, description="Run browser in headless mode")
    timeout: Optional[int] = Field(default=60, description="Browser timeout in seconds")
    max_retries: Optional[int] = Field(default=3, description="Maximum number of retries")
    llm_model: Optional[str] = Field(default="gpt-4o-mini", description="LLM model to use")
    use_vision: Optional[bool] = Field(default=True, description="Use vision capabilities")
    save_screenshots: Optional[bool] = Field(default=False, description="Save screenshots during execution")


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error detail message")
    type: str = Field(..., description="Error type")
    code: Optional[int] = Field(default=None, description="Error code")