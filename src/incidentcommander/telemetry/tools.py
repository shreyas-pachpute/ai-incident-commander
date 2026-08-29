"""Read-only telemetry query tools (PROJECT.md Section 16: "strictly
read-only... enforced at the tool-registration level"). This module
contains exactly two functions, both pure queries against an in-memory
`IncidentScenario` -- there is no write, execute, restart, rollback, scale,
or deploy function anywhere in this file, or anywhere else in this
codebase (verified by tests/test_no_write_capability.py, which statically
scans the entire package for exactly that).
"""

from __future__ import annotations

from incidentcommander.telemetry.schemas import IncidentScenario, LogEntry, LogLevel, MetricPoint


def query_logs(
    scenario: IncidentScenario,
    level_filter: str | None = None,
    since_minute: int = -60,
    limit: int = 10,
) -> list[LogEntry]:
    """Return log entries at or after `since_minute`, optionally filtered
    by level, most recent first, capped at `limit`.
    """
    results = [log for log in scenario.logs if log.minute >= since_minute]
    if level_filter:
        results = [log for log in results if log.level.value == level_filter.upper()]
    results.sort(key=lambda log: log.minute, reverse=True)
    return results[:limit]


def query_metrics(
    scenario: IncidentScenario,
    metric_name: str,
    since_minute: int = -60,
    limit: int = 12,
) -> list[MetricPoint]:
    """Return metric points for `metric_name` at or after `since_minute`,
    in chronological order, capped at `limit`.
    """
    results = [
        point for point in scenario.metrics
        if point.metric_name == metric_name and point.minute >= since_minute
    ]
    results.sort(key=lambda point: point.minute)
    return results[-limit:]
