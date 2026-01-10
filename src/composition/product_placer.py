"""
Product image placement for ad composition.

Handles loading, background removal, sizing, and positioning of product images.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Literal

from PIL import Image, ImageFilter

from src.composition.templates.layout_specs import LayoutZone
from src.models.concept import ProductPlacement

logger = logging.getLogger(__name__)

# Size multipliers relative to min(canvas_width, canvas_height)
SIZE_MULTIPLIERS: dict[str, float] = {
    "dominant": 0.65,
    "balanced": 0.45,
    "subtle": 0.30,
}


async def load_product_image(source: str) -> Image.Image:
    """
    Load product image from URL or local path.
    
    Args:
        source: HTTP(S) URL or local file path
        
    Returns:
        PIL Image in RGBA mode
        
    Raises:
        FileNotFoundError: If local file doesn't exist
        httpx.HTTPError: If URL fetch fails
    """
    if source.startswith(("http://", "https://")):
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(source, timeout=30.0)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Product image not found: {source}")
        image = Image.open(path)
    
    # Convert to RGBA for transparency support
    return image.convert("RGBA")


def remove_background(image: Image.Image) -> Image.Image:
    """
    Remove background from product image using rembg.
    
    Args:
        image: PIL Image (any mode)
        
    Returns:
        PIL Image in RGBA mode with transparent background
    """
    from rembg import remove
    
    logger.info("Removing background from product image...")
    
    # rembg works directly with PIL images
    result = remove(image)
    
    # Ensure RGBA
    return result.convert("RGBA")


def has_transparency(image: Image.Image) -> bool:
    """Check if image has meaningful transparency."""
    if image.mode != "RGBA":
        return False
    
    # Check alpha channel
    alpha = image.split()[-1]
    extrema = alpha.getextrema()
    
    # If min alpha < 255, there's some transparency
    return extrema[0] < 250


def calculate_product_size(
    canvas_size: tuple[int, int],
    size_directive: Literal["dominant", "balanced", "subtle"],
) -> int:
    """
    Calculate target product size (max dimension).
    
    Args:
        canvas_size: (width, height) of canvas
        size_directive: Size category from ProductPlacement
        
    Returns:
        Target size in pixels (for the largest dimension)
    """
    multiplier = SIZE_MULTIPLIERS.get(size_directive, SIZE_MULTIPLIERS["balanced"])
    base_size = min(canvas_size)
    return int(base_size * multiplier)


def resize_product_image(
    image: Image.Image,
    target_max_size: int,
) -> Image.Image:
    """
    Resize product image maintaining aspect ratio.
    
    Args:
        image: PIL Image to resize
        target_max_size: Maximum dimension (width or height)
        
    Returns:
        Resized PIL Image
    """
    # Calculate scale to fit within target size
    width, height = image.size
    max_dim = max(width, height)
    
    if max_dim <= target_max_size:
        return image  # No resize needed
    
    scale = target_max_size / max_dim
    new_size = (int(width * scale), int(height * scale))
    
    return image.resize(new_size, Image.Resampling.LANCZOS)


def calculate_product_position(
    canvas_size: tuple[int, int],
    product_size: tuple[int, int],
    position_directive: str,
    zone: LayoutZone,
) -> tuple[int, int]:
    """
    Calculate top-left position for product placement.
    
    Args:
        canvas_size: (width, height) of canvas
        product_size: (width, height) of product image
        position_directive: Position string (e.g., 'center', 'left-third')
        zone: Layout zone to place product within
        
    Returns:
        (x, y) top-left position for product
    """
    canvas_w, canvas_h = canvas_size
    prod_w, prod_h = product_size
    
    # Get zone bounds
    zone_x1, zone_y1, zone_x2, zone_y2 = zone.get_bounds(canvas_w, canvas_h)
    zone_w = zone_x2 - zone_x1
    zone_h = zone_y2 - zone_y1
    
    # Parse position directive
    position = position_directive.lower().replace("-", "_").replace(" ", "_")
    
    # Calculate center position within zone
    zone_center_x = zone_x1 + zone_w // 2
    zone_center_y = zone_y1 + zone_h // 2
    
    if "center" in position and "bottom" not in position and "top" not in position:
        # Pure center
        x = zone_center_x - prod_w // 2
        y = zone_center_y - prod_h // 2
    elif "left" in position:
        # Left-aligned within zone
        x = zone_x1 + int(zone_w * 0.15)
        y = zone_center_y - prod_h // 2
    elif "right" in position:
        # Right-aligned within zone
        x = zone_x2 - prod_w - int(zone_w * 0.1)
        y = zone_center_y - prod_h // 2
    elif "bottom" in position:
        x = zone_center_x - prod_w // 2
        y = zone_y2 - prod_h - int(zone_h * 0.1)
        if "right" in position:
            x = zone_x2 - prod_w - int(zone_w * 0.1)
        elif "left" in position:
            x = zone_x1 + int(zone_w * 0.1)
    elif "top" in position:
        x = zone_center_x - prod_w // 2
        y = zone_y1 + int(zone_h * 0.1)
    else:
        # Default: center in zone
        x = zone_center_x - prod_w // 2
        y = zone_center_y - prod_h // 2
    
    # Clamp to canvas bounds
    x = max(0, min(x, canvas_w - prod_w))
    y = max(0, min(y, canvas_h - prod_h))
    
    return (x, y)


def apply_drop_shadow(
    image: Image.Image,
    offset: tuple[int, int] = (8, 8),
    blur_radius: int = 15,
    shadow_color: tuple[int, int, int, int] = (0, 0, 0, 100),
) -> Image.Image:
    """
    Apply drop shadow effect to image.
    
    Args:
        image: RGBA image to add shadow to
        offset: (x, y) shadow offset
        blur_radius: Gaussian blur radius
        shadow_color: RGBA shadow color
        
    Returns:
        New RGBA image with shadow (larger canvas to fit shadow)
    """
    # Calculate new canvas size to fit shadow
    shadow_extend = blur_radius * 2 + max(abs(offset[0]), abs(offset[1]))
    new_width = image.width + shadow_extend * 2
    new_height = image.height + shadow_extend * 2
    
    # Create shadow layer
    shadow = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    
    # Create shadow shape from alpha channel
    if image.mode == "RGBA":
        alpha = image.split()[-1]
        shadow_shape = Image.new("RGBA", image.size, shadow_color)
        shadow_shape.putalpha(alpha)
    else:
        shadow_shape = Image.new("RGBA", image.size, shadow_color)
    
    # Paste shadow at offset position
    shadow_x = shadow_extend + offset[0]
    shadow_y = shadow_extend + offset[1]
    shadow.paste(shadow_shape, (shadow_x, shadow_y))
    
    # Blur the shadow
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # Paste original image on top
    img_x = shadow_extend
    img_y = shadow_extend
    shadow.paste(image, (img_x, img_y), image if image.mode == "RGBA" else None)
    
    return shadow


def apply_product_treatment(
    image: Image.Image,
    treatment: str,
) -> Image.Image:
    """
    Apply visual effects based on treatment directive.
    
    Args:
        image: Product image (RGBA)
        treatment: Treatment description from CreativeConcept
        
    Returns:
        Processed image with effects applied
    """
    treatment_lower = treatment.lower()
    
    if "shadow" in treatment_lower or "floating" in treatment_lower:
        return apply_drop_shadow(image)
    
    if "reflection" in treatment_lower or "surface" in treatment_lower:
        # Simple reflection: flip vertically, fade, composite below
        reflection = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        # Create fade gradient for reflection
        gradient = Image.linear_gradient("L").rotate(180)
        gradient = gradient.resize(reflection.size)
        # Apply fade to alpha
        if reflection.mode == "RGBA":
            r, g, b, a = reflection.split()
            a = Image.blend(a, gradient.convert("L"), 0.7)
            reflection = Image.merge("RGBA", (r, g, b, a))
        
        # Create canvas for product + reflection
        total_height = int(image.height * 1.4)
        result = Image.new("RGBA", (image.width, total_height), (0, 0, 0, 0))
        result.paste(image, (0, 0), image if image.mode == "RGBA" else None)
        # Paste faded reflection below (cropped to 40% height)
        reflection_height = int(image.height * 0.4)
        reflection_cropped = reflection.crop((0, 0, reflection.width, reflection_height))
        result.paste(
            reflection_cropped, 
            (0, image.height), 
            reflection_cropped if reflection_cropped.mode == "RGBA" else None
        )
        return result
    
    # No treatment or unrecognized: add subtle shadow by default
    return apply_drop_shadow(image, offset=(5, 5), blur_radius=10, shadow_color=(0, 0, 0, 60))


async def place_product(
    canvas: Image.Image,
    product_source: str,
    placement: ProductPlacement,
    zone: LayoutZone,
    remove_bg: bool = True,
) -> Image.Image:
    """
    Full product placement pipeline.
    
    Args:
        canvas: Background canvas to place product on
        product_source: URL or path to product image
        placement: ProductPlacement with position, size, treatment
        zone: LayoutZone defining where product can be placed
        remove_bg: Whether to remove background (default True)
        
    Returns:
        Canvas with product composited
    """
    # Load product image
    product = await load_product_image(product_source)
    logger.info(f"Loaded product image: {product.size}")
    
    # Remove background if needed
    if remove_bg and not has_transparency(product):
        product = remove_background(product)
        logger.info("Background removed from product image")
    
    # Calculate target size
    target_size = calculate_product_size(canvas.size, placement.size)
    product = resize_product_image(product, target_size)
    logger.info(f"Resized product to: {product.size}")
    
    # Apply treatment (shadow, reflection, etc.)
    product = apply_product_treatment(product, placement.treatment)
    logger.info(f"Applied treatment: {placement.treatment}")
    
    # Calculate position
    position = calculate_product_position(
        canvas.size,
        product.size,
        placement.position,
        zone,
    )
    logger.info(f"Product position: {position}")
    
    # Composite onto canvas
    result = canvas.copy()
    result.paste(product, position, product if product.mode == "RGBA" else None)
    
    return result
