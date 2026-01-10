"""
Layout specifications for ad composition archetypes.

Defines zones and positioning rules for each layout type.
"""

from dataclasses import dataclass
from difflib import get_close_matches


@dataclass(frozen=True)
class LayoutZone:
    """
    Defines a rectangular zone as percentages of the canvas.
    
    Values are ratios (0.0 to 1.0) representing start and end positions.
    """
    
    x_start: float  # Left edge as % of width (0.0 = left)
    x_end: float    # Right edge as % of width (1.0 = right)
    y_start: float  # Top edge as % of height (0.0 = top)
    y_end: float    # Bottom edge as % of height (1.0 = bottom)
    
    def get_bounds(self, width: int, height: int) -> tuple[int, int, int, int]:
        """
        Convert zone to pixel coordinates.
        
        Returns:
            Tuple of (x1, y1, x2, y2) in pixels.
        """
        return (
            int(width * self.x_start),
            int(height * self.y_start),
            int(width * self.x_end),
            int(height * self.y_end),
        )
    
    def get_center(self, width: int, height: int) -> tuple[int, int]:
        """Get center point in pixels."""
        x1, y1, x2, y2 = self.get_bounds(width, height)
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def get_size(self, width: int, height: int) -> tuple[int, int]:
        """Get zone size in pixels."""
        x1, y1, x2, y2 = self.get_bounds(width, height)
        return (x2 - x1, y2 - y1)


@dataclass(frozen=True)
class LayoutSpec:
    """
    Complete layout specification for an archetype.
    
    Defines zones for product, text, and logo placement.
    """
    
    name: str
    description: str
    product_zone: LayoutZone      # Where product can be placed
    headline_zone: LayoutZone     # Headline text area
    body_zone: LayoutZone         # Body copy area
    cta_zone: LayoutZone          # CTA button area
    logo_zone: LayoutZone         # Primary logo placement
    secondary_logo_zone: LayoutZone | None = None  # For co-branded

    # Typography settings
    headline_font_ratio: float = 0.045   # Font size as ratio of canvas height
    body_font_ratio: float = 0.025       # Body font size ratio
    cta_font_ratio: float = 0.028        # CTA font size ratio


# =============================================================================
# Layout Archetype Definitions
# =============================================================================

LAYOUT_ARCHETYPES: dict[str, LayoutSpec] = {
    # -------------------------------------------------------------------------
    # Hero Product with Stat Overlay
    # Product dominates center, text overlay at bottom-left
    # -------------------------------------------------------------------------
    "Hero Product with Stat Overlay": LayoutSpec(
        name="Hero Product with Stat Overlay",
        description="Product centered and prominent, with key stat/headline overlaid at bottom",
        product_zone=LayoutZone(0.15, 0.85, 0.10, 0.70),    # Center-dominant
        headline_zone=LayoutZone(0.05, 0.65, 0.68, 0.82),   # Bottom-left
        body_zone=LayoutZone(0.05, 0.65, 0.82, 0.92),       # Below headline
        cta_zone=LayoutZone(0.05, 0.40, 0.88, 0.98),        # Bottom-left corner
        logo_zone=LayoutZone(0.75, 0.95, 0.03, 0.12),       # Top-right
        headline_font_ratio=0.05,
    ),
    
    # -------------------------------------------------------------------------
    # Problem/Solution Split
    # Left side: text, Right side: product
    # -------------------------------------------------------------------------
    "Problem/Solution Split": LayoutSpec(
        name="Problem/Solution Split",
        description="Vertical split: text on left, product on right",
        product_zone=LayoutZone(0.50, 0.95, 0.10, 0.85),    # Right half
        headline_zone=LayoutZone(0.05, 0.48, 0.15, 0.35),   # Left, upper
        body_zone=LayoutZone(0.05, 0.48, 0.38, 0.65),       # Left, middle
        cta_zone=LayoutZone(0.05, 0.35, 0.70, 0.85),        # Left, lower
        logo_zone=LayoutZone(0.05, 0.25, 0.03, 0.12),       # Top-left
        headline_font_ratio=0.042,
    ),
    
    # -------------------------------------------------------------------------
    # Lifestyle Context Shot
    # Product subtle in corner, large text area for storytelling
    # -------------------------------------------------------------------------
    "Lifestyle Context Shot": LayoutSpec(
        name="Lifestyle Context Shot",
        description="Emphasis on lifestyle context, product positioned subtly",
        product_zone=LayoutZone(0.55, 0.95, 0.50, 0.95),    # Bottom-right, smaller
        headline_zone=LayoutZone(0.05, 0.70, 0.08, 0.25),   # Top-left
        body_zone=LayoutZone(0.05, 0.55, 0.28, 0.45),       # Below headline
        cta_zone=LayoutZone(0.05, 0.35, 0.50, 0.62),        # Mid-left
        logo_zone=LayoutZone(0.75, 0.95, 0.03, 0.12),       # Top-right
        headline_font_ratio=0.048,
    ),
    
    # -------------------------------------------------------------------------
    # Minimal Product Focus
    # Clean, centered layout with product as hero
    # -------------------------------------------------------------------------
    "Minimal Product Focus": LayoutSpec(
        name="Minimal Product Focus",
        description="Clean, minimal design with centered product and text below",
        product_zone=LayoutZone(0.20, 0.80, 0.12, 0.62),    # Center, balanced
        headline_zone=LayoutZone(0.10, 0.90, 0.65, 0.78),   # Bottom-center
        body_zone=LayoutZone(0.15, 0.85, 0.78, 0.88),       # Below headline
        cta_zone=LayoutZone(0.30, 0.70, 0.88, 0.96),        # Bottom-center
        logo_zone=LayoutZone(0.40, 0.60, 0.02, 0.10),       # Top-center
        headline_font_ratio=0.04,
    ),
}

# Default fallback layout
DEFAULT_LAYOUT = "Minimal Product Focus"


def get_layout_spec(archetype: str) -> LayoutSpec:
    """
    Get layout specification for an archetype.
    
    Uses fuzzy matching if exact name not found.
    
    Args:
        archetype: Layout archetype name (e.g., "Hero Product with Stat Overlay")
        
    Returns:
        LayoutSpec for the archetype
        
    Raises:
        ValueError: If no matching archetype found
    """
    # Exact match
    if archetype in LAYOUT_ARCHETYPES:
        return LAYOUT_ARCHETYPES[archetype]
    
    # Fuzzy match
    archetype_names = list(LAYOUT_ARCHETYPES.keys())
    matches = get_close_matches(archetype, archetype_names, n=1, cutoff=0.4)
    
    if matches:
        return LAYOUT_ARCHETYPES[matches[0]]
    
    # Fallback to default
    return LAYOUT_ARCHETYPES[DEFAULT_LAYOUT]


def list_archetypes() -> list[str]:
    """Return list of available layout archetype names."""
    return list(LAYOUT_ARCHETYPES.keys())
