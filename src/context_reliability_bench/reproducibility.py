from __future__ import annotations

import platform
import sys
from dataclasses import dataclass

from context_reliability_bench import __version__


@dataclass(frozen=True)
class ReproducibilityMetadata:
    """Captures the environment needed to reproduce a benchmark run."""

    python_version: str
    platform_system: str
    platform_machine: str
    library_version: str
    seed: int | None

    def is_reproducible(self) -> bool:
        """A run is reproducible when a seed is set."""
        return self.seed is not None

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "python_version": self.python_version,
            "platform_system": self.platform_system,
            "platform_machine": self.platform_machine,
            "library_version": self.library_version,
            "seed": self.seed,
        }


def capture_metadata(seed: int | None = None) -> ReproducibilityMetadata:
    """Capture the current Python environment as reproducibility metadata."""
    return ReproducibilityMetadata(
        python_version=sys.version,
        platform_system=platform.system(),
        platform_machine=platform.machine(),
        library_version=__version__,
        seed=seed,
    )
