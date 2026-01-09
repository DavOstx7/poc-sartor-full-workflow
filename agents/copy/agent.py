"""
Copy Agent for Sartor Ad Engine.

Writes ad copy (headline, body, CTA) tailored to the ICP
and aligned with the creative concept.

TODO: Implement in Phase 3
"""

from src.state import AdCreationState


def run(state: AdCreationState, icp_id: str) -> AdCreationState:
    """
    Execute the Copy Agent for a specific ICP.
    
    Args:
        state: Current pipeline state with concept data
        icp_id: The ICP to create copy for
    
    Returns:
        Updated state with `copy[icp_id]` populated
    
    Raises:
        NotImplementedError: Phase 3 - Implement agent logic
    """
    raise NotImplementedError("Phase 3: Implement copy agent logic")
