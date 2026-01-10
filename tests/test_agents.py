"""
Tests for Sartor Ad Engine agents.

Tests agent implementations with mocked LLM responses to verify:
- Correct prompt construction
- Schema-compliant outputs
- Error handling
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models import (
    AdCopy,
    BrandContext,
    ChannelContext,
    CreativeConcept,
    Dimensions,
    ICP,
    ProductData,
    ProductPlacement,
    StrategicBrief,
    TextConstraints,
)
from src.state import create_initial_state


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_product():
    """Create a mock product for testing."""
    return ProductData(
        product_id="TEST-001",
        name="Test Wireless Headphones",
        description="Premium noise-canceling headphones",
        features=["Active Noise Cancellation", "40hr Battery", "Bluetooth 5.3"],
        benefits=["Focus without distractions", "All-day listening"],
        price={"value": 299.00, "currency": "USD"},
        category="Electronics > Audio > Headphones",
        images=["https://example.com/product.jpg"],
    )


@pytest.fixture
def mock_store_brand():
    """Create a mock store brand for testing."""
    return BrandContext(
        brand_name="TestBrand",
        brand_voice="Premium, innovative, minimalist",
        tone_keywords=["confident", "refined", "modern"],
        visual_style="Clean lines, dark backgrounds",
        color_palette={"primary": "#1A1A2E", "accent": "#E94560"},
        logo_url="https://example.com/logo.png",
    )


@pytest.fixture
def mock_channel():
    """Create a mock channel context for testing."""
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
def mock_icp():
    """Create a mock ICP for testing."""
    return ICP(
        icp_id="test_icp_001",
        name="Test Professional",
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
            "responds_to": ["data_and_specs", "social_proof"],
        },
    )


@pytest.fixture
def mock_strategy(mock_icp):
    """Create a mock strategic brief for testing."""
    return StrategicBrief(
        icp_id=mock_icp.icp_id,
        positioning_statement="For busy professionals who need focus...",
        primary_pain_point="Distractions during remote work",
        key_benefit="Deep focus with premium noise cancellation",
        proof_point="40-hour battery life",
        emotional_appeal="Confidence and control",
        tone_of_voice="Confident and refined",
        message_hierarchy=["Focus", "Quality", "Comfort"],
    )


@pytest.fixture
def mock_concept(mock_icp):
    """Create a mock creative concept for testing."""
    return CreativeConcept(
        icp_id=mock_icp.icp_id,
        big_idea="Your sanctuary of sound",
        visual_metaphor=None,
        layout_archetype="Hero Product Shot",
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


@pytest.fixture
def mock_state(mock_product, mock_store_brand, mock_channel):
    """Create a mock state for testing."""
    return create_initial_state(
        product=mock_product,
        store_brand=mock_store_brand,
        channel=mock_channel,
        brand_strategy="store_dominant",
    )


# =============================================================================
# SEGMENTATION AGENT TESTS
# =============================================================================

class TestSegmentationAgent:
    """Tests for the Segmentation Agent."""

    def test_segmentation_returns_icps_on_success(self, mock_state, mock_icp):
        """Verify segmentation returns list of ICPs on successful LLM call."""
        from agents.segmentation.agent import SegmentationResponse, run_segmentation_agent
        
        # Create a second ICP to test multiple ICP handling
        mock_icp_2 = ICP(
            icp_id="test_icp_002",
            name="Budget Shopper",
            demographic={
                "age_range": "35-45",
                "gender": None,
                "income_level": "Middle",
                "location_type": "Suburban",
            },
            psychographics={
                "values": ["value", "practicality"],
                "lifestyle": "Family-focused",
                "aspirations": "Financial security",
            },
            behavioral_triggers={
                "purchase_motivators": ["deals", "necessity"],
                "objections": ["quality concerns"],
                "decision_factors": ["price", "reviews"],
            },
            communication_preferences={
                "tone": "Friendly",
                "vocabulary_level": "Conversational",
                "responds_to": ["value_proposition", "social_proof"],
            },
        )
        
        # Mock the LLM with 2 ICPs
        mock_response = SegmentationResponse(icps=[mock_icp, mock_icp_2])
        
        with patch("agents.segmentation.agent.create_llm_for_agent") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.with_structured_output.return_value.invoke.return_value = mock_response
            mock_create_llm.return_value = mock_llm
            
            result = run_segmentation_agent(mock_state)
        
        assert "icps" in result
        assert len(result["icps"]) == 2
        assert result["icps"][0].icp_id == mock_icp.icp_id

    def test_segmentation_handles_llm_error(self, mock_state):
        """Verify segmentation gracefully handles LLM failures."""
        from agents.segmentation.agent import run_segmentation_agent
        
        with patch("agents.segmentation.agent.create_llm_for_agent") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("API Error")
            mock_create_llm.return_value = mock_llm
            
            result = run_segmentation_agent(mock_state)
        
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "API Error" in result["errors"][0].error_message


# =============================================================================
# STRATEGY AGENT TESTS
# =============================================================================

class TestStrategyAgent:
    """Tests for the Strategy Agent."""

    def test_strategy_processes_all_icps(self, mock_state, mock_icp, mock_strategy):
        """Verify strategy generates brief for each ICP."""
        from agents.strategy.agent import run_strategy_agent
        
        # Add ICP to state
        mock_state["icps"] = [mock_icp]
        
        with patch("agents.strategy.agent.create_llm_for_agent") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.with_structured_output.return_value.invoke.return_value = mock_strategy
            mock_create_llm.return_value = mock_llm
            
            result = run_strategy_agent(mock_state)
        
        assert "strategies" in result
        assert mock_icp.icp_id in result["strategies"]
        assert result["strategies"][mock_icp.icp_id].key_benefit == mock_strategy.key_benefit

    def test_strategy_handles_missing_icps(self, mock_state):
        """Verify strategy handles case with no ICPs."""
        from agents.strategy.agent import run_strategy_agent
        
        mock_state["icps"] = []
        
        result = run_strategy_agent(mock_state)
        
        assert "errors" in result


# =============================================================================
# CONCEPT AGENT TESTS
# =============================================================================

class TestConceptAgent:
    """Tests for the Concept Agent."""

    def test_concept_uses_strategy(self, mock_state, mock_icp, mock_strategy, mock_concept):
        """Verify concept agent uses strategy from prior agent."""
        from agents.concept.agent import run_concept_agent
        
        mock_state["icps"] = [mock_icp]
        mock_state["strategies"] = {mock_icp.icp_id: mock_strategy}
        
        with patch("agents.concept.agent.create_llm_for_agent") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.with_structured_output.return_value.invoke.return_value = mock_concept
            mock_create_llm.return_value = mock_llm
            
            result = run_concept_agent(mock_state)
        
        assert "concepts" in result
        assert mock_icp.icp_id in result["concepts"]
        assert result["concepts"][mock_icp.icp_id].big_idea == mock_concept.big_idea


# =============================================================================
# COPY AGENT TESTS
# =============================================================================

class TestCopyAgent:
    """Tests for the Copy Agent."""

    def test_copy_generates_ad_copy(self, mock_state, mock_icp, mock_strategy, mock_concept):
        """Verify copy agent generates ad copy for ICP."""
        from agents.copy.agent import run_copy_agent
        
        mock_state["icps"] = [mock_icp]
        mock_state["strategies"] = {mock_icp.icp_id: mock_strategy}
        mock_state["concepts"] = {mock_icp.icp_id: mock_concept}
        
        mock_ad_copy = AdCopy(
            icp_id=mock_icp.icp_id,
            headline="Your Focus, Engineered",
            subheadline=None,
            body_copy="40 hours of silence.",
            cta_text="Shop Now",
            cta_urgency=None,
            legal_disclaimer=None,
        )
        
        with patch("agents.copy.agent.create_llm_for_agent") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.with_structured_output.return_value.invoke.return_value = mock_ad_copy
            mock_create_llm.return_value = mock_llm
            
            result = run_copy_agent(mock_state)
        
        assert "copy" in result
        assert mock_icp.icp_id in result["copy"]
        assert result["copy"][mock_icp.icp_id].headline == "Your Focus, Engineered"


# =============================================================================
# DESIGN AGENT TESTS
# =============================================================================

class TestDesignAgent:
    """Tests for the Design Agent."""

    def test_design_builds_prompt_package(self, mock_state, mock_icp, mock_concept):
        """Verify design agent builds image generation prompt."""
        from agents.design.agent import run_design_agent
        
        mock_state["icps"] = [mock_icp]
        mock_state["concepts"] = {mock_icp.icp_id: mock_concept}
        
        result = run_design_agent(mock_state)
        
        assert "scenes" in result
        assert mock_icp.icp_id in result["scenes"]
        # Verify the ImageAsset has required fields
        asset = result["scenes"][mock_icp.icp_id]
        assert asset.width == 1080
        assert asset.height == 1080
        assert asset.prompt_used is not None
