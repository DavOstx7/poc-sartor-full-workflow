"""
Checkpoint and resume logic for Sartor Ad Engine.

Provides checkpoint persistence for long-running pipeline executions,
enabling resume capability after interruptions.

This module uses LangGraph's built-in checkpointing with SQLite storage.

NOTE: Requires optional dependency: pip install langgraph-checkpoint-sqlite
"""

import logging
from pathlib import Path
from typing import Optional

# Optional checkpoint support - requires langgraph-checkpoint-sqlite
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    CHECKPOINT_AVAILABLE = True
except ImportError:
    SqliteSaver = None
    CHECKPOINT_AVAILABLE = False

from src.config import get_settings
from src.graph import build_graph
from src.state import GraphState


logger = logging.getLogger(__name__)


# =============================================================================
# CHECKPOINT CONFIGURATION
# =============================================================================

def get_checkpoint_path() -> Path:
    """Get the path for checkpoint storage."""
    settings = get_settings()
    checkpoint_dir = Path(settings.output_dir) / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir / "sartor_checkpoints.db"


def create_checkpointer():
    """
    Create a SQLite-based checkpointer for the pipeline.
    
    Returns:
        SqliteSaver instance configured for our checkpoint storage
        
    Raises:
        ImportError: If langgraph-checkpoint-sqlite is not installed
    """
    if not CHECKPOINT_AVAILABLE:
        raise ImportError(
            "Checkpoint support requires langgraph-checkpoint-sqlite. "
            "Install with: pip install langgraph-checkpoint-sqlite"
        )
    
    checkpoint_path = get_checkpoint_path()
    logger.info(f"Checkpoint storage: {checkpoint_path}")
    return SqliteSaver.from_conn_string(f"sqlite:///{checkpoint_path}")


# =============================================================================
# GRAPH WITH CHECKPOINTING
# =============================================================================

def build_graph_with_checkpoints():
    """
    Build the graph with checkpoint support enabled.
    
    Returns:
        Compiled graph with SQLite checkpointing
    """
    checkpointer = create_checkpointer()
    
    # Import and rebuild with checkpointer
    from langgraph.graph import END, START, StateGraph
    from src.graph import segmentation_node, process_icp_node, route_to_icps
    
    builder = StateGraph(GraphState)
    
    # Add nodes
    builder.add_node("segmentation", segmentation_node)
    builder.add_node("process_icp", process_icp_node)
    
    # Add edges
    builder.add_edge(START, "segmentation")
    builder.add_conditional_edges("segmentation", route_to_icps)
    builder.add_edge("process_icp", END)
    
    # Compile with checkpointer
    graph = builder.compile(checkpointer=checkpointer)
    
    logger.info("Graph compiled with checkpointing enabled")
    
    return graph


# =============================================================================
# CHECKPOINT OPERATIONS
# =============================================================================

def get_checkpoint_config(run_id: str, thread_id: str = "main") -> dict:
    """
    Create checkpoint configuration for a run.
    
    Args:
        run_id: Unique identifier for the pipeline run
        thread_id: Thread identifier (default: "main")
        
    Returns:
        Config dict for checkpoint operations
    """
    return {
        "configurable": {
            "thread_id": f"{run_id}_{thread_id}",
        }
    }


def run_with_checkpoints(
    state: GraphState,
    run_id: Optional[str] = None,
) -> GraphState:
    """
    Run the pipeline with checkpoint persistence.
    
    Args:
        state: Initial graph state
        run_id: Optional run ID (uses state's run_id if not provided)
        
    Returns:
        Final graph state
    """
    run_id = run_id or state.get("run_id", "unknown")
    config = get_checkpoint_config(run_id)
    
    graph = build_graph_with_checkpoints()
    
    logger.info(f"Running pipeline with checkpoints (run_id: {run_id})")
    
    return graph.invoke(state, config=config)


def resume_from_checkpoint(run_id: str) -> Optional[GraphState]:
    """
    Resume a pipeline from the last checkpoint.
    
    Args:
        run_id: Run ID of the interrupted pipeline
        
    Returns:
        Final graph state if resumable, None if no checkpoint found
    """
    config = get_checkpoint_config(run_id)
    
    graph = build_graph_with_checkpoints()
    
    logger.info(f"Attempting to resume from checkpoint (run_id: {run_id})")
    
    try:
        # Get the last checkpoint state
        checkpoint = graph.get_state(config)
        
        if checkpoint.values:
            logger.info(f"Found checkpoint, resuming...")
            # Resume from checkpoint
            return graph.invoke(None, config=config)
        else:
            logger.warning(f"No checkpoint found for run_id: {run_id}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to resume from checkpoint: {e}")
        return None


def list_checkpoints() -> list[str]:
    """
    List all available checkpoint run IDs.
    
    Returns:
        List of run IDs with checkpoints
    """
    checkpoint_path = get_checkpoint_path()
    
    if not checkpoint_path.exists():
        return []
    
    # Query SQLite for unique thread_ids
    import sqlite3
    
    try:
        conn = sqlite3.connect(checkpoint_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        rows = cursor.fetchall()
        conn.close()
        
        # Extract run_id from thread_id (format: "{run_id}_main")
        run_ids = []
        for row in rows:
            thread_id = row[0]
            if "_" in thread_id:
                run_id = thread_id.rsplit("_", 1)[0]
                if run_id not in run_ids:
                    run_ids.append(run_id)
        
        return run_ids
        
    except Exception as e:
        logger.error(f"Failed to list checkpoints: {e}")
        return []


def clear_checkpoint(run_id: str) -> bool:
    """
    Clear checkpoint for a specific run.
    
    Args:
        run_id: Run ID to clear
        
    Returns:
        True if cleared, False otherwise
    """
    checkpoint_path = get_checkpoint_path()
    
    if not checkpoint_path.exists():
        return False
    
    import sqlite3
    
    try:
        conn = sqlite3.connect(checkpoint_path)
        cursor = conn.cursor()
        # Delete checkpoints matching this run_id
        cursor.execute(
            "DELETE FROM checkpoints WHERE thread_id LIKE ?",
            (f"{run_id}_%",)
        )
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        
        logger.info(f"Cleared {deleted} checkpoints for run_id: {run_id}")
        return deleted > 0
        
    except Exception as e:
        logger.error(f"Failed to clear checkpoint: {e}")
        return False


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "build_graph_with_checkpoints",
    "run_with_checkpoints",
    "resume_from_checkpoint",
    "list_checkpoints",
    "clear_checkpoint",
    "get_checkpoint_config",
]
