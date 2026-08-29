"""CLI entry point: context, investigate, eval."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from incidentcommander.agent.investigate import run_investigation
from incidentcommander.config import load_config
from incidentcommander.context.gather import gather_context
from incidentcommander.data.scenarios import ALL_SCENARIOS, SCENARIOS_BY_ID
from incidentcommander.llm import DailyQuotaExhausted, OllamaUnavailable, build_llm_client
from incidentcommander.report.render import save_run

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)
console = Console()


@app.command()
def context(scenario: str = typer.Option(..., help="Scenario ID, e.g. 'bad_deploy'.")) -> None:
    """Deterministic context assembly for one scenario (zero LLM cost)."""
    if scenario not in SCENARIOS_BY_ID:
        console.print(f"[bold red]Unknown scenario '{scenario}'.[/] Known: {list(SCENARIOS_BY_ID)}")
        raise typer.Exit(code=1)
    config = load_config()
    ctx = gather_context(SCENARIOS_BY_ID[scenario], config)

    console.print(f"[bold]Alert:[/] {ctx.alert.alert_type} on {ctx.alert.service} — {ctx.alert.description}")
    table = Table(title="Current Metric Snapshot")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_column("Minute", justify="right")
    for m in ctx.current_metrics:
        table.add_row(m.metric_name, str(m.value), str(m.minute))
    console.print(table)
    console.print(f"Recent deploys: {[(d.deploy_id, d.minute) for d in ctx.recent_deploys]}")
    console.print(f"Recent infra changes: {[(c.change_id, c.minute) for c in ctx.recent_infra_changes]}")


@app.command()
def investigate(scenario: str = typer.Option(..., help="Scenario ID, e.g. 'bad_deploy'.")) -> None:
    """Run the full bounded cyclic investigation loop for one scenario."""
    if scenario not in SCENARIOS_BY_ID:
        console.print(f"[bold red]Unknown scenario '{scenario}'.[/] Known: {list(SCENARIOS_BY_ID)}")
        raise typer.Exit(code=1)

    config = load_config()
    console.print(f"[bold]Investigating '{scenario}' (LLM provider: {config.llm_provider})...[/]")
    client = build_llm_client(config)
    try:
        trace = run_investigation(client, config, SCENARIOS_BY_ID[scenario])
    except (DailyQuotaExhausted, OllamaUnavailable) as exc:
        console.print(f"[bold red]Stopped: {exc}[/]")
        raise typer.Exit(code=1)

    report = trace.final_report
    console.print(f"\n[bold]Root cause:[/] {report.root_cause_category.value}  [bold]Confidence:[/] {report.confidence}")
    console.print(f"[bold]Expected:[/] {SCENARIOS_BY_ID[scenario].expected_category}")
    console.print(f"[bold]Narrative:[/] {report.narrative}")

    if trace.grounding_violations:
        console.print(f"\n[bold red]Grounding: FAILED[/] — {trace.grounding_violations}")
    else:
        console.print("\n[bold green]Grounding: passed[/]")
    console.print(f"Iterations used: {trace.iterations_used}  LLM calls: {trace.llm_call_count}")

    run_dir = save_run(trace, config.runs_dir)
    console.print(f"Saved to: {run_dir}")


@app.command(name="eval")
def eval_cmd() -> None:
    """Run the full investigation loop against all 4 curated incidents; report accuracy, grounding, and cost."""
    from incidentcommander.eval.harness import run_eval

    config = load_config()
    console.print(f"[bold]Running eval over {len(ALL_SCENARIOS)} incidents (LLM provider: {config.llm_provider})...[/]\n")
    client = build_llm_client(config)
    try:
        summary = run_eval(client, config)
    except (DailyQuotaExhausted, OllamaUnavailable) as exc:
        console.print(f"[bold red]Stopped: {exc}[/]")
        raise typer.Exit(code=1)

    table = Table(title="Eval: Per-Incident Results")
    table.add_column("Scenario")
    table.add_column("Expected")
    table.add_column("Predicted")
    table.add_column("Confidence")
    table.add_column("Iterations", justify="right")
    table.add_column("Grounded")
    for r in summary.results:
        table.add_row(
            r.scenario.scenario_id, r.scenario.expected_category,
            r.trace.final_report.root_cause_category.value, r.trace.final_report.confidence,
            str(r.trace.iterations_used),
            "[green]yes[/]" if not r.trace.grounding_violations else "[red]no[/]",
        )
    console.print(table)

    console.print(f"\n[bold]Root-cause accuracy:[/] {summary.accuracy:.0%}")
    console.print(f"[bold]Grounding pass rate:[/] {summary.grounding_pass_rate:.0%}")
    console.print(f"[bold]Avg iterations used:[/] {summary.avg_iterations:.1f}")
    console.print(f"[bold]Total LLM calls:[/] {summary.total_llm_calls}")


if __name__ == "__main__":
    app()
