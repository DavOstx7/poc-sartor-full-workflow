"""
LangGraph workflow definition for Sartor Ad Engine.

This module defines the complete ad generation pipeline as a LangGraph
workflow with parallel ICP processing support via the Send API.

Workflow Structure:
    START → Segmentation → [Fan-out per ICP] → Process ICP → END
    
    Where Process ICP runs: Strategy → Concept → Copy → Design → Composition
    for each ICP in parallel.
"""

import logging
import time
from pathlib import Path
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agents.common.agent_utils import create_error, model_to_dict
from agents.concept.agent import run_concept_for_icp
from agents.copy.agent import run_copy_for_icp
from agents.design.agent import generate_scene_for_icp
from agents.segmentation.agent import run_segmentation_agent
from agents.strategy.agent import run_strategy_for_icp
from src.composition import CompositionInput, Compositor
from src.config import get_settings
from src.models import ICP, ErrorLog, ImageAsset
from src.state import GraphState


logger = logging.getLogger(__name__)


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

def segmentation_node(state: GraphState) -> dict:
    """
    LangGraph node for the Segmentation Agent.
    
    Identifies 1-4 distinct ICPs for the product. This is the first
    step in the pipeline and runs exactly once.
    
    Args:
        state: Current graph state with product and brand inputs
        
    Returns:
        State update with 'icps' list populated
    """
    start_time = time.time()
    logger.info("[Segmentation] Starting segmentation...")
    
    try:
        result = run_segmentation_agent(state)
        elapsed = time.time() - start_time
        
        if "icps" in result:
            logger.info(
                f"[Segmentation] Complete: {len(result['icps'])} ICPs generated "
                f"in {elapsed:.2f}s"
            )
        else:
            logger.warning("[Segmentation] No ICPs returned")
            
        return result
        
    except Exception as e:
        logger.error(f"[Segmentation] Failed: {e}")
        return {
            "errors": [
                ErrorLog(
                    agent_name="segmentation",
                    error_message=str(e),
                )
            ]
        }


def process_icp_node(state: GraphState) -> dict:
    """
    LangGraph node that processes a single ICP through all stages.
    
    Runs Strategy → Concept → Copy → Design → Composition sequentially
    for the ICP specified in state['current_icp_id'].
    
    This node is invoked via Send() for each ICP, enabling parallel
    processing of different ICPs.
    
    Args:
        state: Current graph state with 'current_icp_id' set
        
    Returns:
        State update with strategy, concept, copy, scene, and final_ad
        for this ICP
    """
    icp_id = state.get("current_icp_id")
    if not icp_id:
        logger.error("[ProcessICP] No current_icp_id in state")
        return {
            "errors": [
                ErrorLog(
                    agent_name="process_icp",
                    error_message="No ICP ID provided",
                )
            ]
        }
    
    # Find the ICP object
    icps = state.get("icps", [])
    icp = next((i for i in icps if i.icp_id == icp_id), None)
    
    if not icp:
        logger.error(f"[ProcessICP] ICP not found: {icp_id}")
        return {
            "errors": [
                ErrorLog(
                    agent_name="process_icp",
                    icp_id=icp_id,
                    error_message=f"ICP not found: {icp_id}",
                )
            ]
        }
    
    logger.info(f"[ProcessICP] Processing ICP: {icp.name} ({icp_id})")
    start_time = time.time()
    
    # Results accumulator
    results: dict = {}
    errors: list[ErrorLog] = []
    
    # --- Stage 1: Strategy ---
    try:
        logger.info(f"[ProcessICP:{icp_id}] Running Strategy Agent...")
        strategy = run_strategy_for_icp(state, icp)
        results["strategies"] = {icp_id: strategy}
        logger.info(f"[ProcessICP:{icp_id}] Strategy complete: {strategy.key_benefit[:50]}...")
    except Exception as e:
        logger.error(f"[ProcessICP:{icp_id}] Strategy failed: {e}")
        errors.append(ErrorLog(agent_name="strategy", icp_id=icp_id, error_message=str(e)))
        # Can't continue without strategy
        results["errors"] = errors
        return results
    
    # --- Stage 2: Concept ---
    try:
        logger.info(f"[ProcessICP:{icp_id}] Running Concept Agent...")
        concept = run_concept_for_icp(state, icp, strategy)
        results["concepts"] = {icp_id: concept}
        logger.info(f"[ProcessICP:{icp_id}] Concept complete: {concept.big_idea[:50]}...")
    except Exception as e:
        logger.error(f"[ProcessICP:{icp_id}] Concept failed: {e}")
        errors.append(ErrorLog(agent_name="concept", icp_id=icp_id, error_message=str(e)))
        results["errors"] = errors
        return results
    
    # --- Stage 3: Copy ---
    try:
        logger.info(f"[ProcessICP:{icp_id}] Running Copy Agent...")
        ad_copy = run_copy_for_icp(state, icp, strategy, concept)
        results["copy"] = {icp_id: ad_copy}
        logger.info(f"[ProcessICP:{icp_id}] Copy complete: {ad_copy.headline}")
    except Exception as e:
        logger.error(f"[ProcessICP:{icp_id}] Copy failed: {e}")
        errors.append(ErrorLog(agent_name="copy", icp_id=icp_id, error_message=str(e)))
        results["errors"] = errors
        return results
    
    # --- Stage 4: Design ---
    try:
        logger.info(f"[ProcessICP:{icp_id}] Running Design Agent...")
        scene = generate_scene_for_icp(state, icp, concept)
        results["scenes"] = {icp_id: scene}
        logger.info(f"[ProcessICP:{icp_id}] Design complete: {scene.path}")
    except Exception as e:
        logger.error(f"[ProcessICP:{icp_id}] Design failed: {e}")
        errors.append(ErrorLog(agent_name="design", icp_id=icp_id, error_message=str(e)))
        results["errors"] = errors
        return results
    
    # --- Stage 5: Composition ---
    try:
        logger.info(f"[ProcessICP:{icp_id}] Running Composition...")
        final_ad = _run_composition(state, icp_id, concept, ad_copy, scene)
        results["final_ads"] = {icp_id: final_ad}
        logger.info(f"[ProcessICP:{icp_id}] Composition complete: {final_ad.path}")
    except Exception as e:
        logger.error(f"[ProcessICP:{icp_id}] Composition failed: {e}")
        errors.append(ErrorLog(agent_name="composition", icp_id=icp_id, error_message=str(e)))
        results["errors"] = errors
        return results
    
    # All stages complete
    elapsed = time.time() - start_time
    logger.info(f"[ProcessICP:{icp_id}] Complete in {elapsed:.2f}s")
    
    if errors:
        results["errors"] = errors
    
    return results


def _run_composition(
    state: GraphState,
    icp_id: str,
    concept,
    ad_copy,
    scene: ImageAsset,
) -> ImageAsset:
    """
    Run the deterministic Composition Module for a single ICP.
    
    Args:
        state: Current graph state
        icp_id: ID of the ICP being processed
        concept: CreativeConcept for this ICP
        ad_copy: AdCopy for this ICP
        scene: Background scene ImageAsset for this ICP
        
    Returns:
        ImageAsset with path to final composed ad
    """
    settings = get_settings()
    product = state["product"]
    
    # Determine output path
    output_dir = Path(settings.output_dir) / "ads"
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = state.get("run_id", "unknown")
    output_path = output_dir / f"ad_{icp_id}_{run_id[:8]}.png"
    
    # Get first product image
    product_image = product.images[0] if product.images else None
    
    if not product_image:
        raise ValueError("No product images available for composition")
    
    # Build composition input
    composition_input = CompositionInput(
        background_path=scene.path,
        product_image_source=product_image,
        ad_copy=ad_copy,
        concept=concept,
        store_brand=state["store_brand"],
        product_brand=state.get("product_brand"),
        brand_strategy=state.get("brand_strategy", "store_dominant"),
        channel=state["channel"],
        output_path=str(output_path),
        output_format="PNG",
        remove_product_bg=True,
    )
    
    # Run compositor
    compositor = Compositor()
    result = compositor.compose(composition_input)
    
    return result


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def route_to_icps(state: GraphState) -> list[Send]:
    """
    Conditional edge function that fans out to process each ICP.
    
    After segmentation completes, this function creates a Send object
    for each ICP, enabling parallel processing.
    
    Args:
        state: Current graph state with 'icps' populated
        
    Returns:
        List of Send objects, one per ICP, each routing to 'process_icp'
        with the current_icp_id set
    """
    icps = state.get("icps", [])
    
    if not icps:
        logger.warning("[Router] No ICPs to process, ending workflow")
        return []
    
    logger.info(f"[Router] Fanning out to {len(icps)} ICPs")
    
    # Create a Send for each ICP
    sends = []
    for icp in icps:
        sends.append(
            Send(
                "process_icp",
                {
                    **state,
                    "current_icp_id": icp.icp_id,
                }
            )
        )
    
    return sends


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph workflow for ad generation.
    
    The graph structure:
    - START → segmentation (identifies 1-4 ICPs)
    - segmentation → [conditional fan-out via Send] → process_icp (parallel)
    - process_icp → END
    
    Each ICP is processed through Strategy→Concept→Copy→Design→Composition
    within the process_icp node.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Building ad generation graph...")
    
    # Create graph with our state schema
    builder = StateGraph(GraphState)
    
    # Add nodes
    builder.add_node("segmentation", segmentation_node)
    builder.add_node("process_icp", process_icp_node)
    
    # Add edges
    builder.add_edge(START, "segmentation")
    
    # Conditional edge for fan-out after segmentation
    builder.add_conditional_edges(
        "segmentation",
        route_to_icps,
        # If no ICPs, the empty list will end the graph
        # Otherwise, Send objects route to process_icp
    )
    
    # Each process_icp ends the graph (they run in parallel)
    builder.add_edge("process_icp", END)
    
    # Compile the graph
    graph = builder.compile()
    
    logger.info("Graph compiled successfully")
    
    return graph


def get_graph():
    """
    Get or create the compiled graph instance.
    
    This is a convenience function for use by the runner.
    
    Returns:
        Compiled StateGraph
    """
    return build_graph()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "build_graph",
    "get_graph",
    "segmentation_node",
    "process_icp_node",
    "route_to_icps",
]
