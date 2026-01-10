"""
Segmentation Agent implementation for Sartor Ad Engine.

Mission: Identify 1-4 distinct Ideal Customer Profiles (ICPs) for an eCommerce product.

This is the first agent in the pipeline. It analyzes product attributes,
price point, category, and brand positioning to generate meaningful customer
segments that will receive personalized ad creatives.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from agents.common.agent_utils import (
    add_error_to_state,
    create_error,
    log_agent_call,
    model_to_dict,
)
from src.models import ICP
from src.state import AdCreationState
from src.utils.llm_factory import create_llm_for_agent

from .prompts import SYSTEM_PROMPT, format_user_message


logger = logging.getLogger(__name__)


# =============================================================================
# RESPONSE MODEL
# =============================================================================

class SegmentationResponse(BaseModel):
    """Wrapper model for structured output parsing."""
    
    icps: list[ICP] = Field(
        ...,
        description="List of 1-4 Ideal Customer Profiles",
        min_length=1,
        max_length=4,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_input_summary(state: AdCreationState) -> str:
    """Create a brief summary of inputs for logging."""
    product = state["product"]
    store_brand = state["store_brand"]
    return (
        f"Product: {product.name}, "
        f"Category: {product.category}, "
        f"Store: {store_brand.brand_name}"
    )


def _prepare_user_message_data(state: AdCreationState) -> dict[str, Any]:
    """Extract and format data for the user message template."""
    product = state["product"]
    store_brand = state["store_brand"]
    product_brand = state.get("product_brand")
    brand_strategy = state.get("brand_strategy", "store_dominant")
    store_context = state.get("store_context")
    
    return {
        "product": model_to_dict(product),
        "store_brand": model_to_dict(store_brand),
        "product_brand": model_to_dict(product_brand) if product_brand else None,
        "brand_strategy": brand_strategy,
        "store_context": model_to_dict(store_context) if store_context else None,
    }


# =============================================================================
# MAIN AGENT FUNCTION
# =============================================================================

def run_segmentation_agent(state: AdCreationState) -> dict:
    """
    LangGraph node function for the Segmentation Agent.
    
    Analyzes product and brand context to identify 1-4 distinct ICPs.
    
    Args:
        state: The accumulated pipeline state containing product, brands,
               brand_strategy, and optional store_context
    
    Returns:
        Dict with "icps" key containing list of ICP objects.
        On error, returns dict with updated "errors" list.
    """
    agent_name = "segmentation"
    
    try:
        # 1. Log input if enabled
        input_summary = _build_input_summary(state)
        log_agent_call(agent_name, input_summary)
        
        # 2. Prepare message data
        message_data = _prepare_user_message_data(state)
        
        # 3. Build prompts
        system_prompt = SYSTEM_PROMPT
        user_message = format_user_message(
            product=message_data["product"],
            store_brand=message_data["store_brand"],
            product_brand=message_data["product_brand"],
            brand_strategy=message_data["brand_strategy"],
            store_context=message_data["store_context"],
        )
        
        # 4. Create LLM with structured output
        llm = create_llm_for_agent(agent_name)
        structured_llm = llm.with_structured_output(SegmentationResponse)
        
        # 5. Build messages and invoke
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        
        response: SegmentationResponse = structured_llm.invoke(messages)
        
        # 6. Log output and return
        log_agent_call(agent_name, input_summary, response)
        
        logger.info(f"Segmentation Agent generated {len(response.icps)} ICPs")
        
        return {"icps": response.icps}
        
    except Exception as e:
        logger.error(f"Segmentation Agent failed: {e}")
        error = create_error(
            agent_name=agent_name,
            error_message=str(e),
        )
        return {"errors": add_error_to_state(state, error)}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["run_segmentation_agent", "SegmentationResponse"]
