"""
Product data models for Sartor Ad Engine.

Defines the ProductData schema representing an eCommerce product catalog item.
"""

from typing import Any

from pydantic import BaseModel, Field


class Price(BaseModel):
    """Product pricing information."""

    value: float
    currency: str = "USD"
    compare_at_price: float | None = None  # Original price for discounts


class ProductData(BaseModel):
    """
    Complete product catalog item.
    
    This is the primary input for the ad generation pipeline.
    All product information must be grounded in this data.
    """

    product_id: str = Field(..., description="Unique identifier (SKU)")
    name: str = Field(..., description="Product display name")
    description: str = Field(..., description="Full product description")
    features: list[str] = Field(..., description="Key product features/specs")
    benefits: list[str] = Field(..., description="Customer-facing benefits")
    price: Price
    category: str = Field(..., description="Product category/taxonomy")
    images: list[str] = Field(..., description="Product image URLs")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional attributes")
