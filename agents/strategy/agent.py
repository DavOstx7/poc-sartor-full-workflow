"""
Strategy Agent implementation for Sartor Ad Engine.

Mission: Define the strategic positioning for a product targeting a specific ICP.

The Strategy Agent receives the full accumulated state (product, brands, ICP) and
produces a StrategicBrief that anchors all subsequent creative execution.
This ensures "strategy before creativity" — the core architectural principle.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.common.agent_utils import (
    add_error_to_state,
    create_error,
    log_agent_call,
    model_to_dict,
)
from src.models import ICP, StrategicBrief
from src.state import AdCreationState
from src.utils.llm_factory import create_llm_for_agent

from .prompts import SYSTEM_PROMPT, format_user_message


logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_input_summary(state: AdCreationState, icp: ICP) -> str:
    """Create a brief summary of inputs for logging."""
    product = state["product"]
    return f"Product: {product.name}, ICP: {icp.name}"


def _prepare_user_message_data(
    state: AdCreationState,
    icp: ICP,
) -> dict[str, Any]:
    """Extract and format data for the user message template."""
    product = state["product"]
    store_brand = state["store_brand"]
    product_brand = state.get("product_brand")
    brand_strategy = state.get("brand_strategy", "store_dominant")
    channel = state["channel"]
    
    return {
        "product": model_to_dict(product),
        "store_brand": model_to_dict(store_brand),
        "product_brand": model_to_dict(product_brand) if product_brand else None,
        "brand_strategy": brand_strategy,
        "icp": model_to_dict(icp),
        "channel": model_to_dict(channel),
    }


# =============================================================================
# SINGLE ICP PROCESSING
# =============================================================================

def run_strategy_for_icp(
    state: AdCreationState,
    icp: ICP,
) -> StrategicBrief:
    """
    Generate strategic brief for a single ICP.
    
    Args:
        state: The accumulated pipeline state
        icp: The specific ICP to generate strategy for
        
    Returns:
        StrategicBrief for this ICP
        
    Raises:
        Exception: If LLM invocation fails
    """
    agent_name = "strategy"
    
    # 1. Log input
    input_summary = _build_input_summary(state, icp)
    log_agent_call(agent_name, input_summary)
    
    # 2. Prepare message data
    message_data = _prepare_user_message_data(state, icp)
    
    # 3. Build prompts
    system_prompt = SYSTEM_PROMPT
    user_message = format_user_message(
        product=message_data["product"],
        store_brand=message_data["store_brand"],
        product_brand=message_data["product_brand"],
        brand_strategy=message_data["brand_strategy"],
        icp=message_data["icp"],
        channel=message_data["channel"],
    )
    
    # 4. Create LLM with structured output
    llm = create_llm_for_agent(agent_name)
    structured_llm = llm.with_structured_output(StrategicBrief)
    
    # 5. Build messages and invoke
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    
    response: StrategicBrief = structured_llm.invoke(messages)
    
    # 6. Log output
    log_agent_call(agent_name, input_summary, response)
    
    return response


# =============================================================================
# MAIN AGENT FUNCTION
# =============================================================================

def run_strategy_agent(state: AdCreationState) -> dict:
    """
    LangGraph node function for the Strategy Agent.
    
    Processes all ICPs in sequence, generating a StrategicBrief for each.
    
    Args:
        state: The accumulated pipeline state containing product, brands,
               brand_strategy, channel, and icps from Segmentation Agent
    
    Returns:
        Dict with "strategies" key containing dict[icp_id, StrategicBrief].
        On error, returns dict with updated "errors" list.
    """
    agent_name = "strategy"
    icps = state.get("icps", [])
    
    if not icps:
        logger.warning("Strategy Agent called with no ICPs")
        error = create_error(
            agent_name=agent_name,
            error_message="No ICPs available from Segmentation Agent",
        )
        return {"errors": add_error_to_state(state, error)}
    
    strategies: dict[str, StrategicBrief] = state.get("strategies", {}).copy()
    errors = list(state.get("errors", []))
    
    for icp in icps:
        try:
            brief = run_strategy_for_icp(state, icp)
            strategies[icp.icp_id] = brief
            logger.info(f"Generated strategy for ICP: {icp.name}")
            
        except Exception as e:
            logger.error(f"Strategy Agent failed for ICP {icp.icp_id}: {e}")
            error = create_error(
                agent_name=agent_name,
                error_message=str(e),
                icp_id=icp.icp_id,
            )
            errors.append(error)
            # Continue processing other ICPs
    
    result = {"strategies": strategies}
    if errors != state.get("errors", []):
        result["errors"] = errors
    
    return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["run_strategy_agent", "run_strategy_for_icp"]
