"""
Design Agent implementation for Sartor Ad Engine.

Mission: Generate the visual background/context scene for the ad.
Does NOT include text or the product itself - those are added
by the Composition Module.

IMPORTANT: Unlike Agents 1-4, the Design Agent uses an IMAGE GENERATION API
(Imagen 3 / Flux), not an LLM with structured output. This module builds the
image generation prompt and calls the appropriate API.
"""

import logging
from pathlib import Path
from typing import Any

from agents.common.agent_utils import (
    add_error_to_state,
    create_error,
    get_dominant_brand,
    log_agent_call,
    model_to_dict,
)
from src.config import get_settings
from src.models import CreativeConcept, ICP, ImageAsset
from src.state import AdCreationState

from .prompts import build_image_gen_package, format_for_imagen3, format_for_flux


logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_input_summary(icp: ICP, concept: CreativeConcept) -> str:
    """Create a brief summary of inputs for logging."""
    return f"ICP: {icp.name}, Layout: {concept.layout_archetype}"


def _ensure_output_directory() -> Path:
    """Ensure the output directory exists and return its path."""
    settings = get_settings()
    output_dir = Path(settings.output_dir) / "scenes"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _generate_scene_filename(icp_id: str, run_id: str) -> str:
    """Generate a unique filename for the scene image."""
    return f"scene_{icp_id}_{run_id[:8]}.png"


# =============================================================================
# IMAGE GENERATION (STUB)
# =============================================================================

def _call_image_generation_api(
    prompt_package: dict,
    output_path: Path,
) -> ImageAsset:
    """
    Call the image generation API to create the scene.
    
    NOTE: This is currently a STUB implementation. It logs the prompt
    and creates a placeholder ImageAsset. To enable real image generation:
    
    1. For Imagen 3: Integrate with Google Cloud Vertex AI
    2. For Flux: Integrate with Replicate or similar API
    
    Args:
        prompt_package: Dict with 'prompt', 'negative_prompt', 'width', 'height'
        output_path: Path where the generated image should be saved
        
    Returns:
        ImageAsset with path and metadata
    """
    settings = get_settings()
    design_model = settings.design_model
    
    # Log the prompt that would be used
    logger.info(f"[Design Agent] Model: {design_model}")
    logger.info(f"[Design Agent] Prompt: {prompt_package['prompt'][:200]}...")
    logger.info(f"[Design Agent] Dimensions: {prompt_package['width']}x{prompt_package['height']}")
    
    # Format for specific API
    if design_model.startswith("imagen"):
        api_payload = format_for_imagen3(prompt_package)
        logger.debug(f"Imagen API payload: {api_payload}")
    else:
        api_payload = format_for_flux(prompt_package)
        logger.debug(f"Flux API payload: {api_payload}")
    
    # TODO: Actual API call would go here
    # For now, we create a placeholder asset
    
    # Create placeholder file if it doesn't exist
    if not output_path.exists():
        # Write a simple placeholder (empty file for now)
        output_path.touch()
        logger.warning(f"Created placeholder scene at {output_path}")
    
    return ImageAsset(
        path=str(output_path),
        url=None,
        prompt_used=prompt_package["prompt"],
        width=prompt_package["width"],
        height=prompt_package["height"],
    )


# =============================================================================
# SINGLE ICP PROCESSING
# =============================================================================

def generate_scene_for_icp(
    state: AdCreationState,
    icp: ICP,
    concept: CreativeConcept,
) -> ImageAsset:
    """
    Generate background scene for a single ICP.
    
    Args:
        state: The accumulated pipeline state
        icp: The specific ICP to generate scene for
        concept: The CreativeConcept for this ICP
        
    Returns:
        ImageAsset with path to generated scene
        
    Raises:
        Exception: If image generation fails
    """
    agent_name = "design"
    
    # 1. Log input
    input_summary = _build_input_summary(icp, concept)
    log_agent_call(agent_name, input_summary)
    
    # 2. Get dominant brand for visual style
    dominant_brand = get_dominant_brand(state)
    
    # 3. Build image generation prompt package
    channel = state["channel"]
    store_context = state.get("store_context")
    
    prompt_package = build_image_gen_package(
        concept=model_to_dict(concept),
        dominant_brand=model_to_dict(dominant_brand),
        channel=model_to_dict(channel),
        store_context=model_to_dict(store_context) if store_context else None,
    )
    
    # 4. Determine output path
    output_dir = _ensure_output_directory()
    run_id = state.get("run_id", "unknown")
    filename = _generate_scene_filename(icp.icp_id, run_id)
    output_path = output_dir / filename
    
    # 5. Call image generation API
    asset = _call_image_generation_api(prompt_package, output_path)
    
    # 6. Log output
    log_agent_call(agent_name, input_summary, asset)
    
    return asset


# =============================================================================
# MAIN AGENT FUNCTION
# =============================================================================

def run_design_agent(state: AdCreationState) -> dict:
    """
    LangGraph node function for the Design Agent.
    
    Processes all ICPs in sequence, generating a background scene for each.
    Requires concepts to be available from the Concept Agent.
    
    Args:
        state: The accumulated pipeline state containing icps and concepts
    
    Returns:
        Dict with "scenes" key containing dict[icp_id, ImageAsset].
        On error, returns dict with updated "errors" list.
    """
    agent_name = "design"
    icps = state.get("icps", [])
    concepts = state.get("concepts", {})
    
    if not icps:
        logger.warning("Design Agent called with no ICPs")
        error = create_error(
            agent_name=agent_name,
            error_message="No ICPs available",
        )
        return {"errors": add_error_to_state(state, error)}
    
    scenes: dict[str, ImageAsset] = state.get("scenes", {}).copy()
    errors = list(state.get("errors", []))
    
    for icp in icps:
        # Skip if no concept available
        if icp.icp_id not in concepts:
            logger.warning(f"No concept for ICP {icp.icp_id}, skipping design")
            continue
        
        try:
            concept = concepts[icp.icp_id]
            asset = generate_scene_for_icp(state, icp, concept)
            scenes[icp.icp_id] = asset
            logger.info(f"Generated scene for ICP: {icp.name} -> {asset.path}")
            
        except Exception as e:
            logger.error(f"Design Agent failed for ICP {icp.icp_id}: {e}")
            error = create_error(
                agent_name=agent_name,
                error_message=str(e),
                icp_id=icp.icp_id,
            )
            errors.append(error)
            # Continue processing other ICPs
    
    result = {"scenes": scenes}
    if errors != state.get("errors", []):
        result["errors"] = errors
    
    return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["run_design_agent", "generate_scene_for_icp"]
