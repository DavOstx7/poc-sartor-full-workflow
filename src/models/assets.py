"""
Asset and error tracking models for Sartor Ad Engine.

Defines ImageAsset for Design Agent output and ErrorLog for error tracking.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ImageAsset(BaseModel):
    """
    Generated or processed image asset.
    
    Used for both Design Agent output (scene images)
    and Composition Module output (final ads).
    """

    path: str = Field(..., description="Local file path")
    url: str | None = Field(None, description="Remote URL if applicable")
    prompt_used: str | None = Field(
        None, 
        description="Image generation prompt (for debugging)"
    )
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


class ErrorLog(BaseModel):
    """
    Error log entry for tracking failures in the pipeline.
    
    Stored in AdCreationState.errors for debugging and recovery.
    """

    agent_name: str = Field(..., description="Name of the agent that failed")
    icp_id: str | None = Field(
        None, 
        description="ICP being processed when error occurred"
    )
    error_message: str = Field(..., description="Error description")
    timestamp: datetime = Field(default_factory=datetime.now)
