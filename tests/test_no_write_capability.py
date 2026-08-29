"""The adversarial/structural safety test (PROJECT.md Section 24: "verified
by adversarial testing, not just documented as policy"; Section 17:
"explicit red-team testing confirming the agent cannot be prompted... into
attempting a production action"). This statically scans every .py file in
the package for:

1. Any function whose name suggests a state-changing production capability
   (restart, rollback, deploy, scale, patch, shutdown, etc.) -- there
   should be none, because the correct design (Section 11) is that the
   capability is never built, not that it exists behind a permission check.
2. Any call to subprocess/os.system/eval/exec -- the only way this
   codebase could ever reach outside its own synthetic in-memory data.
3. That the agent's structured output schema (RootCauseReport) has no
   field capable of representing an executed action.

This is the same class of proof as project 10's architectural-separation
test and project 06's sandbox policy tests, applied to "no write capability
exists at all" rather than "no write capability is reachable."
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "incidentcommander"

_FORBIDDEN_FUNCTION_NAME_RE = (
    "restart", "rollback", "redeploy", "scale", "reconfigure", "shutdown",
    "reboot", "terminate", "provision", "deprovision", "apply_change",
    "write_config", "execute_command", "run_command",
)
_FORBIDDEN_CALL_TARGETS = {"system", "popen", "run", "Popen", "call", "check_call", "check_output"}
_FORBIDDEN_BUILTIN_CALLS = {"eval", "exec", "compile"}
_FORBIDDEN_IMPORTS = {"subprocess"}


def _all_py_files() -> list[Path]:
    return sorted(SRC_ROOT.rglob("*.py"))


@pytest.mark.parametrize("path", _all_py_files(), ids=lambda p: str(p.relative_to(SRC_ROOT)))
def test_no_state_changing_function_defined(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lowered = node.name.lower()
            hits = [pat for pat in _FORBIDDEN_FUNCTION_NAME_RE if pat in lowered]
            assert not hits, f"{path.name}: function '{node.name}' matches forbidden pattern(s) {hits}"


@pytest.mark.parametrize("path", _all_py_files(), ids=lambda p: str(p.relative_to(SRC_ROOT)))
def test_no_subprocess_or_dynamic_exec_calls(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in _FORBIDDEN_IMPORTS, f"{path.name}: forbidden import '{alias.name}'"
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _FORBIDDEN_BUILTIN_CALLS:
                pytest.fail(f"{path.name}: forbidden call to builtin '{func.id}'")
            if isinstance(func, ast.Attribute) and func.attr in _FORBIDDEN_CALL_TARGETS:
                pytest.fail(f"{path.name}: forbidden call '.{func.attr}(...)'")


def test_root_cause_report_schema_has_no_action_taken_field():
    from incidentcommander.agent.schemas import RootCauseReport

    field_names = set(RootCauseReport.model_fields)
    forbidden = {"action_taken", "executed", "action_performed", "remediation_executed", "status"}
    assert not (field_names & forbidden), (
        f"RootCauseReport has field(s) {field_names & forbidden} that could represent an executed "
        "action -- this schema must only ever be able to describe a diagnosis and a suggestion."
    )


def test_telemetry_tools_module_exposes_exactly_the_two_read_only_functions():
    from incidentcommander.telemetry import tools

    public_functions = {
        name for name in dir(tools)
        if callable(getattr(tools, name)) and not name.startswith("_")
        and getattr(getattr(tools, name), "__module__", "") == tools.__name__
    }
    assert public_functions == {"query_logs", "query_metrics"}
