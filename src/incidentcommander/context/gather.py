"""Deterministic context assembly (PROJECT.md Section 8: "a fixed
sequence, not agentic reasoning"). Runs before the agent is ever invoked
and costs zero LLM calls: the alert itself, a current metric snapshot, and
every deploy/infra change within the lookback window are handed to the
agent for free -- only deeper log/metric investigation is agentic.
"""

from __future__ import annotations

from dataclasses import dataclass

from incidentcommander.config import Config
from incidentcommander.telemetry.schemas import (
    Alert,
    DeployRecord,
    IncidentScenario,
    InfraChangeRecord,
)


@dataclass(frozen=True)
class MetricSnapshot:
    metric_name: str
    value: float
    minute: int


@dataclass(frozen=True)
class IncidentContext:
    alert: Alert
    current_metrics: list[MetricSnapshot]
    recent_deploys: list[DeployRecord]
    recent_infra_changes: list[InfraChangeRecord]


def _latest_at_or_before(scenario: IncidentScenario, metric_name: str, minute: int) -> MetricSnapshot | None:
    candidates = [p for p in scenario.metrics if p.metric_name == metric_name and p.minute <= minute]
    if not candidates:
        return None
    latest = max(candidates, key=lambda p: p.minute)
    return MetricSnapshot(metric_name=latest.metric_name, value=latest.value, minute=latest.minute)


def gather_context(scenario: IncidentScenario, config: Config) -> IncidentContext:
    metric_names = sorted({p.metric_name for p in scenario.metrics})
    snapshots = [
        snap for snap in (_latest_at_or_before(scenario, name, minute=0) for name in metric_names)
        if snap is not None
    ]

    lookback = -config.context_lookback_minutes
    recent_deploys = sorted(
        (d for d in scenario.deploys if d.minute >= lookback), key=lambda d: d.minute
    )
    recent_infra_changes = sorted(
        (c for c in scenario.infra_changes if c.minute >= lookback), key=lambda c: c.minute
    )

    return IncidentContext(
        alert=scenario.alert,
        current_metrics=snapshots,
        recent_deploys=recent_deploys,
        recent_infra_changes=recent_infra_changes,
    )
