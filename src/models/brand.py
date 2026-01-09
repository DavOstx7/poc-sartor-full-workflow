"""
Brand data models for Sartor Ad Engine.

Defines BrandContext (reusable for store and product brands) and BrandStrategy.
"""

from typing import Literal

from pydantic import BaseModel, Field


# Brand strategy type - determines which brand identity dominates the ad
BrandStrategyType = Literal["store_dominant", "product_dominant", "co_branded"]


class ColorPalette(BaseModel):
    """Brand color scheme with hex codes."""

    primary: str = Field(..., description="Primary brand color (hex)")
    secondary: str | None = Field(None, description="Secondary color (hex)")
    accent: str | None = Field(None, description="Accent color (hex)")
    background: str | None = Field(None, description="Background color (hex)")


class BrandContext(BaseModel):
    """
    Brand identity context.
    
    This model is reusable for both store_brand and product_brand fields.
    When product_brand is None, the store IS the brand (DTC model).
    """

    brand_name: str = Field(..., description="Brand display name")
    brand_voice: str = Field(
        ..., 
        description="Description of brand personality (e.g., 'Premium, minimalist, tech-forward')"
    )
    tone_keywords: list[str] = Field(
        ..., 
        description="Adjectives defining tone (e.g., ['confident', 'aspirational', 'warm'])"
    )
    visual_style: str = Field(
        ..., 
        description="Visual identity description (e.g., 'Clean lines, dark backgrounds')"
    )
    color_palette: ColorPalette
    logo_url: str = Field(..., description="Brand logo asset URL")
    tagline: str | None = Field(None, description="Brand tagline if applicable")
