"""Common utilities and shared components for Sartor Ad Engine agents."""

from .prompts_common import (
    ECOMMERCE_CONTEXT,
    BRAND_STRATEGY_RULES,
    ACCUMULATED_STATE_REMINDER,
    GROUNDING_GUARDRAILS,
    get_dominant_brand_instruction,
    format_brand_context,
    BrandStrategy,
)

__all__ = [
    "ECOMMERCE_CONTEXT",
    "BRAND_STRATEGY_RULES",
    "ACCUMULATED_STATE_REMINDER",
    "GROUNDING_GUARDRAILS",
    "get_dominant_brand_instruction",
    "format_brand_context",
    "BrandStrategy",
]
