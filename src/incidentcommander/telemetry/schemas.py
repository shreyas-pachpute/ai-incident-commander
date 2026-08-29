"""Synthetic telemetry data model for a single well-instrumented service
(PROJECT.md Section 21 MVP scope). Timestamps are integer minutes relative
to the alert (t=0 is when the alert fired, negative is before) -- this
keeps the synthetic dataset and every test trivially exact, and is purely
an implementation simplification of "real" ISO timestamps, not a product
decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LogLevel(StrEnum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass(frozen=True)
class LogEntry:
    log_id: str
    minute: int
    level: LogLevel
    message: str


@dataclass(frozen=True)
class MetricPoint:
    metric_name: str
    minute: int
    value: float

    @property
    def record_id(self) -> str:
        return f"{self.metric_name}@{self.minute}"


@dataclass(frozen=True)
class DeployRecord:
    deploy_id: str
    minute: int
    version: str
    description: str


@dataclass(frozen=True)
class InfraChangeRecord:
    change_id: str
    minute: int
    description: str


@dataclass(frozen=True)
class Alert:
    alert_id: str
    service: str
    alert_type: str
    description: str


@dataclass(frozen=True)
class IncidentScenario:
    """One self-contained synthetic incident: an alert plus the full
    telemetry universe a real observability stack would hold for it. The
    investigation agent only ever sees what it queries -- `expected_category`
    and `expected_ruled_out` are ground truth used solely by eval/harness.py,
    never fed to the agent.
    """

    scenario_id: str
    alert: Alert
    logs: list[LogEntry]
    metrics: list[MetricPoint]
    deploys: list[DeployRecord]
    infra_changes: list[InfraChangeRecord]
    expected_category: str
