"""The Incident Investigation Agent: a genuinely cyclic, bounded loop
(PROJECT.md Section 24) where each round's query depends on what the prior
round found, up to `config.max_iterations` rounds, followed by one final
synthesis call. Deterministic context assembly happens first and costs
zero LLM calls (Section 8).

No function in this module -- or anywhere else in this codebase -- can
modify production state; `query_logs`/`query_metrics` (telemetry/tools.py)
are the only tools available, both pure reads.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from incidentcommander.agent.grounding import validate_grounding
from incidentcommander.agent.prompts import (
    SYSTEM_INSTRUCTION,
    final_report_prompt,
    render_log_results,
    render_metric_results,
    step_prompt,
)
from incidentcommander.agent.schemas import InvestigationStep, RootCauseReport
from incidentcommander.config import Config
from incidentcommander.context.gather import IncidentContext, gather_context
from incidentcommander.llm import LLMClient
from incidentcommander.telemetry.schemas import IncidentScenario
from incidentcommander.telemetry.tools import query_logs, query_metrics


@dataclass
class StepLogEntry:
    iteration: int
    action: str
    reasoning: str
    params: dict
    result_count: int


@dataclass
class InvestigationTrace:
    run_id: str
    scenario_id: str
    context: IncidentContext
    steps: list[StepLogEntry]
    final_report: RootCauseReport
    grounding_violations: list[str]
    iterations_used: int
    llm_call_count: int
    llm_prompt_tokens: int
    llm_output_tokens: int


def run_investigation(llm: LLMClient, config: Config, scenario: IncidentScenario) -> InvestigationTrace:
    context = gather_context(scenario, config)

    seen_record_ids: set[str] = (
        {d.deploy_id for d in context.recent_deploys}
        | {c.change_id for c in context.recent_infra_changes}
        | {f"{m.metric_name}@{m.minute}" for m in context.current_metrics}
    )
    evidence_log: list[str] = []
    steps: list[StepLogEntry] = []
    iterations_used = 0

    for iteration in range(1, config.max_iterations + 1):
        iterations_used = iteration
        step: InvestigationStep = llm.generate_structured(
            SYSTEM_INSTRUCTION,
            step_prompt(context, evidence_log, iteration, config.max_iterations),
            InvestigationStep,
        )

        if step.action == "conclude":
            steps.append(StepLogEntry(iteration, "conclude", step.reasoning, {}, 0))
            break

        if step.action == "query_logs":
            results = query_logs(
                scenario, level_filter=step.level_filter,
                since_minute=-config.context_lookback_minutes, limit=config.max_log_results,
            )
            evidence_log.append(
                f"Round {iteration} -- query_logs(level_filter={step.level_filter}). "
                f"Reasoning: {step.reasoning}\n{render_log_results(results)}"
            )
            seen_record_ids |= {r.log_id for r in results}
            steps.append(StepLogEntry(iteration, "query_logs", step.reasoning, {"level_filter": step.level_filter}, len(results)))
        else:  # query_metrics
            metric_name = step.metric_name or "error_rate_pct"
            results = query_metrics(
                scenario, metric_name,
                since_minute=-config.context_lookback_minutes, limit=config.max_metric_points,
            )
            evidence_log.append(
                f"Round {iteration} -- query_metrics(metric_name={metric_name}). "
                f"Reasoning: {step.reasoning}\n{render_metric_results(results)}"
            )
            seen_record_ids |= {r.record_id for r in results}
            steps.append(StepLogEntry(iteration, "query_metrics", step.reasoning, {"metric_name": metric_name}, len(results)))

    final_report: RootCauseReport = llm.generate_structured(
        SYSTEM_INSTRUCTION, final_report_prompt(context, evidence_log), RootCauseReport
    )
    violations = validate_grounding(final_report, seen_record_ids)

    return InvestigationTrace(
        run_id=uuid.uuid4().hex[:12],
        scenario_id=scenario.scenario_id,
        context=context,
        steps=steps,
        final_report=final_report,
        grounding_violations=violations,
        iterations_used=iterations_used,
        llm_call_count=llm.call_count,
        llm_prompt_tokens=llm.prompt_tokens,
        llm_output_tokens=llm.output_tokens,
    )
