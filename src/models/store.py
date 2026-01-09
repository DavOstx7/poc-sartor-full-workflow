"""
Store context models for Sartor Ad Engine.

Defines optional store-level context for enhanced personalization.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


# Price positioning options
PricePositioning = Literal["budget", "mid-range", "premium", "luxury"]


class StoreContext(BaseModel):
    """
    Optional store-level context.
    
    Provides additional context about the store's customer base
    and market positioning to enhance ad personalization.
    """

    customer_summary: str | None = Field(
        None, 
        description="Description of typical customer base"
    )
    price_positioning: PricePositioning | None = Field(
        None, 
        description="Market positioning: budget, mid-range, premium, or luxury"
    )
    competitors: list[str] = Field(
        default_factory=list, 
        description="Key competitor names"
    )
    store_statistics: dict[str, Any] | None = Field(
        None, 
        description="Historical performance data if available"
    )
