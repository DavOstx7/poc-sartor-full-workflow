"""
Main compositor for ad composition.

Orchestrates the full composition pipeline: background + product + text + logo → final ad.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw
from pydantic import BaseModel, Field

from src.composition.product_placer import place_product, load_product_image
from src.composition.templates.layout_specs import get_layout_spec, LayoutZone
from src.composition.text_renderer import (
    render_headline,
    render_subheadline,
    render_body,
    render_cta_button,
    render_disclaimer,
    load_font,
)
from src.models.assets import ImageAsset
from src.models.brand import BrandContext, BrandStrategyType
from src.models.channel import ChannelContext
from src.models.concept import CreativeConcept
from src.models.copy import AdCopy

logger = logging.getLogger(__name__)


class CompositionInput(BaseModel):
    """Validated input for ad composition."""
    
    background_path: str = Field(..., description="Path to background scene image")
    product_image_source: str = Field(..., description="URL or path to product image")
    ad_copy: AdCopy
    concept: CreativeConcept
    store_brand: BrandContext
    product_brand: BrandContext | None = None
    brand_strategy: BrandStrategyType = "store_dominant"
    channel: ChannelContext
    output_path: str = Field(..., description="Where to save final ad")
    output_format: Literal["PNG", "JPEG"] = "PNG"
    remove_product_bg: bool = True


class Compositor:
    """
    Deterministic ad composition engine.
    
    Combines background scene, product image, text, and logos
    to produce final static ad creatives.
    """
    
    def __init__(self):
        """Initialize compositor."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def compose(self, input: CompositionInput) -> ImageAsset:
        """
        Execute full composition pipeline.
        
        Pipeline:
        1. Load and resize background to channel dimensions
        2. Place product image (with optional bg removal)
        3. Render text (headline, subheadline, body, CTA)
        4. Add logo(s) based on brand strategy
        5. Add legal disclaimer if present
        6. Export final image
        
        Args:
            input: Validated composition input
            
        Returns:
            ImageAsset with path to final ad
        """
        self.logger.info(f"Starting composition for ICP: {input.ad_copy.icp_id}")
        
        # Get layout specification
        layout = get_layout_spec(input.concept.layout_archetype)
        self.logger.info(f"Using layout: {layout.name}")
        
        # Step 1: Load and resize background
        canvas = self._load_background(
            input.background_path,
            input.channel.dimensions.width,
            input.channel.dimensions.height,
        )
        self.logger.info(f"Background loaded: {canvas.size}")
        
        # Step 2: Place product
        canvas = await place_product(
            canvas,
            input.product_image_source,
            input.concept.product_placement,
            layout.product_zone,
            remove_bg=input.remove_product_bg,
        )
        self.logger.info("Product placed")
        
        # Step 3: Render text
        canvas = self._render_all_text(canvas, input, layout)
        self.logger.info("Text rendered")
        
        # Step 4: Add logos
        canvas = await self._render_logos(canvas, input, layout)
        self.logger.info("Logos added")
        
        # Step 5: Add legal disclaimer
        if input.ad_copy.legal_disclaimer:
            canvas = render_disclaimer(canvas, input.ad_copy.legal_disclaimer)
            self.logger.info("Disclaimer added")
        
        # Step 6: Export
        output_path = self._save_image(canvas, input.output_path, input.output_format)
        self.logger.info(f"Saved to: {output_path}")
        
        return ImageAsset(
            path=str(output_path),
            width=canvas.width,
            height=canvas.height,
        )
    
    def _load_background(
        self,
        path: str,
        target_width: int,
        target_height: int,
    ) -> Image.Image:
        """Load background and resize to exact dimensions."""
        bg = Image.open(path)
        
        # Convert to RGB (no transparency for background)
        if bg.mode != "RGB":
            bg = bg.convert("RGB")
        
        # Resize to exact dimensions (may distort slightly)
        if bg.size != (target_width, target_height):
            bg = bg.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Convert to RGBA for compositing
        return bg.convert("RGBA")
    
    def _get_dominant_brand(self, input: CompositionInput) -> BrandContext:
        """Get the dominant brand based on strategy."""
        if input.brand_strategy == "product_dominant" and input.product_brand:
            return input.product_brand
        return input.store_brand
    
    def _render_all_text(
        self,
        canvas: Image.Image,
        input: CompositionInput,
        layout,
    ) -> Image.Image:
        """Render all text elements."""
        dominant_brand = self._get_dominant_brand(input)
        
        # Get brand colors
        primary_color = dominant_brand.color_palette.primary
        accent_color = dominant_brand.color_palette.accent or primary_color
        
        # Determine text color based on background
        text_color = self._get_contrasting_text_color(primary_color)
        
        current_y_offset = 0
        
        # Headline
        canvas, headline_height = render_headline(
            canvas,
            input.ad_copy.headline,
            layout.headline_zone,
            primary_color,
            font_size_ratio=layout.headline_font_ratio,
        )
        current_y_offset = headline_height + 20  # Add spacing
        
        # Subheadline (if present)
        if input.ad_copy.subheadline:
            canvas, subheadline_height = render_subheadline(
                canvas,
                input.ad_copy.subheadline,
                layout.headline_zone,
                y_offset=current_y_offset,
            )
            current_y_offset += subheadline_height + 15
        
        # Body copy
        if input.ad_copy.body_copy:
            canvas, body_height = render_body(
                canvas,
                input.ad_copy.body_copy,
                layout.body_zone,
                color="#FFFFFF",
                font_size_ratio=layout.body_font_ratio,
            )
        
        # CTA button
        canvas = render_cta_button(
            canvas,
            input.ad_copy.cta_text,
            layout.cta_zone,
            accent_color,
            font_size_ratio=layout.cta_font_ratio,
        )
        
        # CTA urgency (if present)
        if input.ad_copy.cta_urgency:
            draw = ImageDraw.Draw(canvas)
            font = load_font("regular", int(canvas.height * 0.018))
            x1, y1, x2, y2 = layout.cta_zone.get_bounds(canvas.width, canvas.height)
            # Place urgency text below CTA
            urgency_y = y2 + 10
            draw.text(
                (x1, urgency_y),
                input.ad_copy.cta_urgency,
                font=font,
                fill="#FFCC00",  # Warning/urgency color
            )
        
        return canvas
    
    async def _render_logos(
        self,
        canvas: Image.Image,
        input: CompositionInput,
        layout,
    ) -> Image.Image:
        """
        Render logos based on brand strategy.
        
        - store_dominant: Store logo in logo_zone
        - product_dominant: Product logo + "Available at [Store]"
        - co_branded: Both logos
        """
        logo_zone = layout.logo_zone
        x1, y1, x2, y2 = logo_zone.get_bounds(canvas.width, canvas.height)
        zone_width = x2 - x1
        zone_height = y2 - y1
        
        if input.brand_strategy == "store_dominant":
            # Store logo only
            canvas = await self._place_logo(
                canvas, 
                input.store_brand.logo_url,
                (x1, y1),
                max_height=zone_height,
                brand_name=input.store_brand.brand_name,
            )
        
        elif input.brand_strategy == "product_dominant" and input.product_brand:
            # Product logo prominent
            canvas = await self._place_logo(
                canvas,
                input.product_brand.logo_url,
                (x1, y1),
                max_height=zone_height,
                brand_name=input.product_brand.brand_name,
            )
            
            # "Available at [Store]" text at bottom
            draw = ImageDraw.Draw(canvas)
            font = load_font("regular", int(canvas.height * 0.018))
            available_text = f"Available at {input.store_brand.brand_name}"
            draw.text(
                (10, canvas.height - 30),
                available_text,
                font=font,
                fill="#CCCCCC",
            )
        
        elif input.brand_strategy == "co_branded":
            # Both logos side by side
            half_width = zone_width // 2
            
            # Store logo on left
            canvas = await self._place_logo(
                canvas,
                input.store_brand.logo_url,
                (x1, y1),
                max_width=half_width - 10,
                max_height=zone_height,
                brand_name=input.store_brand.brand_name,
            )
            
            # Product logo on right (if exists)
            if input.product_brand:
                canvas = await self._place_logo(
                    canvas,
                    input.product_brand.logo_url,
                    (x1 + half_width + 10, y1),
                    max_width=half_width - 10,
                    max_height=zone_height,
                    brand_name=input.product_brand.brand_name,
                )
        
        return canvas
    
    async def _place_logo(
        self,
        canvas: Image.Image,
        logo_source: str | None,
        position: tuple[int, int],
        max_width: int = None,
        max_height: int = None,
        brand_name: str = None,
    ) -> Image.Image:
        """Load and place a logo on the canvas. Falls back to text-based logo if loading fails."""
        if not logo_source:
            if brand_name:
                return self._render_text_logo(canvas, brand_name, position, max_height)
            return canvas
            
        try:
            # Skip known placeholder URLs
            if "example.com" in logo_source or "placeholder" in logo_source.lower():
                self.logger.debug(f"Skipping placeholder logo URL: {logo_source}")
                if brand_name:
                    return self._render_text_logo(canvas, brand_name, position, max_height)
                return canvas
            
            # Load logo
            if logo_source.startswith(("http://", "https://")):
                logo = await load_product_image(logo_source)
            else:
                logo = Image.open(logo_source).convert("RGBA")
            
            # Resize to fit constraints
            if max_width or max_height:
                logo = self._resize_to_fit(logo, max_width, max_height)
            
            # Composite onto canvas
            canvas.paste(logo, position, logo if logo.mode == "RGBA" else None)
            
        except Exception as e:
            self.logger.warning(f"Failed to load logo from {logo_source}: {e}")
            # Fallback to text-based logo
            if brand_name:
                return self._render_text_logo(canvas, brand_name, position, max_height)
        
        return canvas
    
    def _render_text_logo(
        self,
        canvas: Image.Image,
        brand_name: str,
        position: tuple[int, int],
        max_height: int = None,
    ) -> Image.Image:
        """Render brand name as a text-based logo fallback."""
        draw = ImageDraw.Draw(canvas)
        font_size = min(max_height or 30, 30)
        font = load_font("bold", font_size)
        draw.text(position, brand_name, font=font, fill="#FFFFFF")
        return canvas
    
    def _resize_to_fit(
        self,
        image: Image.Image,
        max_width: int = None,
        max_height: int = None,
    ) -> Image.Image:
        """Resize image to fit within max dimensions, maintaining aspect ratio."""
        width, height = image.size
        
        scale = 1.0
        if max_width and width > max_width:
            scale = min(scale, max_width / width)
        if max_height and height > max_height:
            scale = min(scale, max_height / height)
        
        if scale < 1.0:
            new_size = (int(width * scale), int(height * scale))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def _get_contrasting_text_color(self, background_color: str) -> str:
        """Get a text color that contrasts with the background."""
        # Simple luminance check
        try:
            # Remove # and parse hex
            hex_color = background_color.lstrip("#")
            r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#000000" if luminance > 0.5 else "#FFFFFF"
        except Exception:
            return "#FFFFFF"
    
    def _save_image(
        self,
        image: Image.Image,
        path: str,
        format: str,
    ) -> Path:
        """Save image to disk."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to RGB for JPEG
        if format == "JPEG" and image.mode == "RGBA":
            # Composite onto white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        save_kwargs = {}
        if format == "JPEG":
            save_kwargs["quality"] = 95
        
        image.save(output_path, format=format, **save_kwargs)
        return output_path


# Convenience function for simple composition
async def compose_ad(
    background_path: str,
    product_image_source: str,
    ad_copy: AdCopy,
    concept: CreativeConcept,
    store_brand: BrandContext,
    channel: ChannelContext,
    output_path: str,
    product_brand: BrandContext | None = None,
    brand_strategy: BrandStrategyType = "store_dominant",
    output_format: Literal["PNG", "JPEG"] = "PNG",
) -> ImageAsset:
    """
    Convenience function to compose an ad.
    
    Args:
        background_path: Path to background scene
        product_image_source: URL or path to product image
        ad_copy: Copy content
        concept: Creative concept with placement directives
        store_brand: Store brand context
        channel: Channel with dimensions
        output_path: Where to save final ad
        product_brand: Optional product brand
        brand_strategy: Brand hierarchy strategy
        output_format: PNG or JPEG
        
    Returns:
        ImageAsset with path to final ad
    """
    input = CompositionInput(
        background_path=background_path,
        product_image_source=product_image_source,
        ad_copy=ad_copy,
        concept=concept,
        store_brand=store_brand,
        product_brand=product_brand,
        brand_strategy=brand_strategy,
        channel=channel,
        output_path=output_path,
        output_format=output_format,
    )
    
    compositor = Compositor()
    return await compositor.compose(input)
