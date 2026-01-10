"""
Shared utilities for Sartor Ad Engine agents.

Provides common functions used across agent implementations.
"""

import logging
from typing import Any

from pydantic import BaseModel

from src.config import get_settings
from src.models import BrandContext, ErrorLog
from src.state import AdCreationState


logger = logging.getLogger(__name__)


def get_dominant_brand(state: AdCreationState) -> BrandContext:
    """
    Return the dominant brand based on brand_strategy.
    
    Args:
        state: The accumulated pipeline state
        
    Returns:
        The brand that should dominate the ad's voice and visual identity
    """
    brand_strategy = state.get("brand_strategy", "store_dominant")
    product_brand = state.get("product_brand")
    store_brand = state["store_brand"]
    
    if brand_strategy == "product_dominant" and product_brand:
        return product_brand
    else:
        # store_dominant, co_branded, or fallback
        return store_brand


def log_agent_call(
    agent_name: str,
    input_summary: str,
    output_data: Any | None = None,
) -> None:
    """
    Log agent invocation if logging is enabled.
    
    Args:
        agent_name: Name of the agent being invoked
        input_summary: Brief summary of input data
        output_data: Optional output to log
    """
    settings = get_settings()
    
    if settings.log_prompts:
        logger.info(f"[{agent_name}] Input: {input_summary}")
        if output_data is not None:
            if isinstance(output_data, BaseModel):
                logger.info(f"[{agent_name}] Output: {output_data.model_dump_json(indent=2)}")
            else:
                logger.info(f"[{agent_name}] Output: {output_data}")


def create_error(
    agent_name: str,
    error_message: str,
    icp_id: str | None = None,
) -> ErrorLog:
    """
    Factory function to create an ErrorLog entry.
    
    Args:
        agent_name: Name of the agent that encountered the error
        error_message: Description of the error
        icp_id: Optional ICP ID if error is ICP-specific
        
    Returns:
        ErrorLog instance for adding to state
    """
    return ErrorLog(
        agent_name=agent_name,
        icp_id=icp_id,
        error_message=error_message,
    )


def model_to_dict(model: BaseModel) -> dict:
    """
    Convert a Pydantic model to a dictionary for prompt formatting.
    
    Uses model_dump() for Pydantic v2 compatibility.
    
    Args:
        model: Pydantic model instance
        
    Returns:
        Dictionary representation of the model
    """
    return model.model_dump()


def add_error_to_state(
    state: AdCreationState,
    error: ErrorLog,
) -> list[ErrorLog]:
    """
    Return updated errors list with new error appended.
    
    Args:
        state: Current pipeline state
        error: New error to add
        
    Returns:
        Updated list of errors (for use in state update dict)
    """
    existing_errors = state.get("errors", [])
    return existing_errors + [error]
