"""
Concept Agent for Sartor Ad Engine.

Develops the creative Big Idea and visual layout direction
that brings the strategy to life for a specific ICP.

TODO: Implement in Phase 3
"""

from src.state import AdCreationState


def run(state: AdCreationState, icp_id: str) -> AdCreationState:
    """
    Execute the Concept Agent for a specific ICP.
    
    Args:
        state: Current pipeline state with strategy data
        icp_id: The ICP to create a concept for
    
    Returns:
        Updated state with `concepts[icp_id]` populated
    
    Raises:
        NotImplementedError: Phase 3 - Implement agent logic
    """
    raise NotImplementedError("Phase 3: Implement concept agent logic")
