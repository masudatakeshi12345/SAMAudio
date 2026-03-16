from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_workspace() -> Path:
    return Path(os.environ.get("SAMAUDIO_WORKSPACE", ".samaudio")).resolve()


@dataclass(frozen=True)
class AppConfig:
    workspace_dir: Path = _default_workspace()
    enrollment_dirname: str = "enrollments"
    export_dirname: str = "exports"
    similarity_threshold: float = 0.72
    min_segment_seconds: float = 1.0

    @property
    def enrollment_dir(self) -> Path:
        return self.workspace_dir / self.enrollment_dirname

    @property
    def export_dir(self) -> Path:
        return self.workspace_dir / self.export_dirname


DEFAULT_CONFIG = AppConfig()
