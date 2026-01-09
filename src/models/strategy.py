"""
Strategic Brief model for Sartor Ad Engine.

Defines the output schema for the Strategy Agent.
"""

from pydantic import BaseModel, Field


class StrategicBrief(BaseModel):
    """
    Strategic positioning brief for a specific ICP.
    
    Defines what to communicate before creative execution begins.
    Output by the Strategy Agent.
    """

    icp_id: str = Field(..., description="Reference to the target ICP")
    positioning_statement: str = Field(
        ..., 
        description="For [ICP] who [need], [Product] is the [category] that [differentiator]"
    )
    primary_pain_point: str = Field(
        ..., 
        description="The specific problem we solve for this ICP"
    )
    key_benefit: str = Field(
        ..., 
        description="Single most compelling benefit for this ICP"
    )
    proof_point: str = Field(
        ..., 
        description="Evidence: feature, stat, or claim that supports the benefit"
    )
    emotional_appeal: str = Field(
        ..., 
        description="The feeling we want to evoke"
    )
    tone_of_voice: str = Field(
        ..., 
        description="Specific tone for this ICP, aligned with brand voice"
    )
    message_hierarchy: list[str] = Field(
        ..., 
        description="[primary message, secondary message, tertiary message]",
        min_length=1,
        max_length=3
    )
