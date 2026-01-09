"""
Channel context models for Sartor Ad Engine.

Defines the advertising channel/platform specifications.
"""

from pydantic import BaseModel, Field


class Dimensions(BaseModel):
    """Image dimensions in pixels."""

    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


class TextConstraints(BaseModel):
    """Character limits for ad copy elements."""

    headline_max_chars: int = Field(..., gt=0)
    body_max_chars: int = Field(..., gt=0)
    cta_max_chars: int = Field(..., gt=0)


class ChannelContext(BaseModel):
    """
    Advertising channel/platform context.
    
    Defines where the ad will be displayed and its constraints.
    """

    platform: str = Field(..., description="Target platform (e.g., 'Facebook', 'Instagram')")
    placement: str = Field(..., description="Specific placement (e.g., 'Feed', 'Stories')")
    dimensions: Dimensions = Field(..., description="Required image dimensions")
    text_constraints: TextConstraints = Field(..., description="Copy character limits")
    audience_context: str | None = Field(
        None, 
        description="Platform-specific audience notes"
    )
