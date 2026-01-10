"""
CLI runner for Sartor Ad Engine pipeline.

Provides command-line interface to execute the full ad generation workflow
from a product JSON input file.

Usage:
    python -m src.runner --input data/samples/dtc_product.json
    python -m src.runner --input data/samples/multi_brand_retailer.json --output-dir output/run_001
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.graph import build_graph
from src.models import (
    BrandContext,
    ChannelContext,
    ColorPalette,
    Dimensions,
    ProductData,
    Price,
    StoreContext,
    TextConstraints,
)
from src.state import create_graph_state, GraphState


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# =============================================================================
# INPUT PARSING
# =============================================================================

def load_product_input(file_path: str) -> dict[str, Any]:
    """
    Load and parse product input JSON file.
    
    Args:
        file_path: Path to JSON input file
        
    Returns:
        Parsed JSON as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_product_data(data: dict) -> ProductData:
    """Parse product data from input dict to Pydantic model."""
    product = data["product"]
    
    # Parse price
    price_data = product.get("price", {})
    price = Price(
        value=price_data.get("value", 0),
        currency=price_data.get("currency", "USD"),
        compare_at_price=price_data.get("compare_at_price"),
    )
    
    return ProductData(
        product_id=product.get("product_id", ""),
        name=product.get("name", ""),
        description=product.get("description", ""),
        features=product.get("features", []),
        benefits=product.get("benefits", []),
        price=price,
        category=product.get("category", ""),
        images=product.get("images", []),
        metadata=product.get("metadata", {}),
    )


def parse_brand_context(data: dict) -> BrandContext:
    """Parse brand context from input dict to Pydantic model."""
    # Parse color palette
    palette_data = data.get("color_palette", {})
    color_palette = ColorPalette(
        primary=palette_data.get("primary", "#000000"),
        secondary=palette_data.get("secondary"),
        accent=palette_data.get("accent"),
        background=palette_data.get("background"),
    )
    
    return BrandContext(
        brand_name=data.get("brand_name", ""),
        brand_voice=data.get("brand_voice", ""),
        tone_keywords=data.get("tone_keywords", []),
        visual_style=data.get("visual_style", ""),
        color_palette=color_palette,
        logo_url=data.get("logo_url"),
        tagline=data.get("tagline"),
    )


def parse_channel_context(data: dict) -> ChannelContext:
    """Parse channel context from input dict to Pydantic model."""
    # Parse dimensions
    dimensions_data = data.get("dimensions", {})
    dimensions = Dimensions(
        width=dimensions_data.get("width", 1080),
        height=dimensions_data.get("height", 1080),
    )
    
    # Parse text constraints
    constraints_data = data.get("text_constraints", {})
    text_constraints = TextConstraints(
        headline_max_chars=constraints_data.get("headline_max_chars", 40),
        body_max_chars=constraints_data.get("body_max_chars", 125),
        cta_max_chars=constraints_data.get("cta_max_chars", 20),
    )
    
    return ChannelContext(
        platform=data.get("platform", ""),
        placement=data.get("placement", ""),
        dimensions=dimensions,
        text_constraints=text_constraints,
        audience_context=data.get("audience_context"),
    )


def parse_store_context(data: dict | None) -> StoreContext | None:
    """Parse store context from input dict to Pydantic model."""
    if not data:
        return None
    
    return StoreContext(
        customer_summary=data.get("customer_summary"),
        price_positioning=data.get("price_positioning", "mid-range"),
        competitors=data.get("competitors", []),
        store_statistics=data.get("store_statistics"),
    )


def parse_full_input(data: dict) -> GraphState:
    """
    Parse full input JSON into a GraphState.
    
    Args:
        data: Parsed JSON dictionary
        
    Returns:
        Initialized GraphState ready for pipeline execution
    """
    # Parse all components
    product = parse_product_data(data)
    store_brand = parse_brand_context(data["store_brand"])
    
    product_brand = None
    if data.get("product_brand"):
        product_brand = parse_brand_context(data["product_brand"])
    
    channel = parse_channel_context(data["channel"])
    store_context = parse_store_context(data.get("store_context"))
    brand_strategy = data.get("brand_strategy", "store_dominant")
    
    # Create state
    return create_graph_state(
        product=product,
        store_brand=store_brand,
        channel=channel,
        brand_strategy=brand_strategy,
        product_brand=product_brand,
        store_context=store_context,
    )


# =============================================================================
# OUTPUT HANDLING
# =============================================================================

def save_run_summary(state: GraphState, output_dir: Path, elapsed_time: float) -> Path:
    """
    Save a summary of the pipeline run to a JSON file.
    
    Args:
        state: Final graph state after pipeline execution
        output_dir: Output directory
        elapsed_time: Total execution time in seconds
        
    Returns:
        Path to the saved summary file
    """
    summary = {
        "run_id": state.get("run_id", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": round(elapsed_time, 2),
        "product_name": state["product"].name,
        "store_brand": state["store_brand"].brand_name,
        "brand_strategy": state.get("brand_strategy", "store_dominant"),
        "icps_generated": len(state.get("icps", [])),
        "ads_generated": len(state.get("final_ads", {})),
        "errors_count": len(state.get("errors", [])),
        "icps": [
            {
                "icp_id": icp.icp_id,
                "name": icp.name,
                "has_strategy": icp.icp_id in state.get("strategies", {}),
                "has_concept": icp.icp_id in state.get("concepts", {}),
                "has_copy": icp.icp_id in state.get("copy", {}),
                "has_scene": icp.icp_id in state.get("scenes", {}),
                "has_final_ad": icp.icp_id in state.get("final_ads", {}),
            }
            for icp in state.get("icps", [])
        ],
        "final_ads": {
            icp_id: {
                "path": asset.path,
                "width": asset.width,
                "height": asset.height,
            }
            for icp_id, asset in state.get("final_ads", {}).items()
        },
        "errors": [
            {
                "agent": err.agent_name,
                "icp_id": err.icp_id,
                "message": err.error_message,
            }
            for err in state.get("errors", [])
        ],
    }
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save summary
    summary_path = output_dir / f"run_summary_{state.get('run_id', 'unknown')[:8]}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    return summary_path


def print_run_report(state: GraphState, elapsed_time: float) -> None:
    """Print a human-readable report of the pipeline run."""
    print("\n" + "=" * 60)
    print("SARTOR AD ENGINE - RUN COMPLETE")
    print("=" * 60)
    
    print(f"\nRun ID:         {state.get('run_id', 'unknown')[:8]}")
    print(f"Product:        {state['product'].name}")
    print(f"Store Brand:    {state['store_brand'].brand_name}")
    print(f"Brand Strategy: {state.get('brand_strategy', 'store_dominant')}")
    print(f"Elapsed Time:   {elapsed_time:.2f}s")
    
    icps = state.get("icps", [])
    final_ads = state.get("final_ads", {})
    errors = state.get("errors", [])
    
    print(f"\n📊 RESULTS:")
    print(f"   ICPs Generated:  {len(icps)}")
    print(f"   Ads Produced:    {len(final_ads)}")
    print(f"   Errors:          {len(errors)}")
    
    if icps:
        print(f"\n👥 ICPs:")
        for icp in icps:
            status = "✅" if icp.icp_id in final_ads else "❌"
            print(f"   {status} {icp.name} ({icp.icp_id})")
    
    if final_ads:
        print(f"\n🖼️  Final Ads:")
        for icp_id, asset in final_ads.items():
            print(f"   • {icp_id}: {asset.path}")
    
    if errors:
        print(f"\n⚠️  Errors:")
        for err in errors:
            icp_info = f" (ICP: {err.icp_id})" if err.icp_id else ""
            print(f"   • [{err.agent_name}]{icp_info}: {err.error_message[:80]}")
    
    print("\n" + "=" * 60 + "\n")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_pipeline(
    input_file: str,
    output_dir: str | None = None,
    run_id: str | None = None,
    verbose: bool = False,
) -> GraphState:
    """
    Execute the full ad generation pipeline.
    
    Args:
        input_file: Path to product input JSON file
        output_dir: Output directory (defaults to settings.output_dir)
        run_id: Optional custom run ID
        verbose: Enable verbose logging
        
    Returns:
        Final GraphState after pipeline execution
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    settings = get_settings()
    output_path = Path(output_dir) if output_dir else Path(settings.output_dir)
    
    # Load input
    logger.info(f"Loading input from: {input_file}")
    input_data = load_product_input(input_file)
    
    # Parse to state
    logger.info("Parsing input data...")
    state = parse_full_input(input_data)
    
    # Override run_id if provided
    if run_id:
        state["run_id"] = run_id
    
    logger.info(f"Run ID: {state['run_id']}")
    logger.info(f"Product: {state['product'].name}")
    logger.info(f"Output directory: {output_path}")
    
    # Build and run graph
    logger.info("Building graph...")
    graph = build_graph()
    
    logger.info("Starting pipeline execution...")
    start_time = time.time()
    
    try:
        # Execute the graph
        final_state = graph.invoke(state)
        elapsed_time = time.time() - start_time
        
        # Save summary
        summary_path = save_run_summary(final_state, output_path, elapsed_time)
        logger.info(f"Run summary saved to: {summary_path}")
        
        # Print report
        print_run_report(final_state, elapsed_time)
        
        return final_state
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Pipeline failed after {elapsed_time:.2f}s: {e}")
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sartor Ad Engine - Generate personalized ads for eCommerce products",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.runner --input data/samples/dtc_product.json
  python -m src.runner --input data/samples/multi_brand_retailer.json --output-dir output/run_001
  python -m src.runner --input input.json --run-id my-custom-run --verbose
        """,
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to product input JSON file",
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Output directory for generated ads (default: output/)",
    )
    
    parser.add_argument(
        "--run-id",
        default=None,
        help="Custom run ID (auto-generated if not provided)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    try:
        run_pipeline(
            input_file=args.input,
            output_dir=args.output_dir,
            run_id=args.run_id,
            verbose=args.verbose,
        )
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
