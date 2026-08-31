from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out" 

class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"

    @property
    def rank(self) -> int:
        """For sorting worst-first."""
        return {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFORMATIONAL: 4,
        }[self]


class Vulnerability(BaseModel):
    # ignore any extra keys the model invents rather than rejecting the
    # whole report over one stray field
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    severity: Severity
    description: str = Field(min_length=1, max_length=10_000)
    file: str = Field(min_length=1, max_length=500)
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    impact: str | None = Field(default=None, max_length=5_000)
    recommendation: str | None = Field(default=None, max_length=5_000)
    poc: str | None = Field(default=None, max_length=20_000)
    verified: bool = False
    verification: str | None = Field(default=None, max_length=5_000)

    @field_validator("file")
    @classmethod
    def no_path_escape(cls, v: str) -> str:
        """The agent may only point at files inside the uploaded bundle.

        Without this, a report could name ../../etc/passwd and the frontend
        would happily try to open it.
        """
        if v.startswith("/") or ".." in v.split("/"):
            raise ValueError(f"file must be a relative path inside the bundle: {v}")
        return v

    @field_validator("end_line")
    @classmethod
    def end_after_start(cls, v: int | None, info) -> int | None:
        start = info.data.get("start_line")
        if v is not None and start is not None and v < start:
            raise ValueError("end_line cannot be before start_line")
        return v


class Report(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vulnerabilities: list[Vulnerability] = Field(default_factory=list, max_length=500)
    summary: str | None = Field(default=None, max_length=10_000)

    @property
    def counts(self) -> dict[str, int]:
        """How many findings per severity, for the UI badges."""
        out = {s.value: 0 for s in Severity}
        for v in self.vulnerabilities:
            out[v.severity.value] += 1
        return out

    @property
    def missing_proofs(self) -> list[str]:
        """Findings claimed verified that carry no test source.

        The proof is why the second stage exists. If it does not survive
        into the report, the finding is an assertion again and there is
        nothing to score it on.
        """
        return [v.title for v in self.vulnerabilities if v.verified and not v.poc]

    @property
    def unlocated(self) -> list[str]:
        """Findings with no usable file path -- unscoreable, unfixable."""
        return [
            v.title for v in self.vulnerabilities
            if not v.file or v.file.strip().lower() in {"unknown", "n/a", "-"}
        ]

    @property
    def verified_count(self) -> int:
        """How many findings came with a Foundry test that passed."""
        return sum(1 for v in self.vulnerabilities if v.verified)

    def sorted_findings(self) -> list[Vulnerability]:
        """Worst first, and within a severity, proven before merely claimed."""
        return sorted(
            self.vulnerabilities,
            key=lambda v: (v.severity.rank, not v.verified, v.file),
        )


@dataclass 
class Job:
    id: str
    status: JobStatus
    model: str
    upload_path: str
    container_id: str | None
    created_at: str
    started_at: str | None
    finished_at: str | None
    error: str | None
    report: Report | None

    # spend, tracked by the proxy
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = field(default_factory=lambda: Decimal(0))
    budget_usd: Decimal = field(default_factory=lambda: Decimal("50.0"))


class JobResponse(BaseModel):
    """Public job view. Omits host-local fields (upload_path, container_id)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: JobStatus
    model: str
    created_at: str
    started_at: str | None
    finished_at: str | None
    error: str | None
    report: Report | None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal(0)
    budget_usd: Decimal = Decimal("50.0")

    @classmethod
    def from_job(cls, job: Job) -> "JobResponse":
        return cls.model_validate(job)


class JobHistoryResponse(BaseModel):
    jobs: list[JobResponse]
    limit: int
    offset: int
    count: int
