"""
State management for Sartor Ad Engine.

Defines AdCreationState TypedDict for LangGraph state management.
All agents read from and write to this accumulated state object.
"""

from datetime import datetime
from typing import TypedDict

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
