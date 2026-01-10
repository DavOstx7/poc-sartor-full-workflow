"""
State management for Sartor Ad Engine.

Defines AdCreationState TypedDict for LangGraph state management.
All agents read from and write to this accumulated state object.

This module provides two state variants:
- AdCreationState: Basic TypedDict for simple sequential processing
- GraphState: Annotated TypedDict with reducers for parallel ICP processing
"""

import operator
from datetime import datetime
from typing import Annotated, TypedDict

from src.models import (
    AdCopy,
    BrandContext,
    BrandStrategyType,
    ChannelContext,
    CreativeConcept,
    ErrorLog,
    ICP,
    ImageAsset,
    ProductData,
    StoreContext,
    StrategicBrief,
)


# =============================================================================
# REDUCER FUNCTIONS
# =============================================================================

def merge_dicts(a: dict, b: dict) -> dict:
    """
    Reducer that merges two dictionaries.
    
    Used for parallel updates to dict-keyed fields (strategies, concepts, etc.).
    Later values (b) take precedence over earlier values (a).
    
    Args:
        a: Existing dictionary in state
        b: New dictionary to merge in
        
    Returns:
        Merged dictionary with all keys from both
    """
    if a is None:
        return b or {}
    if b is None:
        return a
    return {**a, **b}


def merge_lists(a: list, b: list) -> list:
    """
    Reducer that concatenates two lists.
    
    Used for accumulating errors from parallel branches.
    
    Args:
        a: Existing list in state
        b: New list to append
        
    Returns:
        Concatenated list
    """
    if a is None:
        return b or []
    if b is None:
        return a
    return a + b


# =============================================================================
# BASIC STATE (for individual agents and simple tests)
# =============================================================================

class AdCreationState(TypedDict, total=False):
    """
    Accumulated state object for the ad creation pipeline.
    
    This TypedDict is compatible with LangGraph's state management.
    All agents receive the full state and update their designated fields.
    
    State Flow:
    -----------
    INIT:               product, store_brand, product_brand, brand_strategy, channel, store_context
    AFTER SEGMENTATION: + icps
    AFTER STRATEGY:     + strategies[icp_id]
    AFTER CONCEPT:      + concepts[icp_id]
    AFTER COPY:         + copy[icp_id]
    AFTER DESIGN:       + scenes[icp_id]
    AFTER COMPOSITION:  + final_ads[icp_id]
    """

    # === INPUTS (set at initialization, immutable thereafter) ===
    product: ProductData
    store_brand: BrandContext
    product_brand: BrandContext | None  # Only if distinct from store (multi-brand retailer)
    brand_strategy: BrandStrategyType  # "store_dominant" | "product_dominant" | "co_branded"
    channel: ChannelContext
    store_context: StoreContext | None  # Optional store-level context

    # === AGENT OUTPUTS (populated sequentially) ===
    icps: list[ICP]  # Segmentation Agent output
    strategies: dict[str, StrategicBrief]  # Strategy Agent output, keyed by icp_id
    concepts: dict[str, CreativeConcept]  # Concept Agent output, keyed by icp_id
    copy: dict[str, AdCopy]  # Copy Agent output, keyed by icp_id
    scenes: dict[str, ImageAsset]  # Design Agent output, keyed by icp_id
    final_ads: dict[str, ImageAsset]  # Composition Module output, keyed by icp_id

    # === METADATA ===
    run_id: str  # Unique identifier for this pipeline run
    created_at: datetime  # Timestamp when pipeline started
    errors: list[ErrorLog]  # Error log for debugging and recovery


# =============================================================================
# GRAPH STATE WITH REDUCERS (for parallel ICP processing)
# =============================================================================

class GraphState(TypedDict, total=False):
    """
    LangGraph state with reducers for parallel ICP processing.
    
    This state variant uses Annotated types with reducer functions to enable
    safe parallel updates from multiple ICP processing branches. When multiple
    branches complete and return updates to the same field, the reducer function
    determines how to merge the results.
    
    Reducer behavior:
    - merge_dicts: For strategies, concepts, copy, scenes, final_ads
    - merge_lists: For errors
    - No reducer: For inputs (set once) and icps (set by segmentation only)
    
    Usage:
        Use GraphState when building the LangGraph workflow.
        Use AdCreationState for individual agent testing.
    """

    # === INPUTS (set at initialization, no reducer needed) ===
    product: ProductData
    store_brand: BrandContext
    product_brand: BrandContext | None
    brand_strategy: BrandStrategyType
    channel: ChannelContext
    store_context: StoreContext | None

    # === AGENT OUTPUTS ===
    # ICPs set once by segmentation (no reducer needed)
    icps: list[ICP]
    
    # Per-ICP outputs need merge reducer for parallel processing
    strategies: Annotated[dict[str, StrategicBrief], merge_dicts]
    concepts: Annotated[dict[str, CreativeConcept], merge_dicts]
    copy: Annotated[dict[str, AdCopy], merge_dicts]
    scenes: Annotated[dict[str, ImageAsset], merge_dicts]
    final_ads: Annotated[dict[str, ImageAsset], merge_dicts]

    # === METADATA ===
    run_id: str
    created_at: datetime
    errors: Annotated[list[ErrorLog], merge_lists]  # Accumulate errors from all branches
    
    # === GRAPH CONTROL (used internally by graph routing) ===
    current_icp_id: str | None  # Set when processing a specific ICP


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_initial_state(
    product: ProductData,
    store_brand: BrandContext,
    channel: ChannelContext,
    brand_strategy: BrandStrategyType = "store_dominant",
    product_brand: BrandContext | None = None,
    store_context: StoreContext | None = None,
    run_id: str | None = None,
) -> AdCreationState:
    """
    Factory function to create a properly initialized AdCreationState.
    
    Args:
        product: The product to generate ads for
        store_brand: Store/retailer brand identity
        channel: Target advertising channel
        brand_strategy: Which brand dominates the ad
        product_brand: Product brand if distinct from store
        store_context: Optional store context
        run_id: Optional custom run ID (auto-generated if not provided)
    
    Returns:
        Initialized AdCreationState ready for pipeline execution
    """
    import uuid

    return AdCreationState(
        # Inputs
        product=product,
        store_brand=store_brand,
        product_brand=product_brand,
        brand_strategy=brand_strategy,
        channel=channel,
        store_context=store_context,
        # Empty agent outputs
        icps=[],
        strategies={},
        concepts={},
        copy={},
        scenes={},
        final_ads={},
        # Metadata
        run_id=run_id or str(uuid.uuid4()),
        created_at=datetime.now(),
        errors=[],
    )


def create_graph_state(
    product: ProductData,
    store_brand: BrandContext,
    channel: ChannelContext,
    brand_strategy: BrandStrategyType = "store_dominant",
    product_brand: BrandContext | None = None,
    store_context: StoreContext | None = None,
    run_id: str | None = None,
) -> GraphState:
    """
    Factory function to create a properly initialized GraphState for LangGraph.
    
    This is the preferred factory when running the full pipeline with
    parallel ICP processing enabled.
    
    Args:
        product: The product to generate ads for
        store_brand: Store/retailer brand identity
        channel: Target advertising channel
        brand_strategy: Which brand dominates the ad
        product_brand: Product brand if distinct from store
        store_context: Optional store context
        run_id: Optional custom run ID (auto-generated if not provided)
    
    Returns:
        Initialized GraphState ready for LangGraph pipeline execution
    """
    import uuid

    return GraphState(
        # Inputs
        product=product,
        store_brand=store_brand,
        product_brand=product_brand,
        brand_strategy=brand_strategy,
        channel=channel,
        store_context=store_context,
        # Empty agent outputs
        icps=[],
        strategies={},
        concepts={},
        copy={},
        scenes={},
        final_ads={},
        # Metadata
        run_id=run_id or str(uuid.uuid4()),
        created_at=datetime.now(),
        errors=[],
        # Graph control
        current_icp_id=None,
    )
