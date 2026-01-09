"""
Image utilities for Sartor Ad Engine.

Provides functions for loading, validating, and processing images.
"""

from io import BytesIO
from pathlib import Path

from PIL import Image


def load_image_from_path(path: str | Path) -> Image.Image:
    """
    Load an image from a local file path.
    
    Args:
        path: Path to the image file
    
    Returns:
        PIL Image object
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        PIL.UnidentifiedImageError: If the file isn't a valid image
    """
    return Image.open(path)


async def load_image_from_url(url: str) -> Image.Image:
    """
    Load an image from a URL.
    
    Args:
        url: HTTP(S) URL of the image
    
    Returns:
        PIL Image object
    
    Raises:
        httpx.HTTPError: If the request fails
        PIL.UnidentifiedImageError: If the response isn't a valid image
    """
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))


def validate_image_dimensions(
    image: Image.Image,
    expected_width: int,
    expected_height: int,
) -> bool:
    """
    Check if an image matches expected dimensions.
    
    Args:
        image: PIL Image to validate
        expected_width: Required width in pixels
        expected_height: Required height in pixels
    
    Returns:
        True if dimensions match, False otherwise
    """
    return image.width == expected_width and image.height == expected_height


def resize_image(
    image: Image.Image,
    width: int,
    height: int,
    resample: int = Image.Resampling.LANCZOS,
) -> Image.Image:
    """
    Resize an image to exact dimensions.
    
    Args:
        image: PIL Image to resize
        width: Target width
        height: Target height
        resample: Resampling filter (default: LANCZOS for quality)
    
    Returns:
        Resized PIL Image
    """
    return image.resize((width, height), resample=resample)


def save_image(
    image: Image.Image,
    path: str | Path,
    format: str | None = None,
    quality: int = 95,
) -> Path:
    """
    Save an image to disk.
    
    Args:
        image: PIL Image to save
        path: Destination path
        format: Image format (auto-detected from extension if None)
        quality: JPEG quality (1-100)
    
    Returns:
        Path to saved image
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    save_kwargs = {}
    if format or path.suffix.lower() in [".jpg", ".jpeg"]:
        save_kwargs["quality"] = quality
    
    image.save(path, format=format, **save_kwargs)
    return path
