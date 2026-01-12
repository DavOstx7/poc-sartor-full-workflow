"""
Text rendering for ad composition.

Handles font loading, text wrapping, and rendering of headlines, body copy, and CTAs.
"""

import logging
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

from src.composition.templates.layout_specs import LayoutZone

logger = logging.getLogger(__name__)

# Font directory (relative to this file's package root)
FONT_DIR = Path(__file__).parent.parent.parent / "assets" / "fonts"

# Font file names (primary: DejaVu Sans, fallback: Inter)
FONT_FILES = {
    "regular": "DejaVuSans.ttf",
    "bold": "DejaVuSans-Bold.ttf",
    "semibold": "DejaVuSans-Bold.ttf",  # DejaVu has no semibold, use bold
}

# Fallback font files (Inter if available)
FALLBACK_FONT_FILES = {
    "regular": "Inter-Regular.ttf",
    "bold": "Inter-Bold.ttf",
    "semibold": "Inter-SemiBold.ttf",
}

# Text alignment options
TextAlign = Literal["left", "center", "right"]


def load_font(
    weight: Literal["regular", "bold", "semibold"] = "regular",
    size: int = 24,
) -> ImageFont.FreeTypeFont:
    """
    Load font with fallback chain: DejaVu -> Inter -> System -> Default.
    
    Args:
        weight: Font weight ('regular', 'bold', 'semibold')
        size: Font size in pixels
        
    Returns:
        PIL ImageFont
    """
    # Try primary fonts (DejaVu)
    font_file = FONT_DIR / FONT_FILES.get(weight, FONT_FILES["regular"])
    try:
        if font_file.exists():
            return ImageFont.truetype(str(font_file), size)
    except Exception as e:
        logger.warning(f"Failed to load primary font {font_file}: {e}")
    
    # Try fallback fonts (Inter)
    fallback_file = FONT_DIR / FALLBACK_FONT_FILES.get(weight, FALLBACK_FONT_FILES["regular"])
    try:
        if fallback_file.exists():
            return ImageFont.truetype(str(fallback_file), size)
    except Exception as e:
        logger.warning(f"Failed to load fallback font {fallback_file}: {e}")
    
    # Fallback: try system fonts
    for system_font in ["Arial.ttf", "arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf"]:
        try:
            return ImageFont.truetype(system_font, size)
        except OSError:
            continue
    
    # Ultimate fallback: default font (may be bitmap)
    logger.warning(f"Using default font (size may not apply correctly)")
    return ImageFont.load_default()


def wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """
    Split text into lines that fit within max_width.
    
    Args:
        text: Text to wrap
        font: Font to measure with
        max_width: Maximum line width in pixels
        
    Returns:
        List of text lines
    """
    if not text:
        return []
    
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        # Test if word fits on current line
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line.append(word)
        else:
            # Word doesn't fit, start new line
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    # Add remaining line
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines


def get_text_size(
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    line_spacing: int = 8,
) -> tuple[int, int]:
    """
    Calculate total bounding box for multi-line text.
    
    Args:
        lines: List of text lines
        font: Font to measure with
        line_spacing: Pixels between lines
        
    Returns:
        (width, height) in pixels
    """
    if not lines:
        return (0, 0)
    
    max_width = 0
    total_height = 0
    
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        
        max_width = max(max_width, line_width)
        total_height += line_height
        
        if i < len(lines) - 1:
            total_height += line_spacing
    
    return (max_width, total_height)


def render_text_block(
    draw: ImageDraw.Draw,
    text: str,
    position: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    color: str,
    max_width: int,
    line_spacing: int = 8,
    align: TextAlign = "left",
    shadow: bool = True,
    shadow_color: str = "#00000080",
    shadow_offset: tuple[int, int] = (2, 2),
) -> int:
    """
    Render wrapped text block.
    
    Args:
        draw: ImageDraw object
        text: Text to render
        position: (x, y) top-left position
        font: Font to use
        color: Text color (hex or name)
        max_width: Maximum line width
        line_spacing: Pixels between lines
        align: Text alignment
        shadow: Whether to add drop shadow
        shadow_color: Shadow color (with alpha)
        shadow_offset: Shadow offset (x, y)
        
    Returns:
        Total height of rendered text block
    """
    lines = wrap_text(text, font, max_width)
    
    if not lines:
        return 0
    
    x, y = position
    total_height = 0
    
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        
        # Calculate x position based on alignment
        if align == "center":
            line_x = x + (max_width - line_width) // 2
        elif align == "right":
            line_x = x + max_width - line_width
        else:
            line_x = x
        
        line_y = y + total_height
        
        # Draw shadow first
        if shadow:
            draw.text(
                (line_x + shadow_offset[0], line_y + shadow_offset[1]),
                line,
                font=font,
                fill=shadow_color,
            )
        
        # Draw text
        draw.text((line_x, line_y), line, font=font, fill=color)
        
        total_height += line_height + line_spacing
    
    return total_height - line_spacing  # Remove trailing spacing


def render_headline(
    canvas: Image.Image,
    text: str,
    zone: LayoutZone,
    brand_color: str,
    font_size_ratio: float = 0.045,
    align: TextAlign = "left",
) -> tuple[Image.Image, int]:
    """
    Render headline text in specified zone.
    
    Args:
        canvas: Canvas to draw on (modified in place)
        text: Headline text
        zone: Layout zone for headline
        brand_color: Primary brand color (hex)
        font_size_ratio: Font size as ratio of canvas height
        align: Text alignment
        
    Returns:
        Tuple of (canvas, height_used)
    """
    draw = ImageDraw.Draw(canvas)
    
    # Calculate zone bounds
    x1, y1, x2, y2 = zone.get_bounds(canvas.width, canvas.height)
    zone_width = x2 - x1
    
    # Calculate font size
    font_size = int(canvas.height * font_size_ratio)
    font = load_font("bold", font_size)
    
    # Render text
    height = render_text_block(
        draw,
        text,
        (x1, y1),
        font,
        brand_color,
        zone_width,
        line_spacing=int(font_size * 0.3),
        align=align,
        shadow=True,
    )
    
    return canvas, height


def render_body(
    canvas: Image.Image,
    text: str,
    zone: LayoutZone,
    y_offset: int = 0,
    color: str = "#FFFFFF",
    font_size_ratio: float = 0.025,
    align: TextAlign = "left",
) -> tuple[Image.Image, int]:
    """
    Render body copy in specified zone.
    
    Args:
        canvas: Canvas to draw on
        text: Body copy text
        zone: Layout zone for body
        y_offset: Vertical offset from zone top (e.g., after headline)
        color: Text color
        font_size_ratio: Font size as ratio of canvas height
        align: Text alignment
        
    Returns:
        Tuple of (canvas, height_used)
    """
    draw = ImageDraw.Draw(canvas)
    
    x1, y1, x2, y2 = zone.get_bounds(canvas.width, canvas.height)
    zone_width = x2 - x1
    
    font_size = int(canvas.height * font_size_ratio)
    font = load_font("regular", font_size)
    
    height = render_text_block(
        draw,
        text,
        (x1, y1 + y_offset),
        font,
        color,
        zone_width,
        line_spacing=int(font_size * 0.4),
        align=align,
        shadow=True,
    )
    
    return canvas, height


def render_cta_button(
    canvas: Image.Image,
    text: str,
    zone: LayoutZone,
    accent_color: str,
    text_color: str = "#FFFFFF",
    font_size_ratio: float = 0.028,
) -> Image.Image:
    """
    Render CTA as a button with rounded rectangle background.
    
    Args:
        canvas: Canvas to draw on
        text: CTA text
        zone: Layout zone for CTA
        accent_color: Button background color
        text_color: Button text color
        font_size_ratio: Font size ratio
        
    Returns:
        Canvas with CTA button
    """
    draw = ImageDraw.Draw(canvas)
    
    x1, y1, x2, y2 = zone.get_bounds(canvas.width, canvas.height)
    
    font_size = int(canvas.height * font_size_ratio)
    font = load_font("semibold", font_size)
    
    # Measure text
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate button size with padding
    padding_x = int(font_size * 1.2)
    padding_y = int(font_size * 0.6)
    button_width = text_width + padding_x * 2
    button_height = text_height + padding_y * 2
    
    # Center button in zone (or align left if zone is small)
    zone_width = x2 - x1
    if button_width < zone_width:
        button_x = x1
    else:
        button_x = x1
    button_y = y1
    
    # Draw rounded rectangle
    corner_radius = int(button_height * 0.3)
    draw.rounded_rectangle(
        [button_x, button_y, button_x + button_width, button_y + button_height],
        radius=corner_radius,
        fill=accent_color,
    )
    
    # Draw text centered in button
    text_x = button_x + padding_x
    text_y = button_y + padding_y
    draw.text((text_x, text_y), text, font=font, fill=text_color)
    
    return canvas


def render_subheadline(
    canvas: Image.Image,
    text: str,
    zone: LayoutZone,
    y_offset: int = 0,
    color: str = "#CCCCCC",
    font_size_ratio: float = 0.030,
) -> tuple[Image.Image, int]:
    """
    Render subheadline (smaller than headline, above body).
    
    Args:
        canvas: Canvas to draw on
        text: Subheadline text
        zone: Layout zone
        y_offset: Vertical offset
        color: Text color
        font_size_ratio: Font size ratio
        
    Returns:
        Tuple of (canvas, height_used)
    """
    draw = ImageDraw.Draw(canvas)
    
    x1, y1, x2, y2 = zone.get_bounds(canvas.width, canvas.height)
    zone_width = x2 - x1
    
    font_size = int(canvas.height * font_size_ratio)
    font = load_font("semibold", font_size)
    
    height = render_text_block(
        draw,
        text,
        (x1, y1 + y_offset),
        font,
        color,
        zone_width,
        shadow=True,
    )
    
    return canvas, height


def render_disclaimer(
    canvas: Image.Image,
    text: str,
    position: tuple[int, int] = None,
    color: str = "#999999",
    font_size: int = 12,
) -> Image.Image:
    """
    Render legal disclaimer text (small, at bottom).
    
    Args:
        canvas: Canvas to draw on
        text: Disclaimer text
        position: (x, y) position (default: bottom-center)
        color: Text color
        font_size: Font size in pixels
        
    Returns:
        Canvas with disclaimer
    """
    draw = ImageDraw.Draw(canvas)
    font = load_font("regular", font_size)
    
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    if position is None:
        # Bottom center with padding
        x = (canvas.width - text_width) // 2
        y = canvas.height - text_height - 10
        position = (x, y)
    
    draw.text(position, text, font=font, fill=color)
    
    return canvas
