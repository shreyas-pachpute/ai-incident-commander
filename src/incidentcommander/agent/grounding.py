"""Deterministic grounding validation (PROJECT.md Section 6: "every claim
in the investigation summary traces to a specific log line, metric value,
or change record"). Every evidence citation's record_id must be one the
investigation actually saw -- in the initial deterministic context or in a
query result during the loop -- or it's flagged as a hallucinated citation.
"""

from __future__ import annotations

from incidentcommander.agent.schemas import RootCauseReport


def validate_grounding(report: RootCauseReport, seen_record_ids: set[str]) -> list[str]:
    violations: list[str] = []

    for citation in report.evidence:
        if citation.record_id not in seen_record_ids:
            violations.append(
                f"Evidence cites record_id '{citation.record_id}' ({citation.kind}), which was never "
                "returned by any query or present in the initial context."
            )

    if not report.evidence and report.confidence != "low":
        violations.append(
            f"Report cites zero evidence but claims '{report.confidence}' confidence -- "
            "a conclusion with no supporting evidence should never be reported above low confidence."
        )

    return violations
