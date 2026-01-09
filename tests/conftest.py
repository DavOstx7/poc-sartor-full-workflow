"""
Pytest configuration and fixtures for Sartor Ad Engine tests.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def samples_dir() -> Path:
    """Path to sample data directory."""
    return Path(__file__).parent.parent / "data" / "samples"


@pytest.fixture
def dtc_sample_data(samples_dir: Path) -> dict:
    """Load DTC product sample (store_dominant strategy)."""
    path = samples_dir / "dtc_product.json"
    return json.loads(path.read_text())


@pytest.fixture
def multi_brand_sample_data(samples_dir: Path) -> dict:
    """Load multi-brand retailer sample (product_dominant strategy)."""
    path = samples_dir / "multi_brand_retailer.json"
    return json.loads(path.read_text())


@pytest.fixture
def dtc_product(dtc_sample_data: dict):
    """ProductData instance from DTC sample."""
    from src.models import ProductData
    return ProductData(**dtc_sample_data["product"])


@pytest.fixture
def dtc_store_brand(dtc_sample_data: dict):
    """BrandContext instance from DTC sample (store brand)."""
    from src.models import BrandContext
    return BrandContext(**dtc_sample_data["store_brand"])


@pytest.fixture
def dtc_channel(dtc_sample_data: dict):
    """ChannelContext instance from DTC sample."""
    from src.models import ChannelContext
    return ChannelContext(**dtc_sample_data["channel"])


@pytest.fixture
def multi_brand_product(multi_brand_sample_data: dict):
    """ProductData instance from multi-brand sample."""
    from src.models import ProductData
    return ProductData(**multi_brand_sample_data["product"])


@pytest.fixture
def multi_brand_product_brand(multi_brand_sample_data: dict):
    """BrandContext instance for product brand (Sony)."""
    from src.models import BrandContext
    return BrandContext(**multi_brand_sample_data["product_brand"])
