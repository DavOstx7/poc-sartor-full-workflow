"""
LLM factory for Sartor Ad Engine.

Provides factory functions to create LangChain LLM clients
based on model name prefixes.
"""

from langchain_core.language_models import BaseChatModel

from src.config import get_settings


def create_llm(
    model_name: str | None = None,
    temperature: float = 0.7,
    **kwargs,
) -> BaseChatModel:
    """
    Create an LLM client based on model name prefix.
    
    Supports:
    - Gemini models (prefix: "gemini")
    - Claude models (prefix: "claude")
    
    Args:
        model_name: Model identifier (e.g., "gemini-2.0-flash", "claude-sonnet-4-20250514")
        temperature: Sampling temperature (0.0 - 1.0)
        **kwargs: Additional arguments passed to the LLM constructor
    
    Returns:
        Configured LangChain chat model
    
    Raises:
        ValueError: If model_name is unrecognized or API key is missing
    """
    settings = get_settings()

    if model_name is None:
        model_name = settings.strategy_model  # Default to strategy model

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


def create_llm_for_agent(agent_name: str, **kwargs) -> BaseChatModel:
    """
    Create an LLM client for a specific agent using configured model names.
    
    Args:
        agent_name: One of 'segmentation', 'strategy', 'concept', 'copy'
        **kwargs: Additional arguments passed to create_llm
    
    Returns:
        Configured LangChain chat model for the specified agent
    """
    settings = get_settings()

    model_mapping = {
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

    return create_llm(model_name=model_mapping[agent_name], **kwargs)
