"""
Sartor Ad Engine - Pydantic Models.

Central exports for all data models used in the ad generation pipeline.
"""

from .assets import ErrorLog, ImageAsset
from .brand import BrandContext, BrandStrategyType, ColorPalette
from .channel import ChannelContext, Dimensions, TextConstraints
from .concept import CreativeConcept, ProductPlacement, ProductSize
from .copy import AdCopy
from .icp import (
    ICP,
    AppealType,
    BehavioralTriggers,
    CommunicationPreferences,
    Demographic,
    Psychographics,
)
from .product import Price, ProductData
from .store import PricePositioning, StoreContext
from .strategy import StrategicBrief

__all__ = [
    # Product
    "ProductData",
    "Price",
    # Brand
    "BrandContext",
    "ColorPalette",
    "BrandStrategyType",
    # Channel
    "ChannelContext",
    "Dimensions",
    "TextConstraints",
    # Store
    "StoreContext",
    "PricePositioning",
    # ICP
    "ICP",
    "Demographic",
    "Psychographics",
    "BehavioralTriggers",
    "CommunicationPreferences",
    "AppealType",
    # Strategy
    "StrategicBrief",
    # Concept
    "CreativeConcept",
    "ProductPlacement",
    "ProductSize",
    # Copy
    "AdCopy",
    # Assets
    "ImageAsset",
    "ErrorLog",
]
