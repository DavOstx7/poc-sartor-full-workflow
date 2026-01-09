"""
Ideal Customer Profile (ICP) models for Sartor Ad Engine.

Defines the ICP schema output by the Segmentation Agent.
"""

from typing import Literal

from pydantic import BaseModel, Field


# Types of appeals that resonate with customers
# Expanded from architecture to include additional appeal types from Phase 1 prompts
AppealType = Literal[
    "emotional_appeals",
    "data_and_specs",
    "social_proof",
    "urgency",
    "exclusivity",
    "value_proposition",
]


class Demographic(BaseModel):
    """Demographic characteristics of the ICP."""

    age_range: str = Field(..., description="e.g., '25-34'")
    gender: str | None = Field(None, description="Gender if relevant")
    income_level: str = Field(..., description="e.g., 'Upper-middle'")
    location_type: str = Field(..., description="e.g., 'Urban', 'Suburban'")


class Psychographics(BaseModel):
    """Psychological characteristics of the ICP."""

    values: list[str] = Field(..., description="Core values")
    lifestyle: str = Field(..., description="Lifestyle description")
    aspirations: str = Field(..., description="Goals and aspirations")


class BehavioralTriggers(BaseModel):
    """Purchase behavior patterns of the ICP."""

    purchase_motivators: list[str] = Field(..., description="What drives purchase decisions")
    objections: list[str] = Field(..., description="Common concerns or hesitations")
    decision_factors: list[str] = Field(..., description="Key factors in final decision")


class CommunicationPreferences(BaseModel):
    """How the ICP prefers to be communicated with."""

    tone: str = Field(..., description="Preferred communication tone")
    vocabulary_level: str = Field(..., description="e.g., 'Technical', 'Casual'")
    responds_to: list[AppealType] = Field(
        ..., 
        description="Types of appeals that resonate"
    )


class ICP(BaseModel):
    """
    Ideal Customer Profile.
    
    A detailed persona representing a target customer segment.
    Output by the Segmentation Agent.
    """

    icp_id: str = Field(..., description="Unique identifier for this ICP")
    name: str = Field(..., description="Descriptive name (e.g., 'Tech-Forward Professional')")
    demographic: Demographic
    psychographics: Psychographics
    behavioral_triggers: BehavioralTriggers
    communication_preferences: CommunicationPreferences
