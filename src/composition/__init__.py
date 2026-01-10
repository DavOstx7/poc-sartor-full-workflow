"""
Composition Module for Sartor Ad Engine.

Provides deterministic ad composition: background scene + product image + text → final ad.
"""

from src.composition.compositor import Compositor, CompositionInput

__all__ = [
    "Compositor",
    "CompositionInput",
]
