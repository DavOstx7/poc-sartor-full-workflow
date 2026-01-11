"""
LLM factory for Sartor Ad Engine.

Provides factory functions to create LangChain LLM clients
based on model name prefixes.
"""

import time
from threading import Lock
from typing import Literal

from langchain_core.language_models import BaseChatModel

from src.config import get_settings


# Agent name type for type safety
AgentName = Literal["segmentation", "strategy", "concept", "copy"]

# Per-agent default temperatures based on task requirements
AGENT_TEMPERATURES: dict[AgentName, float] = {
    "segmentation": 0.3,  # Analytical, deterministic
    "strategy": 0.5,      # Balanced reasoning
    "concept": 0.8,       # Creative ideation
    "copy": 0.6,          # Creative but controlled
}


class RateLimiter:
    """
    Thread-safe rate limiter for LLM API calls.
    
    Used to respect free tier limits. Set rpm=0 to disable.
    Remove this class when upgrading to a paid tier.
    """
    _last_call: float = 0
    _lock = Lock()
    
    @classmethod
    def wait(cls, rpm: float) -> None:
        if rpm <= 0:
            return
        interval = 60.0 / rpm
        with cls._lock:
            elapsed = time.time() - cls._last_call
            if elapsed < interval:
                time.sleep(interval - elapsed)
            cls._last_call = time.time()


def create_llm(
    model_name: str,
    temperature: float = 0.7,
    **kwargs,
) -> BaseChatModel:
    """
    Create an LLM client based on model name prefix.
    
    Supports:
    - Gemini models (prefix: "gemini")
    - Claude models (prefix: "claude")
    
    Args:
        model_name: Model identifier (e.g., "gemini-2.0-flash", "claude-sonnet-4-20250514").
                    Required - use create_llm_for_agent() for agent-specific defaults.
        temperature: Sampling temperature (0.0 - 1.0). Default: 0.7
        **kwargs: Additional arguments passed to the LLM constructor
    
    Returns:
        Configured LangChain chat model
    
    Raises:
        ValueError: If model_name is unrecognized or API key is missing
    """
    settings = get_settings()
    
    # Rate limit for free tier support (set rpm=0 to disable)
    RateLimiter.wait(settings.llm_rate_limit_rpm)

    if model_name.startswith("gemini"):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=settings.google_api_key,
            **kwargs,
        )

    elif model_name.startswith("claude"):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=settings.anthropic_api_key,
            **kwargs,
        )

    else:
        raise ValueError(
            f"Unknown model: {model_name}. "
            "Supported prefixes: 'gemini', 'claude'"
        )


def create_llm_for_agent(
    agent_name: AgentName,
    temperature: float | None = None,
    **kwargs,
) -> BaseChatModel:
    """
    Create an LLM client for a specific agent using configured model names.
    
    Uses agent-specific default temperatures optimized for each task type:
    - segmentation: 0.3 (analytical)
    - strategy: 0.5 (balanced)
    - concept: 0.8 (creative)
    - copy: 0.6 (creative but controlled)
    
    Note: The 'design' agent is excluded as it uses image generation, not LLM.
    
    Args:
        agent_name: One of 'segmentation', 'strategy', 'concept', 'copy'
        temperature: Override default temperature. If None, uses agent-specific default.
        **kwargs: Additional arguments passed to create_llm
    
    Returns:
        Configured LangChain chat model for the specified agent
    
    Raises:
        ValueError: If agent_name is not recognized
    """
    settings = get_settings()

    model_mapping: dict[AgentName, str] = {
        "segmentation": settings.segmentation_model,
        "strategy": settings.strategy_model,
        "concept": settings.concept_model,
        "copy": settings.copy_model,
    }

    if agent_name not in model_mapping:
        raise ValueError(
            f"Unknown agent: {agent_name}. "
            f"Valid agents: {list(model_mapping.keys())}"
        )

    # Use provided temperature or fall back to agent-specific default
    temp = temperature if temperature is not None else AGENT_TEMPERATURES[agent_name]

    return create_llm(
        model_name=model_mapping[agent_name],
        temperature=temp,
        **kwargs,
    )

