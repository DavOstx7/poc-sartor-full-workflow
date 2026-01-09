"""
Tests for Pydantic models in Sartor Ad Engine.

Validates that all models correctly parse sample data and enforce constraints.
"""

import pytest

from src.models import (
    AdCopy,
    BrandContext,
    BrandStrategyType,
    ChannelContext,
    ColorPalette,
    CreativeConcept,
    Dimensions,
    ErrorLog,
    ICP,
    ImageAsset,
    Price,
    ProductData,
    ProductPlacement,
    StoreContext,
    StrategicBrief,
    TextConstraints,
)


class TestProductModels:
    """Tests for product-related models."""

    def test_price_model(self):
        """Price model validates correctly."""
        price = Price(value=349.00, currency="USD")
        assert price.value == 349.00
        assert price.currency == "USD"
        assert price.compare_at_price is None

    def test_price_with_discount(self):
        """Price model handles compare_at_price."""
        price = Price(value=399.00, currency="USD", compare_at_price=449.00)
        assert price.compare_at_price == 449.00

    def test_product_data_from_sample(self, dtc_sample_data):
        """ProductData model parses DTC sample correctly."""
        product = ProductData(**dtc_sample_data["product"])
        assert product.product_id == "SKU-AF-PRO-001"
        assert product.name == "AeroFlow Pro Wireless Headphones"
        assert len(product.features) >= 1
        assert product.price.value == 349.00


class TestBrandModels:
    """Tests for brand-related models."""

    def test_color_palette(self):
        """ColorPalette model validates hex codes."""
        palette = ColorPalette(primary="#1A1A2E", accent="#E94560")
        assert palette.primary == "#1A1A2E"
        assert palette.secondary is None

    def test_brand_context_from_sample(self, dtc_sample_data):
        """BrandContext model parses store brand correctly."""
        brand = BrandContext(**dtc_sample_data["store_brand"])
        assert brand.brand_name == "SoundScale"
        assert "confident" in brand.tone_keywords
        assert brand.tagline == "Sound, Perfected."

    def test_product_brand_from_multi_brand_sample(self, multi_brand_sample_data):
        """BrandContext model parses product brand correctly."""
        brand = BrandContext(**multi_brand_sample_data["product_brand"])
        assert brand.brand_name == "Sony"
        assert brand.tagline == "Be Moved."

    def test_brand_strategy_type(self):
        """BrandStrategyType literal type works correctly."""
        # Valid strategies
        strategy: BrandStrategyType = "store_dominant"
        assert strategy == "store_dominant"

        strategy = "product_dominant"
        assert strategy == "product_dominant"

        strategy = "co_branded"
        assert strategy == "co_branded"


class TestChannelModels:
    """Tests for channel-related models."""

    def test_dimensions(self):
        """Dimensions model validates positive integers."""
        dims = Dimensions(width=1080, height=1080)
        assert dims.width == 1080
        assert dims.height == 1080

    def test_text_constraints(self):
        """TextConstraints model validates correctly."""
        constraints = TextConstraints(
            headline_max_chars=40,
            body_max_chars=125,
            cta_max_chars=20,
        )
        assert constraints.headline_max_chars == 40

    def test_channel_context_from_sample(self, dtc_sample_data):
        """ChannelContext model parses sample correctly."""
        channel = ChannelContext(**dtc_sample_data["channel"])
        assert channel.platform == "Instagram"
        assert channel.placement == "Feed"
        assert channel.dimensions.width == 1080
        assert channel.text_constraints.headline_max_chars == 40


class TestStoreModels:
    """Tests for store context models."""

    def test_store_context_from_sample(self, dtc_sample_data):
        """StoreContext model parses sample correctly."""
        context = StoreContext(**dtc_sample_data["store_context"])
        assert context.price_positioning == "premium"
        assert "Bose" in context.competitors


class TestAgentOutputModels:
    """Tests for agent output models (ICP, Strategy, Concept, Copy)."""

    def test_icp_model(self):
        """ICP model validates complete profile."""
        icp = ICP(
            icp_id="icp-001",
            name="Tech-Forward Professional",
            demographic={
                "age_range": "25-34",
                "gender": None,
                "income_level": "Upper-middle",
                "location_type": "Urban",
            },
            psychographics={
                "values": ["efficiency", "quality"],
                "lifestyle": "Busy professional",
                "aspirations": "Work-life balance",
            },
            behavioral_triggers={
                "purchase_motivators": ["quality", "reviews"],
                "objections": ["price"],
                "decision_factors": ["features", "brand"],
            },
            communication_preferences={
                "tone": "Professional",
                "vocabulary_level": "Technical",
                "responds_to": ["data", "social proof"],
            },
        )
        assert icp.icp_id == "icp-001"
        assert icp.name == "Tech-Forward Professional"

    def test_strategic_brief_model(self):
        """StrategicBrief model validates correctly."""
        brief = StrategicBrief(
            icp_id="icp-001",
            positioning_statement="For busy professionals who need focus...",
            primary_pain_point="Distractions during remote work",
            key_benefit="Deep focus with premium noise cancellation",
            proof_point="40-hour battery life",
            emotional_appeal="Feeling of productivity and control",
            tone_of_voice="Confident and refined",
            message_hierarchy=["Focus", "Quality", "Comfort"],
        )
        assert brief.icp_id == "icp-001"
        assert len(brief.message_hierarchy) == 3

    def test_creative_concept_model(self):
        """CreativeConcept model validates correctly."""
        concept = CreativeConcept(
            icp_id="icp-001",
            big_idea="Your sanctuary of sound",
            visual_metaphor=None,
            layout_archetype="Hero Product with Stat Overlay",
            scene_description="Minimalist workspace with soft lighting",
            product_placement=ProductPlacement(
                position="center",
                size="dominant",
                treatment="floating with shadow",
            ),
            mood="Calm and sophisticated",
            color_direction="Dark background with accent highlights",
            focal_point="Product center frame",
        )
        assert concept.big_idea == "Your sanctuary of sound"
        assert concept.product_placement.size == "dominant"

    def test_ad_copy_model(self):
        """AdCopy model validates correctly."""
        copy = AdCopy(
            icp_id="icp-001",
            headline="Your Focus, Engineered",
            subheadline=None,
            body_copy="40 hours of silence. Zero distractions.",
            cta_text="Shop Now",
            cta_urgency=None,
            legal_disclaimer=None,
        )
        assert copy.headline == "Your Focus, Engineered"
        assert copy.cta_text == "Shop Now"


class TestAssetModels:
    """Tests for asset and error tracking models."""

    def test_image_asset_model(self):
        """ImageAsset model validates correctly."""
        asset = ImageAsset(
            path="output/scene_icp001.png",
            url=None,
            prompt_used="Minimalist workspace scene",
            width=1080,
            height=1080,
        )
        assert asset.path == "output/scene_icp001.png"
        assert asset.width == 1080

    def test_error_log_model(self):
        """ErrorLog model validates correctly."""
        error = ErrorLog(
            agent_name="design",
            icp_id="icp-001",
            error_message="Image generation failed",
        )
        assert error.agent_name == "design"
        assert error.timestamp is not None


class TestSampleDataIntegration:
    """Integration tests using complete sample data files."""

    def test_dtc_sample_complete(self, dtc_sample_data):
        """All fields in DTC sample parse correctly."""
        product = ProductData(**dtc_sample_data["product"])
        store_brand = BrandContext(**dtc_sample_data["store_brand"])
        channel = ChannelContext(**dtc_sample_data["channel"])
        store_context = StoreContext(**dtc_sample_data["store_context"])

        assert product.name
        assert store_brand.brand_name
        assert channel.platform
        assert store_context.price_positioning

    def test_multi_brand_sample_complete(self, multi_brand_sample_data):
        """All fields in multi-brand sample parse correctly."""
        product = ProductData(**multi_brand_sample_data["product"])
        store_brand = BrandContext(**multi_brand_sample_data["store_brand"])
        product_brand = BrandContext(**multi_brand_sample_data["product_brand"])
        channel = ChannelContext(**multi_brand_sample_data["channel"])

        assert product.price.compare_at_price == 449.00
        assert store_brand.brand_name == "TechMart"
        assert product_brand.brand_name == "Sony"
        assert multi_brand_sample_data["brand_strategy"] == "product_dominant"
