from pathlib import Path
from typing import Optional

from .engine import ReplayEngine
from .loader import JsonLoader
from .models import Alert, ReplayEnvelope, ValidationContext
from .modes import ReplayMode, ReplayOutputFormat
from .queue import AlertQueue

def create_engine(
    filepath: str | Path | None = None,
    include_ground_truth: bool = False,
    mode: ReplayMode = ReplayMode.TIME_PRESERVED,
    output_format: ReplayOutputFormat = ReplayOutputFormat.RAW,
    acceleration_factor: float = 1.0,
) -> ReplayEngine:
    """
    Convenience function to initialize the ReplayEngine.
    
    Args:
        filepath: Path to a specific JSON file, or a directory containing JSON files.
                  Defaults to 'inputs' if None.
        include_ground_truth: Whether to look for and include GroundTruth context files.
        mode: ReplayMode to use (SEQUENTIAL, TIME_PRESERVED, ACCELERATED).
        output_format: Output format for the engine.
        acceleration_factor: Factor by which to accelerate replay (only for ACCELERATED mode).
    """
    loader = JsonLoader(filepath=filepath, include_ground_truth=include_ground_truth)
    dataset = loader.load()
    return ReplayEngine(
        dataset=dataset,
        mode=mode,
        output_format=output_format,
        acceleration_factor=acceleration_factor
    )

__all__ = [
    "create_engine",
    "Alert",
    "AlertQueue",
    "JsonLoader",
    "ReplayEngine",
    "ReplayEnvelope",
    "ReplayMode",
    "ReplayOutputFormat",
    "ValidationContext",
]