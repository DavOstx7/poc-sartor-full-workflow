"""
Concept Agent implementation for Sartor Ad Engine.

Mission: Develop the creative Big Idea and visual layout direction that brings
the strategy to life.

The Concept Agent bridges strategy and execution. It translates the StrategicBrief
into concrete creative direction: the unifying Big Idea, visual layout, scene
description, and product placement—all while respecting the dominant brand's
visual identity.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.common.agent_utils import (
    add_error_to_state,
    create_error,
    get_dominant_brand,
    log_agent_call,
    model_to_dict,
)
from src.models import ICP, CreativeConcept, StrategicBrief
from src.state import AdCreationState
from src.utils.llm_factory import create_llm_for_agent

from .prompts import SYSTEM_PROMPT, format_user_message


logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_input_summary(icp: ICP, strategy: StrategicBrief) -> str:
    """Create a brief summary of inputs for logging."""
    return f"ICP: {icp.name}, Big Idea TBD, Strategy: {strategy.key_benefit}"


def _prepare_user_message_data(
    state: AdCreationState,
    icp: ICP,
    strategy: StrategicBrief,
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
        "strategy": model_to_dict(strategy),
        "channel": model_to_dict(channel),
    }


# =============================================================================
# SINGLE ICP PROCESSING
# =============================================================================

def run_concept_for_icp(
    state: AdCreationState,
    icp: ICP,
    strategy: StrategicBrief,
) -> CreativeConcept:
    """
    Generate creative concept for a single ICP.
    
    Args:
        state: The accumulated pipeline state
        icp: The specific ICP to generate concept for
        strategy: The StrategicBrief for this ICP
        
    Returns:
        CreativeConcept for this ICP
        
    Raises:
        Exception: If LLM invocation fails
    """
    agent_name = "concept"
    
    # 1. Log input
    input_summary = _build_input_summary(icp, strategy)
    log_agent_call(agent_name, input_summary)
    
    # 2. Prepare message data
    message_data = _prepare_user_message_data(state, icp, strategy)
    
    # 3. Build prompts
    system_prompt = SYSTEM_PROMPT
    user_message = format_user_message(
        product=message_data["product"],
        store_brand=message_data["store_brand"],
        product_brand=message_data["product_brand"],
        brand_strategy=message_data["brand_strategy"],
        icp=message_data["icp"],
        strategy=message_data["strategy"],
        channel=message_data["channel"],
    )
    
    # 4. Create LLM with structured output
    llm = create_llm_for_agent(agent_name)
    structured_llm = llm.with_structured_output(CreativeConcept)
    
    # 5. Build messages and invoke
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    
    response: CreativeConcept = structured_llm.invoke(messages)
    
    # 6. Log output
    log_agent_call(agent_name, input_summary, response)
    
    return response


# =============================================================================
# MAIN AGENT FUNCTION
# =============================================================================

def run_concept_agent(state: AdCreationState) -> dict:
    """
    LangGraph node function for the Concept Agent.
    
    Processes all ICPs in sequence, generating a CreativeConcept for each.
    Requires strategies to be available from the Strategy Agent.
    
    Args:
        state: The accumulated pipeline state containing product, brands,
               channel, icps, and strategies from prior agents
    
    Returns:
        Dict with "concepts" key containing dict[icp_id, CreativeConcept].
        On error, returns dict with updated "errors" list.
    """
    agent_name = "concept"
    icps = state.get("icps", [])
    strategies = state.get("strategies", {})
    
    if not icps:
        logger.warning("Concept Agent called with no ICPs")
        error = create_error(
            agent_name=agent_name,
            error_message="No ICPs available",
        )
        return {"errors": add_error_to_state(state, error)}
    
    concepts: dict[str, CreativeConcept] = state.get("concepts", {}).copy()
    errors = list(state.get("errors", []))
    
    for icp in icps:
        # Skip if no strategy available for this ICP
        if icp.icp_id not in strategies:
            logger.warning(f"No strategy available for ICP {icp.icp_id}, skipping")
            error = create_error(
                agent_name=agent_name,
                error_message=f"No strategy available for ICP",
                icp_id=icp.icp_id,
            )
            errors.append(error)
            continue
        
        try:
            strategy = strategies[icp.icp_id]
            concept = run_concept_for_icp(state, icp, strategy)
            concepts[icp.icp_id] = concept
            logger.info(f"Generated concept for ICP: {icp.name} - Big Idea: {concept.big_idea}")
            
        except Exception as e:
            logger.error(f"Concept Agent failed for ICP {icp.icp_id}: {e}")
            error = create_error(
                agent_name=agent_name,
                error_message=str(e),
                icp_id=icp.icp_id,
            )
            errors.append(error)
            # Continue processing other ICPs
    
    result = {"concepts": concepts}
    if errors != state.get("errors", []):
        result["errors"] = errors
    
    return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["run_concept_agent", "run_concept_for_icp"]
