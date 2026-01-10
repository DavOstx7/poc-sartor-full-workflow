"""
Copy Agent implementation for Sartor Ad Engine.

Mission: Write the ad copy—headline, body, and CTA—tailored to the ICP and
aligned with the concept.

The Copy Agent is responsible for all textual content in the ad. It must
respect character limits from the channel context and align with both the
strategic brief (message hierarchy) and the creative concept (tone, Big Idea).
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
from src.models import AdCopy, CreativeConcept, ICP, StrategicBrief
from src.state import AdCreationState
from src.utils.llm_factory import create_llm_for_agent

from .prompts import SYSTEM_PROMPT, format_user_message


logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_input_summary(icp: ICP, concept: CreativeConcept) -> str:
    """Create a brief summary of inputs for logging."""
    return f"ICP: {icp.name}, Big Idea: {concept.big_idea[:50]}..."


def _prepare_user_message_data(
    state: AdCreationState,
    icp: ICP,
    strategy: StrategicBrief,
    concept: CreativeConcept,
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
        "concept": model_to_dict(concept),
        "channel": model_to_dict(channel),
    }


# =============================================================================
# SINGLE ICP PROCESSING
# =============================================================================

def run_copy_for_icp(
    state: AdCreationState,
    icp: ICP,
    strategy: StrategicBrief,
    concept: CreativeConcept,
) -> AdCopy:
    """
    Generate ad copy for a single ICP.
    
    Args:
        state: The accumulated pipeline state
        icp: The specific ICP to generate copy for
        strategy: The StrategicBrief for this ICP
        concept: The CreativeConcept for this ICP
        
    Returns:
        AdCopy for this ICP
        
    Raises:
        Exception: If LLM invocation fails
    """
    agent_name = "copy"
    
    # 1. Log input
    input_summary = _build_input_summary(icp, concept)
    log_agent_call(agent_name, input_summary)
    
    # 2. Prepare message data
    message_data = _prepare_user_message_data(state, icp, strategy, concept)
    
    # 3. Build prompts
    system_prompt = SYSTEM_PROMPT
    user_message = format_user_message(
        product=message_data["product"],
        store_brand=message_data["store_brand"],
        product_brand=message_data["product_brand"],
        brand_strategy=message_data["brand_strategy"],
        icp=message_data["icp"],
        strategy=message_data["strategy"],
        concept=message_data["concept"],
        channel=message_data["channel"],
    )
    
    # 4. Create LLM with structured output
    llm = create_llm_for_agent(agent_name)
    structured_llm = llm.with_structured_output(AdCopy)
    
    # 5. Build messages and invoke
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    
    response: AdCopy = structured_llm.invoke(messages)
    
    # 6. Log output
    log_agent_call(agent_name, input_summary, response)
    
    # 7. Validate character limits (warning only - LLM should respect via prompt)
    _validate_character_limits(response, state["channel"])
    
    return response


def _validate_character_limits(copy: AdCopy, channel) -> None:
    """Log warnings if copy exceeds character limits."""
    constraints = channel.text_constraints
    
    if len(copy.headline) > constraints.headline_max_chars:
        logger.warning(
            f"Headline exceeds limit: {len(copy.headline)}/{constraints.headline_max_chars}"
        )
    
    if len(copy.body_copy) > constraints.body_max_chars:
        logger.warning(
            f"Body copy exceeds limit: {len(copy.body_copy)}/{constraints.body_max_chars}"
        )
    
    if len(copy.cta_text) > constraints.cta_max_chars:
        logger.warning(
            f"CTA exceeds limit: {len(copy.cta_text)}/{constraints.cta_max_chars}"
        )


# =============================================================================
# MAIN AGENT FUNCTION
# =============================================================================

def run_copy_agent(state: AdCreationState) -> dict:
    """
    LangGraph node function for the Copy Agent.
    
    Processes all ICPs in sequence, generating AdCopy for each.
    Requires strategies and concepts to be available from prior agents.
    
    Args:
        state: The accumulated pipeline state containing product, brands,
               channel, icps, strategies, and concepts
    
    Returns:
        Dict with "copy" key containing dict[icp_id, AdCopy].
        On error, returns dict with updated "errors" list.
    """
    agent_name = "copy"
    icps = state.get("icps", [])
    strategies = state.get("strategies", {})
    concepts = state.get("concepts", {})
    
    if not icps:
        logger.warning("Copy Agent called with no ICPs")
        error = create_error(
            agent_name=agent_name,
            error_message="No ICPs available",
        )
        return {"errors": add_error_to_state(state, error)}
    
    copy_outputs: dict[str, AdCopy] = state.get("copy", {}).copy()
    errors = list(state.get("errors", []))
    
    for icp in icps:
        # Skip if missing dependencies
        if icp.icp_id not in strategies:
            logger.warning(f"No strategy for ICP {icp.icp_id}, skipping")
            continue
        
        if icp.icp_id not in concepts:
            logger.warning(f"No concept for ICP {icp.icp_id}, skipping")
            continue
        
        try:
            strategy = strategies[icp.icp_id]
            concept = concepts[icp.icp_id]
            ad_copy = run_copy_for_icp(state, icp, strategy, concept)
            copy_outputs[icp.icp_id] = ad_copy
            logger.info(f"Generated copy for ICP: {icp.name} - Headline: {ad_copy.headline}")
            
        except Exception as e:
            logger.error(f"Copy Agent failed for ICP {icp.icp_id}: {e}")
            error = create_error(
                agent_name=agent_name,
                error_message=str(e),
                icp_id=icp.icp_id,
            )
            errors.append(error)
            # Continue processing other ICPs
    
    result = {"copy": copy_outputs}
    if errors != state.get("errors", []):
        result["errors"] = errors
    
    return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["run_copy_agent", "run_copy_for_icp"]
