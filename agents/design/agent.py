"""
Design Agent for Sartor Ad Engine.

Generates the visual background/context scene for the ad.
Does NOT include text or the product itself - those are
added by the Composition Module.

TODO: Implement in Phase 3
"""

from src.state import AdCreationState


def run(state: AdCreationState, icp_id: str) -> AdCreationState:
    """
    Execute the Design Agent for a specific ICP.
    
    Args:
        state: Current pipeline state with copy data
        icp_id: The ICP to generate a scene for
    
    Returns:
        Updated state with `scenes[icp_id]` populated
    
    Raises:
        NotImplementedError: Phase 3 - Implement agent logic
    """
    raise NotImplementedError("Phase 3: Implement design agent logic")
