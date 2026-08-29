"""Renders an investigation trace to JSON (full audit trail, PROJECT.md
Section 18 -- real-time coordination + postmortem reconstruction) and
Markdown (the incident-channel-facing summary).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from incidentcommander.agent.investigate import InvestigationTrace


def trace_to_dict(trace: InvestigationTrace) -> dict:
    return {
        "run_id": trace.run_id,
        "scenario_id": trace.scenario_id,
        "alert": dataclasses.asdict(trace.context.alert),
        "steps": [dataclasses.asdict(s) for s in trace.steps],
        "final_report": trace.final_report.model_dump(mode="json"),
        "grounding_violations": trace.grounding_violations,
        "iterations_used": trace.iterations_used,
        "llm_call_count": trace.llm_call_count,
        "llm_prompt_tokens": trace.llm_prompt_tokens,
        "llm_output_tokens": trace.llm_output_tokens,
    }


def render_markdown(trace: InvestigationTrace) -> str:
    report = trace.final_report
    lines = [
        f"# Incident Investigation — {trace.context.alert.alert_id} ({trace.context.alert.service})",
        "",
        f"**Run ID:** {trace.run_id}",
        f"**Alert type:** {trace.context.alert.alert_type}",
        f"**Grounding:** {'PASSED' if not trace.grounding_violations else 'FAILED — ' + '; '.join(trace.grounding_violations)}",
        "",
        f"## {report.scenario_summary}",
        "",
        f"**Root cause category:** {report.root_cause_category.value}",
        f"**Confidence:** {report.confidence}",
        "",
        f"**Narrative:** {report.narrative}",
        "",
        "**Evidence:**",
    ]
    for e in report.evidence:
        lines.append(f"  - ({e.kind}:{e.record_id}) {e.note}")
    lines.append("")
    lines.append("**Ruled out:**")
    for item in report.ruled_out:
        lines.append(f"  - {item}")
    lines.append("")
    lines.append("**Recommended remediation (for human review — not executed):**")
    for item in report.recommended_remediation:
        lines.append(f"  - {item}")

    lines += [
        "",
        "## Investigation Trace",
    ]
    for s in trace.steps:
        lines.append(f"- Round {s.iteration}: {s.action} ({s.params}) -> {s.result_count} result(s). Reasoning: {s.reasoning}")

    lines += [
        "",
        "## Observability",
        f"- Iterations used: {trace.iterations_used}",
        f"- LLM calls: {trace.llm_call_count}",
        f"- Prompt tokens: {trace.llm_prompt_tokens}, Output tokens: {trace.llm_output_tokens}",
    ]
    return "\n".join(lines)


def save_run(trace: InvestigationTrace, runs_dir: Path) -> Path:
    run_dir = runs_dir / trace.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "trace.json").write_text(json.dumps(trace_to_dict(trace), indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(render_markdown(trace), encoding="utf-8")
    return run_dir
