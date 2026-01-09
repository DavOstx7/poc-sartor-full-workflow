"""
Creative Concept models for Sartor Ad Engine.

Defines the output schema for the Concept Agent.
"""

from typing import Literal

from pydantic import BaseModel, Field


# Product size in the ad composition
ProductSize = Literal["dominant", "balanced", "subtle"]


class ProductPlacement(BaseModel):
    """Directives for how the product should be placed in the final ad."""

    position: str = Field(
        ..., 
        description="Position in frame (e.g., 'center', 'left-third', 'bottom-right')"
    )
    size: ProductSize = Field(..., description="Relative size in the composition")
    treatment: str = Field(
        ..., 
        description="Visual treatment (e.g., 'floating with shadow', 'on surface')"
    )


class CreativeConcept(BaseModel):
    """
    Creative concept for a specific ICP.
    
    Defines the Big Idea and visual direction that brings the strategy to life.
    Output by the Concept Agent.
    """

    icp_id: str = Field(..., description="Reference to the target ICP")
    big_idea: str = Field(
        ..., 
        description="The unifying creative concept in one sentence"
    )
    visual_metaphor: str | None = Field(
        None, 
        description="If applicable, the visual analogy used"
    )
    layout_archetype: str = Field(
        ..., 
        description="e.g., 'Problem/Solution Split', 'Hero Product with Stat Overlay'"
    )
    scene_description: str = Field(
        ..., 
        description="Detailed description of background/context scene (no product, no text)"
    )
    product_placement: ProductPlacement
    mood: str = Field(
        ..., 
        description="e.g., 'Energetic and bold', 'Calm and sophisticated'"
    )
    color_direction: str = Field(
        ..., 
        description="How brand colors should be applied"
    )
    focal_point: str = Field(
        ..., 
        description="What the eye should be drawn to first"
    )
