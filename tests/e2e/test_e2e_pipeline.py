"""
End-to-end tests for Sartor Ad Engine pipeline.

Runs the complete pipeline for 5 diverse test products and validates
outputs meet Phase 6 quality standards.

Test Cases:
- TC-01: Electronics (Premium) - DTC, store_dominant
- TC-02: Skincare (Luxury) - DTC, store_dominant
- TC-03: Fashion (Streetwear) - DTC, store_dominant
- TC-04: Home (Artisanal) - Multi-brand, product_dominant
- TC-05: Tech (Mass-market) - Multi-brand, co_branded
"""

import json
from pathlib import Path

import pytest

from tests.e2e.conftest import TEST_CASES, load_test_case
from tests.e2e.validators import (
    run_all_validations,
    validate_icps_generated,
    validate_pipeline_complete,
    validate_copy_limits,
    validate_ad_dimensions,
    validate_icps_distinct,
    validate_no_errors,
    validate_final_ads_exist,
)


# =============================================================================
# PIPELINE EXECUTION TESTS
# =============================================================================

class TestPipelineExecution:
    """Test that the pipeline executes successfully for each test case."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_pipeline_completes_without_crash(
        self,
        test_case: str,
        pipeline_results: dict,
    ):
        """Verify the pipeline runs to completion without exceptions."""
        result = pipeline_results[test_case]
        
        assert result["success"], (
            f"Pipeline failed for {test_case}: {result['error']}"
        )
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_no_pipeline_errors(
        self,
        test_case: str,
        pipeline_results: dict,
    ):
        """Verify no errors were logged during pipeline execution."""
        result = pipeline_results[test_case]
        
        if not result["success"]:
            pytest.skip(f"Pipeline did not complete: {result['error']}")
        
        passed, msg = validate_no_errors(result["state"])
        assert passed, msg


# =============================================================================
# ICP GENERATION TESTS
# =============================================================================

class TestICPGeneration:
    """Test ICP (Ideal Customer Profile) generation quality."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_icps_generated(
        self,
        test_case: str,
        pipeline_results: dict,
    ):
        """Verify at least 1 ICP was generated."""
        result = pipeline_results[test_case]
        
        if not result["success"]:
            pytest.skip(f"Pipeline did not complete: {result['error']}")
        
        passed, msg = validate_icps_generated(result["state"], min_count=1)
        assert passed, msg
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_icps_are_distinct(
        self,
        test_case: str,
        pipeline_results: dict,
    ):
        """Verify ICPs have unique names (are distinct)."""
        result = pipeline_results[test_case]
        
        if not result["success"]:
            pytest.skip(f"Pipeline did not complete: {result['error']}")
        
        passed, msg = validate_icps_distinct(result["state"])
        assert passed, msg


# =============================================================================
# PIPELINE COMPLETENESS TESTS
# =============================================================================

class TestPipelineCompleteness:
    """Test that all pipeline stages complete for each ICP."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_all_icps_have_complete_outputs(
        self,
        test_case: str,
        pipeline_results: dict,
    ):
        """Verify each ICP has strategy, concept, copy, scene, and final_ad."""
        result = pipeline_results[test_case]
        
        if not result["success"]:
            pytest.skip(f"Pipeline did not complete: {result['error']}")
        
        passed, msg = validate_pipeline_complete(result["state"])
        assert passed, msg


# =============================================================================
# COPY VALIDATION TESTS
# =============================================================================

class TestCopyValidation:
    """Test ad copy meets constraints."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_copy_within_character_limits(
        self,
        test_case: str,
        pipeline_results: dict,
        samples_dir: Path,
    ):
        """Verify all copy is within channel character limits."""
        result = pipeline_results[test_case]
        
        if not result["success"]:
            pytest.skip(f"Pipeline did not complete: {result['error']}")
        
        # Load the test case to get channel constraints
        test_data = load_test_case(samples_dir, test_case)
        channel = test_data["channel"]
        
        passed, msg = validate_copy_limits(result["state"], channel)
        assert passed, msg


# =============================================================================
# AD OUTPUT TESTS
# =============================================================================

class TestAdOutput:
    """Test final ad outputs."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_ad_dimensions_correct(
        self,
        test_case: str,
        pipeline_results: dict,
        samples_dir: Path,
    ):
        """Verify final ads have correct dimensions."""
        result = pipeline_results[test_case]
        
        if not result["success"]:
            pytest.skip(f"Pipeline did not complete: {result['error']}")
        
        # Load the test case to get channel dimensions
        test_data = load_test_case(samples_dir, test_case)
        channel = test_data["channel"]
        
        passed, msg = validate_ad_dimensions(result["state"], channel)
        assert passed, msg
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_ad_files_exist(
        self,
        test_case: str,
        pipeline_results: dict,
    ):
        """Verify final ad image files exist on disk."""
        result = pipeline_results[test_case]
        
        if not result["success"]:
            pytest.skip(f"Pipeline did not complete: {result['error']}")
        
        passed, msg = validate_final_ads_exist(
            result["state"],
            result["output_dir"],
        )
        assert passed, msg


# =============================================================================
# COMPREHENSIVE VALIDATION TEST
# =============================================================================

class TestComprehensiveValidation:
    """Run all validations and provide detailed report."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_all_validations_pass(
        self,
        test_case: str,
        pipeline_results: dict,
        samples_dir: Path,
    ):
        """Run all validation checks for each test case."""
        result = pipeline_results[test_case]
        
        if not result["success"]:
            pytest.fail(f"Pipeline did not complete: {result['error']}")
        
        # Load the test case to get channel context
        test_data = load_test_case(samples_dir, test_case)
        channel = test_data["channel"]
        
        # Run all validations
        validations = run_all_validations(
            state=result["state"],
            channel=channel,
            output_dir=result["output_dir"],
        )
        
        # Check for any failures
        failures = [
            f"{name}: {msg}"
            for name, (passed, msg) in validations.items()
            if not passed
        ]
        
        if failures:
            pytest.fail(f"Validation failures for {test_case}:\n" + "\n".join(failures))


# =============================================================================
# RESULTS SUMMARY GENERATOR
# =============================================================================

def generate_test_results_summary(
    pipeline_results: dict,
    samples_dir: Path,
    output_path: Path,
) -> None:
    """
    Generate a markdown summary of test results.
    
    Call this after running the test suite to generate docs/test_results.md
    """
    lines = [
        "# Phase 6 E2E Test Results",
        "",
        f"> Generated from e2e test run",
        "",
        "## Summary",
        "",
        "| Test Case | Status | ICPs | Ads | Errors |",
        "|-----------|--------|------|-----|--------|",
    ]
    
    for tc, result in pipeline_results.items():
        if result["success"]:
            state = result["state"]
            icp_count = len(state.get("icps", []))
            ad_count = len(state.get("final_ads", {}))
            error_count = len(state.get("errors", []))
            status = "✅ PASS" if error_count == 0 else "⚠️ PARTIAL"
        else:
            icp_count = 0
            ad_count = 0
            error_count = 1
            status = "❌ FAIL"
        
        lines.append(f"| {tc} | {status} | {icp_count} | {ad_count} | {error_count} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## Per-Test-Case Details",
        "",
    ])
    
    for tc, result in pipeline_results.items():
        lines.append(f"### {tc}")
        lines.append("")
        
        if not result["success"]:
            lines.append(f"**Error:** {result['error']}")
            lines.append("")
            continue
        
        state = result["state"]
        icps = state.get("icps", [])
        final_ads = state.get("final_ads", {})
        
        # Load test case for validation
        test_data = load_test_case(samples_dir, tc)
        channel = test_data["channel"]
        
        # Run validations
        validations = run_all_validations(
            state=state,
            channel=channel,
            output_dir=result["output_dir"],
        )
        
        lines.append("**ICPs Generated:**")
        for icp in icps:
            lines.append(f"- {icp.name} (`{icp.icp_id}`)")
        lines.append("")
        
        lines.append("**Validation Checklist:**")
        for name, (passed, msg) in validations.items():
            icon = "✅" if passed else "❌"
            lines.append(f"- {icon} **{name}:** {msg}")
        lines.append("")
        
        if final_ads:
            lines.append("**Generated Ads:**")
            for icp_id, asset in final_ads.items():
                lines.append(f"- `{icp_id}`: `{asset.path}`")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
