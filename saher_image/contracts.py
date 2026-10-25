from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class OutputAsset:
    filename: str
    subfolder: str = ""
    media_type: str = "output"
    content_type: str = "application/octet-stream"


@dataclass(frozen=True)
class JobStatus:
    job_id: str
    state: JobState
    outputs: list[OutputAsset] = field(default_factory=list)
    error: str | None = None


class GenerationProvider(Protocol):
    """Adapter boundary; providers own remote job IDs, polling, and output assets."""

    def submit(self, prompt: str) -> str: ...

    def status(self, job_id: str) -> JobStatus: ...

    def fetch_output(self, job_id: str, output_index: int) -> tuple[bytes, str]: ...
