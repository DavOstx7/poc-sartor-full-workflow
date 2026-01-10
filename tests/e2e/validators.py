"""
Validation utilities for E2E testing.

Each validator returns a tuple of (passed: bool, message: str).
"""

from pathlib import Path
from typing import Any


def validate_icps_generated(state: dict, min_count: int = 1) -> tuple[bool, str]:
    """
    Validate that at least min_count ICPs were generated.
    
    Args:
        state: The final graph state
        min_count: Minimum number of ICPs expected
        
    Returns:
        (passed, message) tuple
    """
    icps = state.get("icps", [])
    count = len(icps)
    
    if count >= min_count:
        icp_names = [icp.name for icp in icps]
        return True, f"Generated {count} ICPs: {', '.join(icp_names)}"
    else:
        return False, f"Expected at least {min_count} ICPs, got {count}"


def validate_pipeline_complete(state: dict) -> tuple[bool, str]:
    """
    Validate that all ICPs have complete pipeline outputs.
    
    Checks that each ICP has: strategy, concept, copy, scene, final_ad
    
    Returns:
        (passed, message) tuple
    """
    icps = state.get("icps", [])
    strategies = state.get("strategies", {})
    concepts = state.get("concepts", {})
    copy = state.get("copy", {})
    scenes = state.get("scenes", {})
    final_ads = state.get("final_ads", {})
    
    missing = []
    
    for icp in icps:
        icp_id = icp.icp_id
        icp_missing = []
        
        if icp_id not in strategies:
            icp_missing.append("strategy")
        if icp_id not in concepts:
            icp_missing.append("concept")
        if icp_id not in copy:
            icp_missing.append("copy")
        if icp_id not in scenes:
            icp_missing.append("scene")
        if icp_id not in final_ads:
            icp_missing.append("final_ad")
        
        if icp_missing:
            missing.append(f"{icp.name}: missing {', '.join(icp_missing)}")
    
    if not missing:
        return True, f"All {len(icps)} ICPs have complete outputs"
    else:
        return False, f"Incomplete pipelines: {'; '.join(missing)}"


def validate_copy_limits(state: dict, channel: dict) -> tuple[bool, str]:
    """
    Validate that all copy is within character limits.
    
    Args:
        state: The final graph state
        channel: Channel context dict with text_constraints
        
    Returns:
        (passed, message) tuple
    """
    copy_dict = state.get("copy", {})
    constraints = channel.get("text_constraints", {})
    
    headline_max = constraints.get("headline_max_chars", 40)
    body_max = constraints.get("body_max_chars", 125)
    cta_max = constraints.get("cta_max_chars", 20)
    
    violations = []
    
    for icp_id, ad_copy in copy_dict.items():
        headline_len = len(ad_copy.headline) if ad_copy.headline else 0
        body_len = len(ad_copy.body_copy) if ad_copy.body_copy else 0
        cta_len = len(ad_copy.cta_text) if ad_copy.cta_text else 0
        
        if headline_len > headline_max:
            violations.append(f"{icp_id}: headline {headline_len}/{headline_max}")
        if body_len > body_max:
            violations.append(f"{icp_id}: body {body_len}/{body_max}")
        if cta_len > cta_max:
            violations.append(f"{icp_id}: CTA {cta_len}/{cta_max}")
    
    if not violations:
        return True, f"All copy within limits (H≤{headline_max}, B≤{body_max}, C≤{cta_max})"
    else:
        return False, f"Copy limit violations: {'; '.join(violations)}"


def validate_ad_dimensions(state: dict, channel: dict) -> tuple[bool, str]:
    """
    Validate that final ads match channel dimensions.
    
    Args:
        state: The final graph state
        channel: Channel context dict with dimensions
        
    Returns:
        (passed, message) tuple
    """
    final_ads = state.get("final_ads", {})
    dimensions = channel.get("dimensions", {})
    
    expected_width = dimensions.get("width", 1080)
    expected_height = dimensions.get("height", 1080)
    
    violations = []
    
    for icp_id, asset in final_ads.items():
        if asset.width != expected_width or asset.height != expected_height:
            violations.append(
                f"{icp_id}: {asset.width}x{asset.height} (expected {expected_width}x{expected_height})"
            )
    
    if not violations:
        return True, f"All ads at correct dimensions ({expected_width}x{expected_height})"
    else:
        return False, f"Dimension mismatches: {'; '.join(violations)}"


def validate_icps_distinct(state: dict) -> tuple[bool, str]:
    """
    Validate that ICPs are distinct (unique names).
    
    Returns:
        (passed, message) tuple
    """
    icps = state.get("icps", [])
    names = [icp.name for icp in icps]
    
    if len(names) == len(set(names)):
        return True, f"All {len(names)} ICP names are unique"
    else:
        duplicates = [name for name in names if names.count(name) > 1]
        return False, f"Duplicate ICP names: {set(duplicates)}"


def validate_no_errors(state: dict) -> tuple[bool, str]:
    """
    Validate that no errors occurred during pipeline execution.
    
    Returns:
        (passed, message) tuple
    """
    errors = state.get("errors", [])
    
    if not errors:
        return True, "No errors during pipeline execution"
    else:
        error_msgs = [f"{e.agent_name}: {e.error_message[:50]}" for e in errors]
        return False, f"Pipeline errors: {'; '.join(error_msgs)}"


def validate_final_ads_exist(state: dict, output_dir: Path) -> tuple[bool, str]:
    """
    Validate that final ad image files exist on disk.
    
    Returns:
        (passed, message) tuple
    """
    final_ads = state.get("final_ads", {})
    
    missing = []
    for icp_id, asset in final_ads.items():
        if not Path(asset.path).exists():
            missing.append(f"{icp_id}: {asset.path}")
    
    if not missing:
        return True, f"All {len(final_ads)} ad image files exist"
    else:
        return False, f"Missing ad files: {'; '.join(missing)}"


def run_all_validations(
    state: dict,
    channel: dict,
    output_dir: Path,
) -> dict[str, tuple[bool, str]]:
    """
    Run all validation checks and return results.
    
    Returns:
        Dict mapping validation name to (passed, message) tuple
    """
    return {
        "icps_generated": validate_icps_generated(state, min_count=1),
        "pipeline_complete": validate_pipeline_complete(state),
        "copy_limits": validate_copy_limits(state, channel),
        "ad_dimensions": validate_ad_dimensions(state, channel),
        "icps_distinct": validate_icps_distinct(state),
        "no_errors": validate_no_errors(state),
        "ads_exist": validate_final_ads_exist(state, output_dir),
    }
