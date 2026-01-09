"""
Design Agent Prompts

Mission: Generate the visual background/context scene for the ad.
         Does NOT include text or the product itself.

IMPORTANT: Unlike Agents 1-4, the Design Agent uses IMAGE GENERATION prompts
(for Imagen 3 / Flux), not LLM system prompts. This module provides templates
and builders for constructing effective scene-description prompts.

The Design Agent:
1. Takes the CreativeConcept's scene_description, mood, and color_direction
2. Applies brand-appropriate style modifiers
3. Outputs a prompt optimized for image generation models
4. Generates a background scene at the specified dimensions
"""

from typing import Literal

# =============================================================================
# CONSTANTS
# =============================================================================

ImageGenModel = Literal["imagen3", "flux", "dalle3", "midjourney"]

# Layout archetype to composition guidance mapping
LAYOUT_FRAMING_GUIDANCE = {
    "Hero Product Shot": "centered composition with negative space for product overlay, minimal background elements",
    "Hero Product with Stat Overlay": "centered composition with clear area for text overlay, clean background",
    "Problem/Solution Split": "split composition with contrasting environments, clear visual division",
    "Lifestyle Context": "environmental scene with natural product placement area, lifestyle setting",
    "Lifestyle Context Shot": "environmental scene with natural product placement area, lifestyle setting",
    "Stat Overlay": "clean background with designated area for metric display, minimal distractions",
    "Minimal/Editorial": "ultra-clean composition, gallery-style presentation, editorial aesthetic",
    "Minimal Editorial": "ultra-clean composition, gallery-style presentation, editorial aesthetic",
}

# Default style keywords by brand positioning
STYLE_BY_POSITIONING = {
    "premium": "high-end, refined, luxurious materials, sophisticated lighting",
    "luxury": "opulent, exclusive, rich textures, dramatic lighting, editorial quality",
    "mid-range": "polished, approachable, natural lighting, lifestyle feel",
    "budget": "bright, energetic, accessible, cheerful lighting",
    "technical": "precise, clean, studio quality, product-focused",
}


# =============================================================================
# NEGATIVE PROMPT COMPONENTS
# =============================================================================

# Elements to explicitly exclude from scene generation
STANDARD_NEGATIVE_PROMPT = """
text, words, letters, typography, logos, watermarks, signatures, 
product, merchandise, human hands, fingers holding objects,
distorted faces, extra limbs, blurry, low quality, pixelated,
cropped, out of frame, multiple subjects, collage
""".strip()

# Additional negatives for specific contexts
NEGATIVE_ADDITIONS = {
    "luxury": "cluttered, messy, cheap materials, harsh lighting",
    "technical": "organic shapes, messy, unstructured, chaotic",
    "lifestyle": "sterile, clinical, artificial, staged",
}


# =============================================================================
# PROMPT TEMPLATE
# =============================================================================

IMAGE_PROMPT_TEMPLATE = """
{scene_description}

Style: {mood}, {style_keywords}
Composition: {layout_framing}
Color palette: {color_direction}
Lighting: {lighting_guidance}
Quality: High resolution, professional {quality_type} photography, 8K, sharp focus

{additional_guidance}
""".strip()


NEGATIVE_PROMPT_TEMPLATE = """
{standard_negatives}
{context_negatives}
{custom_negatives}
""".strip()


# =============================================================================
# PROMPT BUILDER
# =============================================================================

def build_image_prompt(
    scene_description: str,
    mood: str,
    color_direction: str,
    layout_archetype: str,
    brand_visual_style: str,
    price_positioning: str = "mid-range",
    platform: str = "Instagram",
    custom_guidance: str = "",
) -> str:
    """
    Builds an optimized image generation prompt from concept data.
    
    Args:
        scene_description: Detailed scene description from CreativeConcept
        mood: Mood/atmosphere from CreativeConcept (e.g., "Calm and sophisticated")
        color_direction: How brand colors apply (e.g., "Cool blues with warm accents")
        layout_archetype: Layout type from CreativeConcept
        brand_visual_style: The dominant brand's visual_style description
        price_positioning: Product price tier for style calibration
        platform: Target platform (affects aspect ratio guidance)
        custom_guidance: Any additional prompt guidance
        
    Returns:
        Complete image generation prompt string
    """
    # Get layout-specific framing guidance
    layout_framing = LAYOUT_FRAMING_GUIDANCE.get(
        layout_archetype,
        "balanced composition with space for product and text overlay"
    )
    
    # Get style keywords based on positioning
    style_keywords = STYLE_BY_POSITIONING.get(
        price_positioning,
        STYLE_BY_POSITIONING["mid-range"]
    )
    
    # Incorporate brand visual style
    if brand_visual_style:
        style_keywords = f"{brand_visual_style}, {style_keywords}"
    
    # Determine lighting guidance from mood
    lighting_guidance = _infer_lighting_from_mood(mood)
    
    # Determine quality type (commercial vs editorial vs studio)
    quality_type = _infer_quality_type(layout_archetype, price_positioning)
    
    # Build additional guidance
    additional_parts = []
    if custom_guidance:
        additional_parts.append(custom_guidance)
    
    # Platform-specific notes
    platform_guidance = _get_platform_guidance(platform)
    if platform_guidance:
        additional_parts.append(platform_guidance)
    
    additional_guidance = "\n".join(additional_parts)
    
    return IMAGE_PROMPT_TEMPLATE.format(
        scene_description=scene_description,
        mood=mood,
        style_keywords=style_keywords,
        layout_framing=layout_framing,
        color_direction=color_direction,
        lighting_guidance=lighting_guidance,
        quality_type=quality_type,
        additional_guidance=additional_guidance,
    )


def build_negative_prompt(
    price_positioning: str = "mid-range",
    custom_negatives: str = "",
) -> str:
    """
    Builds a negative prompt to exclude unwanted elements.
    
    Args:
        price_positioning: Product price tier for context-specific negatives
        custom_negatives: Additional elements to exclude
        
    Returns:
        Complete negative prompt string
    """
    # Get context-specific negatives
    context_negatives = NEGATIVE_ADDITIONS.get(price_positioning, "")
    
    return NEGATIVE_PROMPT_TEMPLATE.format(
        standard_negatives=STANDARD_NEGATIVE_PROMPT,
        context_negatives=context_negatives,
        custom_negatives=custom_negatives,
    ).strip()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _infer_lighting_from_mood(mood: str) -> str:
    """Infers appropriate lighting guidance from the mood description."""
    mood_lower = mood.lower()
    
    if any(word in mood_lower for word in ["bold", "energetic", "vibrant", "dynamic"]):
        return "bright, high-contrast, dynamic lighting with bold shadows"
    elif any(word in mood_lower for word in ["calm", "serene", "peaceful", "soft"]):
        return "soft, diffused natural lighting, gentle shadows"
    elif any(word in mood_lower for word in ["sophisticated", "elegant", "refined"]):
        return "subtle, directional studio lighting, controlled highlights"
    elif any(word in mood_lower for word in ["warm", "cozy", "inviting"]):
        return "warm golden hour lighting, soft ambient glow"
    elif any(word in mood_lower for word in ["dramatic", "intense", "powerful"]):
        return "dramatic chiaroscuro lighting, strong contrast, moody"
    elif any(word in mood_lower for word in ["minimal", "clean", "modern"]):
        return "even, clean studio lighting, minimal shadows"
    else:
        return "professional studio lighting, balanced exposure"


def _infer_quality_type(layout_archetype: str, price_positioning: str) -> str:
    """Infers the photography quality type from context."""
    if "editorial" in layout_archetype.lower() or "minimal" in layout_archetype.lower():
        return "editorial"
    elif price_positioning in ["luxury", "premium"]:
        return "commercial advertising"
    elif "lifestyle" in layout_archetype.lower():
        return "lifestyle"
    else:
        return "commercial"


def _get_platform_guidance(platform: str) -> str:
    """Returns platform-specific composition guidance."""
    platform_lower = platform.lower()
    
    if "instagram" in platform_lower or "facebook" in platform_lower:
        return "Social media optimized, eye-catching, scroll-stopping visual"
    elif "google" in platform_lower or "display" in platform_lower:
        return "Web banner optimized, clear focal point for small sizes"
    elif "pinterest" in platform_lower:
        return "Vertical composition optimized, lifestyle-forward"
    else:
        return ""


# =============================================================================
# FULL PROMPT PACKAGE BUILDER
# =============================================================================

def build_image_gen_package(
    concept: dict,
    dominant_brand: dict,
    channel: dict,
    store_context: dict | None = None,
) -> dict:
    """
    Builds a complete image generation package from accumulated state.
    
    Args:
        concept: CreativeConcept dictionary from concept agent
        dominant_brand: The dominant brand dictionary (store or product based on strategy)
        channel: Channel context dictionary
        store_context: Optional store context for price positioning
        
    Returns:
        Dictionary with 'prompt', 'negative_prompt', 'width', 'height'
    """
    # Extract price positioning
    price_positioning = "mid-range"
    if store_context:
        price_positioning = store_context.get("price_positioning", "mid-range")
    
    # Build the main prompt
    prompt = build_image_prompt(
        scene_description=concept.get("scene_description", ""),
        mood=concept.get("mood", ""),
        color_direction=concept.get("color_direction", ""),
        layout_archetype=concept.get("layout_archetype", ""),
        brand_visual_style=dominant_brand.get("visual_style", ""),
        price_positioning=price_positioning,
        platform=channel.get("platform", ""),
    )
    
    # Build the negative prompt
    negative_prompt = build_negative_prompt(
        price_positioning=price_positioning,
    )
    
    # Get dimensions
    dims = channel.get("dimensions", {})
    
    return {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": dims.get("width", 1080),
        "height": dims.get("height", 1080),
    }


# =============================================================================
# MODEL-SPECIFIC FORMATTERS
# =============================================================================

def format_for_imagen3(prompt_package: dict) -> dict:
    """
    Formats the prompt package for Google Imagen 3.
    
    Args:
        prompt_package: Output from build_image_gen_package()
        
    Returns:
        Dictionary formatted for Imagen 3 API
    """
    return {
        "prompt": prompt_package["prompt"],
        "negativePrompt": prompt_package["negative_prompt"],
        "sampleCount": 1,
        "aspectRatio": _calculate_aspect_ratio(
            prompt_package["width"], 
            prompt_package["height"]
        ),
    }


def format_for_flux(prompt_package: dict) -> dict:
    """
    Formats the prompt package for Flux 1.1 Pro.
    
    Args:
        prompt_package: Output from build_image_gen_package()
        
    Returns:
        Dictionary formatted for Flux API
    """
    # Flux prefers prompt and negative in single field with --no
    combined_prompt = prompt_package["prompt"]
    if prompt_package["negative_prompt"]:
        combined_prompt += f" --no {prompt_package['negative_prompt']}"
    
    return {
        "prompt": combined_prompt,
        "width": prompt_package["width"],
        "height": prompt_package["height"],
        "guidance_scale": 7.5,
        "num_inference_steps": 50,
    }


def _calculate_aspect_ratio(width: int, height: int) -> str:
    """Calculates aspect ratio string from dimensions."""
    from math import gcd
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


# =============================================================================
# EXAMPLE USAGE (for documentation)
# =============================================================================

EXAMPLE_CONCEPT = {
    "scene_description": (
        "A serene home office setting with a clean wooden desk near a large window. "
        "Soft morning light streams in, casting gentle shadows. A minimalist plant sits "
        "in the corner. The background is intentionally blurred with subtle warm tones."
    ),
    "mood": "Calm and focused",
    "color_direction": "Warm wood tones with cool blue accents from the window light",
    "layout_archetype": "Hero Product Shot",
}

EXAMPLE_BRAND = {
    "brand_name": "SoundScale",
    "visual_style": "Premium, minimalist, tech-forward with clean lines",
}

EXAMPLE_CHANNEL = {
    "platform": "Instagram",
    "placement": "Feed",
    "dimensions": {"width": 1080, "height": 1080},
}

# Example output:
# prompt = build_image_prompt(
#     scene_description=EXAMPLE_CONCEPT["scene_description"],
#     mood=EXAMPLE_CONCEPT["mood"],
#     color_direction=EXAMPLE_CONCEPT["color_direction"],
#     layout_archetype=EXAMPLE_CONCEPT["layout_archetype"],
#     brand_visual_style=EXAMPLE_BRAND["visual_style"],
#     price_positioning="premium",
#     platform="Instagram",
# )
