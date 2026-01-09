"""
Shared prompt components for Sartor Ad Engine agents.

This module contains reusable prompt fragments, constants, and helper
functions used across multiple agents to ensure consistency.
"""

from typing import Literal

# =============================================================================
# CONSTANTS
# =============================================================================

BrandStrategy = Literal["store_dominant", "product_dominant", "co_branded"]

# =============================================================================
# SHARED CONTEXT FRAGMENTS
# =============================================================================

ECOMMERCE_CONTEXT = """
## Context: eCommerce Advertising

You are working within an automated ad generation system for eCommerce products.
- **Scope:** Physical goods sold online (DTC brands, retailers, marketplaces)
- **Goal:** Generate personalized static advertisements for specific customer segments
- **Constraint:** All outputs must be grounded in the provided product and brand data
""".strip()


BRAND_STRATEGY_RULES = """
## Brand Strategy Rules

The `brand_strategy` field determines which brand identity dominates the ad:

### `store_dominant`
- **When:** DTC brands, or retailers selling unbranded/weak-brand products
- **Voice & Tone:** Use the STORE BRAND's `brand_voice` and `tone_keywords`
- **Visual Identity:** Store brand's `color_palette` and `visual_style`
- **Positioning:** Product is positioned as the store's offering

### `product_dominant`
- **When:** Retailer selling strong product brands (e.g., Sony, Nike, Apple)
- **Voice & Tone:** Use the PRODUCT BRAND's `brand_voice` and `tone_keywords`
- **Visual Identity:** Product brand's `color_palette` and `visual_style`
- **Positioning:** Product brand is hero; store is distribution channel
- **Copy Note:** May include "Available at [Store Name]" as secondary element

### `co_branded`
- **When:** Exclusive partnerships, collaborations, or co-branded products
- **Voice & Tone:** Blend both brand voices harmoniously
- **Visual Identity:** Integrate elements from both brands' palettes/styles
- **Positioning:** Emphasize the partnership or collaboration aspect
""".strip()


ACCUMULATED_STATE_REMINDER = """
## Important: Full Context Access

You have access to the COMPLETE accumulated state from prior agents:
- Original product data (name, description, features, benefits, price, category)
- Store brand identity (voice, tone, visual style, colors)
- Product brand identity (if applicable and distinct from store)
- Brand strategy (store_dominant | product_dominant | co_branded)
- Channel context (platform, dimensions, text constraints)
- Store context (customer base, price positioning, competitors)
- Prior agent outputs (if any)

Use ALL relevant context. Do not ignore or forget earlier information.
""".strip()


# =============================================================================
# OUTPUT QUALITY GUARDRAILS
# =============================================================================

GROUNDING_GUARDRAILS = """
## Grounding Requirements

Your output must be traceable to the input data:
- **Feature claims** → Must exist in `product.features` or `product.description`
- **Benefit claims** → Must exist in `product.benefits` or be directly derivable from features
- **Price references** → Must use actual `product.price` values
- **Brand attributes** → Must reflect the dominant brand's documented voice/tone

❌ Do NOT invent features, specs, or benefits not in the data
❌ Do NOT use generic marketing speak disconnected from the product
❌ Do NOT contradict the brand voice with mismatched tone
""".strip()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_dominant_brand_instruction(brand_strategy: BrandStrategy) -> str:
    """
    Returns instructions on which brand to prioritize based on strategy.
    
    Args:
        brand_strategy: One of 'store_dominant', 'product_dominant', 'co_branded'
        
    Returns:
        Instruction string for the LLM about which brand identity to use
    """
    instructions = {
        "store_dominant": (
            "Use the STORE BRAND as the primary identity. "
            "Adopt its voice, tone keywords, and visual style. "
            "The product brand (if present) is secondary or invisible."
        ),
        "product_dominant": (
            "Use the PRODUCT BRAND as the primary identity. "
            "Adopt its voice, tone keywords, and visual style. "
            "The store brand appears only as 'Available at [Store]' or similar."
        ),
        "co_branded": (
            "BLEND both brand identities harmoniously. "
            "Combine tone keywords from both brands. "
            "Visual style should integrate elements from both palettes."
        ),
    }
    return instructions.get(brand_strategy, instructions["store_dominant"])


def format_brand_context(
    store_brand: dict,
    product_brand: dict | None,
    brand_strategy: BrandStrategy
) -> str:
    """
    Formats brand information for prompt injection based on strategy.
    
    Args:
        store_brand: Store brand dictionary with voice, tone, colors, etc.
        product_brand: Product brand dictionary (None if same as store)
        brand_strategy: Which brand dominates
        
    Returns:
        Formatted brand context string for prompt inclusion
    """
    lines = ["## Brand Context", ""]
    
    # Store brand (always present)
    lines.append(f"### Store Brand: {store_brand.get('brand_name', 'Unknown')}")
    lines.append(f"- **Voice:** {store_brand.get('brand_voice', 'Not specified')}")
    lines.append(f"- **Tone:** {', '.join(store_brand.get('tone_keywords', []))}")
    lines.append(f"- **Visual Style:** {store_brand.get('visual_style', 'Not specified')}")
    lines.append("")
    
    # Product brand (if distinct)
    if product_brand:
        lines.append(f"### Product Brand: {product_brand.get('brand_name', 'Unknown')}")
        lines.append(f"- **Voice:** {product_brand.get('brand_voice', 'Not specified')}")
        lines.append(f"- **Tone:** {', '.join(product_brand.get('tone_keywords', []))}")
        lines.append(f"- **Visual Style:** {product_brand.get('visual_style', 'Not specified')}")
        lines.append("")
    
    # Strategy directive
    lines.append(f"### Active Strategy: `{brand_strategy}`")
    lines.append(get_dominant_brand_instruction(brand_strategy))
    
    return "\n".join(lines)
