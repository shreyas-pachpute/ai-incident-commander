"""Agent I/O schemas. PROJECT.md Section 6/16: the agent investigates and
recommends, it never executes -- `RootCauseReport` has no field capable of
representing an executed action (no `action_taken`, no `status` other than
diagnostic fields). `recommended_remediation` is plain-text suggestions
only, structurally incapable of being a tool call. This is the schema-level
half of the enforcement; tests/test_no_write_capability.py is the other
half (no write/execute function exists anywhere in the codebase to call).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class RootCauseCategory(StrEnum):
    BAD_DEPLOY = "bad_deploy"
    TRAFFIC_SPIKE = "traffic_spike"
    DEPENDENCY_FAILURE = "dependency_failure"
    INFRA_CHANGE = "infra_change"
    UNKNOWN = "unknown"


class InvestigationStep(BaseModel):
    action: Literal["query_logs", "query_metrics", "conclude"] = Field(
        description="The next read-only investigative action, or 'conclude' if there's enough evidence to write the final report."
    )
    reasoning: str = Field(description="Why this action, given the evidence gathered so far.")
    level_filter: str | None = Field(
        default=None, description="Only used when action='query_logs'. One of 'ERROR', 'WARN', 'INFO', or null for all levels."
    )
    metric_name: str | None = Field(
        default=None, description="Only used when action='query_metrics'. e.g. 'error_rate_pct', 'p99_latency_ms', 'request_count'."
    )


class EvidenceCitation(BaseModel):
    kind: Literal["log", "metric", "deploy", "infra_change"]
    record_id: str = Field(description="The exact record ID (log_id, metric record_id, deploy_id, or change_id) this evidence cites.")
    note: str = Field(description="What this record shows and why it matters to the diagnosis.")


class RootCauseReport(BaseModel):
    scenario_summary: str = Field(description="1-2 sentence plain-language description of what's happening.")
    root_cause_category: RootCauseCategory
    confidence: Literal["high", "medium", "low"]
    narrative: str = Field(description="The evidence-backed explanation of the likely root cause.")
    evidence: list[EvidenceCitation]
    ruled_out: list[str] = Field(description="Other categories considered and why they were ruled out, or an empty list if investigation is still early.")
    recommended_remediation: list[str] = Field(
        description="Plain-language remediation suggestions for a human engineer to evaluate and execute -- never a tool call or command."
    )
