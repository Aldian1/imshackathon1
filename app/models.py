"""
Pydantic models for API request/response structures
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


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


# ============================================================================
# JOB SYSTEM MODELS
# ============================================================================

class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Type of job being executed"""
    FOOD_SEARCH = "food_search"
    RESTAURANT_SEARCH = "restaurant_search"
    HEALTH_CHECK = "health_check"


class JobProgress(BaseModel):
    """Job progress information"""
    current_step: int = Field(default=0, description="Current step number")
    total_steps: int = Field(default=1, description="Total number of steps")
    step_description: Optional[str] = Field(default=None, description="Description of current step")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")


class JobRequest(BaseModel):
    """Request to create a new job"""
    job_type: JobType = Field(..., description="Type of job to execute")
    job_data: Dict[str, Any] = Field(..., description="Job-specific data")
    priority: int = Field(default=1, ge=1, le=10, description="Job priority (1=lowest, 10=highest)")
    timeout_seconds: int = Field(default=300, description="Job timeout in seconds")
    
    # For food search jobs, job_data should contain SearchRequest fields
    # Example: {"location": "Buenos Aires", "food_types": ["pizza"], ...}


class Job(BaseModel):
    """Job model with all metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique job ID")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    job_type: JobType = Field(..., description="Type of job")
    job_data: Dict[str, Any] = Field(..., description="Job input data")
    
    # Execution metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Job creation time")
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion time")
    
    # Progress tracking
    progress: JobProgress = Field(default_factory=JobProgress, description="Job progress")
    
    # Results and error handling
    result: Optional[Dict[str, Any]] = Field(default=None, description="Job result data")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Configuration
    priority: int = Field(default=1, description="Job priority")
    timeout_seconds: int = Field(default=300, description="Job timeout")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class JobResponse(BaseModel):
    """Response when creating or querying a job"""
    job_id: str = Field(..., description="Unique job ID")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Human-readable status message")
    
    # Optional fields based on status
    progress: Optional[JobProgress] = Field(default=None, description="Job progress if running")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Job result if completed")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Timing information
    created_at: datetime = Field(..., description="Job creation time")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")


class JobListResponse(BaseModel):
    """Response for listing multiple jobs"""
    jobs: List[JobResponse] = Field(..., description="List of jobs")
    total_count: int = Field(..., description="Total number of jobs")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Jobs per page")