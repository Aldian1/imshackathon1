"""
API routes for food search functionality using Browser Use Rappi agent
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models import (
    SearchRequest, 
    SearchResponse, 
    BrowserStatus, 
    AgentConfig,
    ErrorResponse
)
from app.agents.rappi_agent import RappiAgent

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Global agent instance (in production, you might want to use dependency injection)
_agent_instance = None


def get_agent_instance(config: AgentConfig = None) -> RappiAgent:
    """Get or create agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = RappiAgent(config or AgentConfig())
    return _agent_instance


@router.post("/search", response_model=SearchResponse)
async def search_food_options(
    search_request: SearchRequest,
    background_tasks: BackgroundTasks
) -> SearchResponse:
    """
    Search for food options on Rappi based on user preferences
    
    This endpoint uses Browser Use to automate searching rappi.com.ar
    and returns structured data about available restaurants and food options.
    """
    try:
        logger.info(f"Received search request for location: {search_request.location}")
        
        # Validate request
        if not search_request.location.strip():
            raise HTTPException(
                status_code=400, 
                detail="Location is required"
            )
        
        # Get agent instance
        agent = get_agent_instance()
        
        # Perform the search
        result = await agent.search_food_options(search_request)
        
        logger.info(f"Search completed. Success: {result.success}, Results: {len(result.results)}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during search: {str(e)}"
        )


@router.get("/search/status", response_model=BrowserStatus)
async def get_browser_status() -> BrowserStatus:
    """
    Get the current status of the browser agent
    """
    try:
        agent = get_agent_instance()
        
        # Check if agent has an active session
        is_active = agent.session_id is not None
        
        return BrowserStatus(
            is_active=is_active,
            session_id=agent.session_id,
            current_url="https://rappi.com.ar" if is_active else None,
            last_action=f"Last search: {agent.last_search_time}" if agent.last_search_time else None
        )
        
    except Exception as e:
        logger.error(f"Status endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve browser status"
        )


@router.post("/search/test", response_model=SearchResponse)
async def test_search() -> SearchResponse:
    """
    Test endpoint with a predefined search to verify the system is working
    """
    try:
        # Create a test search request
        test_request = SearchRequest(
            location="Buenos Aires, Argentina",
            max_results=3,
            search_query="pizza"
        )
        
        agent = get_agent_instance()
        result = await agent.search_food_options(test_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Test search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Test search failed: {str(e)}"
        )


@router.post("/agent/config", response_model=Dict[str, Any])
async def update_agent_config(config: AgentConfig) -> Dict[str, Any]:
    """
    Update the agent configuration
    """
    try:
        global _agent_instance
        
        # Create new agent instance with updated config
        _agent_instance = RappiAgent(config)
        
        logger.info(f"Agent configuration updated: {config.dict()}")
        
        return {
            "success": True,
            "message": "Agent configuration updated successfully",
            "config": config.dict()
        }
        
    except Exception as e:
        logger.error(f"Config update error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/agent/config", response_model=AgentConfig)
async def get_agent_config() -> AgentConfig:
    """
    Get the current agent configuration
    """
    try:
        agent = get_agent_instance()
        return agent.config
        
    except Exception as e:
        logger.error(f"Get config error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve agent configuration"
        )


@router.delete("/agent/reset")
async def reset_agent() -> Dict[str, Any]:
    """
    Reset the agent instance (useful for clearing any stuck sessions)
    """
    try:
        global _agent_instance
        _agent_instance = None
        
        logger.info("Agent instance reset")
        
        return {
            "success": True,
            "message": "Agent instance reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Agent reset error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset agent: {str(e)}"
        )


@router.get("/locations/suggestions")
async def get_location_suggestions(query: str = "") -> Dict[str, Any]:
    """
    Get location suggestions for Argentina (static suggestions for now)
    """
    # In a real implementation, you might integrate with a geocoding service
    argentina_locations = [
        "Buenos Aires, Capital Federal, Argentina",
        "Córdoba, Córdoba, Argentina", 
        "Rosario, Santa Fe, Argentina",
        "Mendoza, Mendoza, Argentina",
        "La Plata, Buenos Aires, Argentina",
        "Tucumán, Tucumán, Argentina",
        "Mar del Plata, Buenos Aires, Argentina",
        "Palermo, Buenos Aires, Argentina",
        "Recoleta, Buenos Aires, Argentina",
        "Belgrano, Buenos Aires, Argentina"
    ]
    
    # Filter based on query if provided
    if query:
        filtered_locations = [
            loc for loc in argentina_locations 
            if query.lower() in loc.lower()
        ]
    else:
        filtered_locations = argentina_locations
    
    return {
        "suggestions": filtered_locations[:10],
        "total": len(filtered_locations)
    }