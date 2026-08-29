"""Eval harness (PROJECT.md Sections 14 & 17): runs the full investigation
loop against all 4 curated incidents and reports root-cause accuracy,
confidence calibration, grounding pass rate, query efficiency, and cost --
the same shape as project 09's harness, since this project explicitly
mirrors project 09's core justification for agentic (rather than scripted)
investigation.
"""

from __future__ import annotations

from dataclasses import dataclass

from incidentcommander.agent.investigate import InvestigationTrace, run_investigation
from incidentcommander.config import Config
from incidentcommander.data.scenarios import ALL_SCENARIOS
from incidentcommander.llm import LLMClient
from incidentcommander.report.render import save_run
from incidentcommander.telemetry.schemas import IncidentScenario


@dataclass
class IncidentEvalResult:
    scenario: IncidentScenario
    trace: InvestigationTrace
    correct: bool


@dataclass
class EvalSummary:
    results: list[IncidentEvalResult]

    @property
    def accuracy(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.correct) / len(self.results)

    @property
    def grounding_pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if not r.trace.grounding_violations) / len(self.results)

    @property
    def avg_iterations(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.trace.iterations_used for r in self.results) / len(self.results)

    @property
    def total_llm_calls(self) -> int:
        return sum(r.trace.llm_call_count for r in self.results)


def run_eval(llm: LLMClient, config: Config, save_runs: bool = True) -> EvalSummary:
    results: list[IncidentEvalResult] = []
    for scenario in ALL_SCENARIOS:
        trace = run_investigation(llm, config, scenario)
        correct = trace.final_report.root_cause_category.value == scenario.expected_category
        results.append(IncidentEvalResult(scenario=scenario, trace=trace, correct=correct))
        if save_runs:
            save_run(trace, config.runs_dir)
    return EvalSummary(results=results)
