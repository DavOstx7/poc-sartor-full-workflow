"""
Ad Copy models for Sartor Ad Engine.

Defines the output schema for the Copy Agent.
"""

from pydantic import BaseModel, Field


class AdCopy(BaseModel):
    """
    Ad copy for a specific ICP.
    
    Contains headline, body, and CTA tailored to the ICP
    and aligned with the creative concept.
    Output by the Copy Agent.
    """

    icp_id: str = Field(..., description="Reference to the target ICP")
    headline: str = Field(
        ..., 
        description="Attention-grabbing headline (within channel constraints)"
    )
    subheadline: str | None = Field(
        None, 
        description="Optional secondary headline"
    )
    body_copy: str = Field(
        ..., 
        description="Supporting message (within channel constraints)"
    )
    cta_text: str = Field(
        ..., 
        description="Call-to-action button text"
    )
    cta_urgency: str | None = Field(
        None, 
        description="Optional urgency element"
    )
    legal_disclaimer: str | None = Field(
        None, 
        description="Legal text if required"
    )
