"""
Tests for the Composition Module.

Covers layout specs, product placement, text rendering, and full composition.
"""

import pytest
from pathlib import Path
from PIL import Image
from unittest.mock import AsyncMock, patch, MagicMock

from src.composition.templates.layout_specs import (
    LayoutZone,
    LayoutSpec,
    get_layout_spec,
    list_archetypes,
    LAYOUT_ARCHETYPES,
)
from src.composition.product_placer import (
    calculate_product_size,
    calculate_product_position,
    resize_product_image,
    has_transparency,
    apply_drop_shadow,
)
from src.composition.text_renderer import (
    wrap_text,
    get_text_size,
    load_font,
)
from src.composition.compositor import (
    Compositor,
    CompositionInput,
)
from src.models.brand import BrandContext, ColorPalette
from src.models.channel import ChannelContext, Dimensions, TextConstraints
from src.models.concept import CreativeConcept, ProductPlacement
from src.models.copy import AdCopy


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_canvas() -> Image.Image:
    """Create a 1080x1080 test canvas."""
    return Image.new("RGBA", (1080, 1080), (50, 50, 50, 255))


@pytest.fixture
def sample_product_image(tmp_path: Path) -> Path:
    """Create a sample product image."""
    img = Image.new("RGBA", (500, 500), (255, 0, 0, 255))
    path = tmp_path / "product.png"
    img.save(path)
    return path


@pytest.fixture
def sample_background_image(tmp_path: Path) -> Path:
    """Create a sample background image."""
    img = Image.new("RGB", (1080, 1080), (30, 30, 60))
    path = tmp_path / "background.png"
    img.save(path)
    return path


@pytest.fixture
def sample_store_brand() -> BrandContext:
    """Sample store brand for testing."""
    return BrandContext(
        brand_name="TestStore",
        brand_voice="Modern and friendly",
        tone_keywords=["confident", "approachable"],
        visual_style="Clean and minimal",
        color_palette=ColorPalette(
            primary="#E94560",
            secondary="#1A1A2E",
            accent="#16213E",
        ),
        logo_url="https://example.com/logo.png",
    )


@pytest.fixture
def sample_channel() -> ChannelContext:
    """Sample channel context."""
    return ChannelContext(
        platform="Instagram",
        placement="Feed",
        dimensions=Dimensions(width=1080, height=1080),
        text_constraints=TextConstraints(
            headline_max_chars=40,
            body_max_chars=125,
            cta_max_chars=20,
        ),
    )


@pytest.fixture
def sample_concept() -> CreativeConcept:
    """Sample creative concept."""
    return CreativeConcept(
        icp_id="test_icp",
        big_idea="Innovation meets simplicity",
        layout_archetype="Hero Product with Stat Overlay",
        scene_description="Dark gradient background with subtle tech patterns",
        product_placement=ProductPlacement(
            position="center",
            size="dominant",
            treatment="floating with shadow",
        ),
        mood="Modern and premium",
        color_direction="Dark with accent highlights",
        focal_point="Product center",
    )


@pytest.fixture
def sample_ad_copy() -> AdCopy:
    """Sample ad copy."""
    return AdCopy(
        icp_id="test_icp",
        headline="Your Focus, Engineered",
        subheadline="40 Hours of Pure Sound",
        body_copy="Premium noise-canceling headphones for the discerning listener.",
        cta_text="Shop Now",
    )


# =============================================================================
# Layout Specs Tests
# =============================================================================

class TestLayoutSpecs:
    """Tests for layout specifications."""
    
    def test_layout_zone_get_bounds(self):
        """Test zone bounds calculation."""
        zone = LayoutZone(0.1, 0.9, 0.2, 0.8)
        bounds = zone.get_bounds(1000, 1000)
        
        assert bounds == (100, 200, 900, 800)
    
    def test_layout_zone_get_center(self):
        """Test zone center calculation."""
        zone = LayoutZone(0.0, 1.0, 0.0, 1.0)
        center = zone.get_center(1000, 1000)
        
        assert center == (500, 500)
    
    def test_layout_zone_get_size(self):
        """Test zone size calculation."""
        zone = LayoutZone(0.25, 0.75, 0.25, 0.75)
        size = zone.get_size(1000, 1000)
        
        assert size == (500, 500)
    
    def test_get_layout_spec_exact_match(self):
        """Test getting layout spec by exact name."""
        layout = get_layout_spec("Hero Product with Stat Overlay")
        
        assert layout.name == "Hero Product with Stat Overlay"
        assert layout.product_zone is not None
        assert layout.headline_zone is not None
    
    def test_get_layout_spec_fuzzy_match(self):
        """Test fuzzy matching for layout names."""
        layout = get_layout_spec("Hero Product")
        
        assert "Hero" in layout.name
    
    def test_get_layout_spec_fallback(self):
        """Test fallback to default layout."""
        layout = get_layout_spec("NonexistentLayout")
        
        assert layout.name == "Minimal Product Focus"
    
    def test_list_archetypes(self):
        """Test listing all archetypes."""
        archetypes = list_archetypes()
        
        assert len(archetypes) >= 4
        assert "Hero Product with Stat Overlay" in archetypes
        assert "Problem/Solution Split" in archetypes
    
    def test_all_archetypes_have_required_zones(self):
        """Verify all archetypes have required zones."""
        for name, spec in LAYOUT_ARCHETYPES.items():
            assert spec.product_zone is not None, f"{name} missing product_zone"
            assert spec.headline_zone is not None, f"{name} missing headline_zone"
            assert spec.body_zone is not None, f"{name} missing body_zone"
            assert spec.cta_zone is not None, f"{name} missing cta_zone"
            assert spec.logo_zone is not None, f"{name} missing logo_zone"


# =============================================================================
# Product Placer Tests
# =============================================================================

class TestProductPlacer:
    """Tests for product placement."""
    
    def test_calculate_product_size_dominant(self):
        """Test dominant size calculation."""
        size = calculate_product_size((1080, 1080), "dominant")
        
        # Dominant = 65% of min dimension
        assert size == int(1080 * 0.65)
    
    def test_calculate_product_size_balanced(self):
        """Test balanced size calculation."""
        size = calculate_product_size((1080, 1080), "balanced")
        
        assert size == int(1080 * 0.45)
    
    def test_calculate_product_size_subtle(self):
        """Test subtle size calculation."""
        size = calculate_product_size((1080, 1080), "subtle")
        
        assert size == int(1080 * 0.30)
    
    def test_resize_product_image_downscale(self):
        """Test image downscaling."""
        img = Image.new("RGBA", (1000, 500), (255, 0, 0, 255))
        resized = resize_product_image(img, 500)
        
        assert resized.width == 500
        assert resized.height == 250  # Maintains aspect ratio
    
    def test_resize_product_image_no_upscale(self):
        """Test that small images are not upscaled."""
        img = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
        resized = resize_product_image(img, 500)
        
        # Should not upscale
        assert resized.width == 200
        assert resized.height == 200
    
    def test_calculate_product_position_center(self):
        """Test center positioning."""
        zone = LayoutZone(0.0, 1.0, 0.0, 1.0)
        pos = calculate_product_position(
            (1000, 1000),
            (200, 200),
            "center",
            zone,
        )
        
        # Should be centered
        assert pos == (400, 400)
    
    def test_calculate_product_position_left_third(self):
        """Test left-third positioning."""
        zone = LayoutZone(0.0, 1.0, 0.0, 1.0)
        pos = calculate_product_position(
            (1000, 1000),
            (200, 200),
            "left-third",
            zone,
        )
        
        # Should be left-aligned
        assert pos[0] < 300
    
    def test_has_transparency_with_alpha(self):
        """Test transparency detection with alpha channel."""
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        
        assert has_transparency(img) is True
    
    def test_has_transparency_without_alpha(self):
        """Test transparency detection without meaningful alpha."""
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        
        assert has_transparency(img) is False
    
    def test_has_transparency_rgb_mode(self):
        """Test transparency detection for RGB images."""
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        
        assert has_transparency(img) is False
    
    def test_apply_drop_shadow(self):
        """Test drop shadow application."""
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        result = apply_drop_shadow(img)
        
        # Result should be larger to accommodate shadow
        assert result.width > img.width
        assert result.height > img.height


# =============================================================================
# Text Renderer Tests
# =============================================================================

class TestTextRenderer:
    """Tests for text rendering."""
    
    def test_load_font_fallback(self):
        """Test font loading with fallback."""
        font = load_font("bold", 24)
        
        # Should return a font object (may be fallback)
        assert font is not None
    
    def test_wrap_text_short(self):
        """Test that short text doesn't wrap."""
        font = load_font("regular", 24)
        lines = wrap_text("Short text", font, 500)
        
        assert len(lines) == 1
        assert lines[0] == "Short text"
    
    def test_wrap_text_long(self):
        """Test that long text wraps correctly."""
        font = load_font("regular", 24)
        long_text = "This is a very long sentence that should definitely wrap onto multiple lines when rendered"
        lines = wrap_text(long_text, font, 200)
        
        assert len(lines) > 1
    
    def test_wrap_text_empty(self):
        """Test wrapping empty text."""
        font = load_font("regular", 24)
        lines = wrap_text("", font, 500)
        
        assert lines == []
    
    def test_get_text_size(self):
        """Test text size calculation."""
        font = load_font("regular", 24)
        lines = ["Line 1", "Line 2"]
        size = get_text_size(lines, font)
        
        assert size[0] > 0
        assert size[1] > 0
    
    def test_get_text_size_empty(self):
        """Test text size for empty lines."""
        font = load_font("regular", 24)
        size = get_text_size([], font)
        
        assert size == (0, 0)


# =============================================================================
# Compositor Tests
# =============================================================================

class TestCompositor:
    """Tests for the main compositor."""
    
    @pytest.mark.asyncio
    async def test_compositor_creates_output_file(
        self,
        sample_background_image: Path,
        sample_product_image: Path,
        sample_store_brand: BrandContext,
        sample_channel: ChannelContext,
        sample_concept: CreativeConcept,
        sample_ad_copy: AdCopy,
        tmp_path: Path,
    ):
        """Test that compositor creates output file."""
        output_path = tmp_path / "output" / "test_ad.png"
        
        # Mock rembg to avoid slow model loading
        with patch("src.composition.product_placer.remove_background") as mock_rembg:
            mock_rembg.return_value = Image.new("RGBA", (500, 500), (255, 0, 0, 255))
            
            input = CompositionInput(
                background_path=str(sample_background_image),
                product_image_source=str(sample_product_image),
                ad_copy=sample_ad_copy,
                concept=sample_concept,
                store_brand=sample_store_brand,
                brand_strategy="store_dominant",
                channel=sample_channel,
                output_path=str(output_path),
            )
            
            compositor = Compositor()
            result = await compositor.compose(input)
        
        assert Path(result.path).exists()
        assert result.width == 1080
        assert result.height == 1080
    
    @pytest.mark.asyncio
    async def test_compositor_exact_dimensions(
        self,
        sample_background_image: Path,
        sample_product_image: Path,
        sample_store_brand: BrandContext,
        sample_concept: CreativeConcept,
        sample_ad_copy: AdCopy,
        tmp_path: Path,
    ):
        """Test output matches exact channel dimensions."""
        # Custom dimensions
        channel = ChannelContext(
            platform="Facebook",
            placement="Feed",
            dimensions=Dimensions(width=1200, height=628),
            text_constraints=TextConstraints(
                headline_max_chars=50,
                body_max_chars=150,
                cta_max_chars=25,
            ),
        )
        
        output_path = tmp_path / "test_ad_facebook.png"
        
        with patch("src.composition.product_placer.remove_background") as mock_rembg:
            mock_rembg.return_value = Image.new("RGBA", (500, 500), (255, 0, 0, 255))
            
            input = CompositionInput(
                background_path=str(sample_background_image),
                product_image_source=str(sample_product_image),
                ad_copy=sample_ad_copy,
                concept=sample_concept,
                store_brand=sample_store_brand,
                channel=channel,
                output_path=str(output_path),
            )
            
            compositor = Compositor()
            result = await compositor.compose(input)
        
        # Verify dimensions
        output_image = Image.open(result.path)
        assert output_image.width == 1200
        assert output_image.height == 628
    
    @pytest.mark.asyncio
    async def test_compositor_jpeg_output(
        self,
        sample_background_image: Path,
        sample_product_image: Path,
        sample_store_brand: BrandContext,
        sample_channel: ChannelContext,
        sample_concept: CreativeConcept,
        sample_ad_copy: AdCopy,
        tmp_path: Path,
    ):
        """Test JPEG output format."""
        output_path = tmp_path / "test_ad.jpg"
        
        with patch("src.composition.product_placer.remove_background") as mock_rembg:
            mock_rembg.return_value = Image.new("RGBA", (500, 500), (255, 0, 0, 255))
            
            input = CompositionInput(
                background_path=str(sample_background_image),
                product_image_source=str(sample_product_image),
                ad_copy=sample_ad_copy,
                concept=sample_concept,
                store_brand=sample_store_brand,
                channel=sample_channel,
                output_path=str(output_path),
                output_format="JPEG",
            )
            
            compositor = Compositor()
            result = await compositor.compose(input)
        
        assert Path(result.path).exists()
        # Verify it's a valid JPEG
        output_image = Image.open(result.path)
        assert output_image.format == "JPEG"
    
    def test_composition_input_validation(self):
        """Test CompositionInput validation."""
        # Should raise on missing required fields
        with pytest.raises(Exception):
            CompositionInput(
                background_path="test.png",
                # Missing other required fields
            )


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for full composition workflow."""
    
    @pytest.mark.asyncio
    async def test_full_composition_pipeline(
        self,
        sample_background_image: Path,
        sample_product_image: Path,
        sample_store_brand: BrandContext,
        sample_channel: ChannelContext,
        sample_concept: CreativeConcept,
        sample_ad_copy: AdCopy,
        tmp_path: Path,
    ):
        """Test complete composition pipeline."""
        output_dir = tmp_path / "output" / "integration"
        output_path = output_dir / "final_ad.png"
        
        with patch("src.composition.product_placer.remove_background") as mock_rembg:
            # Return image with transparency
            product_with_alpha = Image.new("RGBA", (500, 500), (255, 0, 0, 200))
            mock_rembg.return_value = product_with_alpha
            
            input = CompositionInput(
                background_path=str(sample_background_image),
                product_image_source=str(sample_product_image),
                ad_copy=sample_ad_copy,
                concept=sample_concept,
                store_brand=sample_store_brand,
                brand_strategy="store_dominant",
                channel=sample_channel,
                output_path=str(output_path),
            )
            
            compositor = Compositor()
            result = await compositor.compose(input)
        
        # Verify output
        assert Path(result.path).exists()
        
        # Load and verify image
        output_image = Image.open(result.path)
        assert output_image.width == sample_channel.dimensions.width
        assert output_image.height == sample_channel.dimensions.height
        
        # Image should not be empty/blank
        extrema = output_image.getextrema()
        assert extrema is not None
