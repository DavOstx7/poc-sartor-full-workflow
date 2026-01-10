"""
Pytest configuration and fixtures for E2E tests.
"""

import json
from pathlib import Path
from typing import Generator

import pytest


# =============================================================================
# PATHS
# =============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def samples_dir(project_root: Path) -> Path:
    """Return the samples directory path."""
    return project_root / "data" / "samples"


@pytest.fixture(scope="session")
def output_dir(project_root: Path) -> Path:
    """Return and create the output directory for e2e tests."""
    output_path = project_root / "output" / "e2e_tests"
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


# =============================================================================
# TEST CASE DATA LOADERS
# =============================================================================

TEST_CASES = [
    "tc01_electronics_premium",
    "tc02_skincare_luxury",
    "tc03_fashion_streetwear",
    "tc04_home_artisanal",
    "tc05_tech_massmarket",
]


@pytest.fixture(scope="session")
def test_case_paths(samples_dir: Path) -> dict[str, Path]:
    """Return dict mapping test case names to their JSON file paths."""
    return {
        tc: samples_dir / f"{tc}.json"
        for tc in TEST_CASES
    }


def load_test_case(samples_dir: Path, test_case: str) -> dict:
    """Load a test case JSON file."""
    path = samples_dir / f"{test_case}.json"
    if not path.exists():
        raise FileNotFoundError(f"Test case file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def tc01_data(samples_dir: Path) -> dict:
    """Load TC-01: Electronics Premium test case."""
    return load_test_case(samples_dir, "tc01_electronics_premium")


@pytest.fixture
def tc02_data(samples_dir: Path) -> dict:
    """Load TC-02: Skincare Luxury test case."""
    return load_test_case(samples_dir, "tc02_skincare_luxury")


@pytest.fixture
def tc03_data(samples_dir: Path) -> dict:
    """Load TC-03: Fashion Streetwear test case."""
    return load_test_case(samples_dir, "tc03_fashion_streetwear")


@pytest.fixture
def tc04_data(samples_dir: Path) -> dict:
    """Load TC-04: Home Artisanal test case."""
    return load_test_case(samples_dir, "tc04_home_artisanal")


@pytest.fixture
def tc05_data(samples_dir: Path) -> dict:
    """Load TC-05: Tech Mass-Market test case."""
    return load_test_case(samples_dir, "tc05_tech_massmarket")


# =============================================================================
# PIPELINE EXECUTION HELPER
# =============================================================================

@pytest.fixture(scope="session")
def pipeline_results(samples_dir: Path, output_dir: Path) -> dict:
    """
    Run the pipeline for all test cases and return results.
    
    This is session-scoped to avoid re-running the full pipeline
    multiple times. Results are cached for the test session.
    """
    from src.runner import run_pipeline
    
    results = {}
    
    for tc in TEST_CASES:
        tc_input = samples_dir / f"{tc}.json"
        tc_output = output_dir / tc
        tc_output.mkdir(parents=True, exist_ok=True)
        
        try:
            state = run_pipeline(
                input_file=str(tc_input),
                output_dir=str(tc_output),
                run_id=tc,
                verbose=False,
            )
            results[tc] = {
                "state": state,
                "success": True,
                "error": None,
                "output_dir": tc_output,
            }
        except Exception as e:
            results[tc] = {
                "state": None,
                "success": False,
                "error": str(e),
                "output_dir": tc_output,
            }
    
    return results
