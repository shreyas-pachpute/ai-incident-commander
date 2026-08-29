"""Central configuration. PROJECT.md Section 8: initial context assembly
(alert, metric snapshot, recent deploys/infra changes) is a fixed
deterministic sequence -- only the follow-up log/metric investigation is
agentic, bounded by max_iterations below.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Config:
    gemini_api_key: str | None
    llm_provider: str = os.environ.get("LLM_PROVIDER", "gemini")
    gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    ollama_model: str = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
    ollama_base_url: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    runs_dir: Path = PROJECT_ROOT / "runs"

    # Bounded cyclic investigation loop (PROJECT.md Section 24: "genuinely
    # cyclic, stateful" but cost-frugal -- max_iterations rounds of
    # propose-a-query/evaluate, then one final synthesis call.
    max_iterations: int = 3
    max_log_results: int = 10
    max_metric_points: int = 12

    # Deterministic context-assembly lookback window (minutes before the
    # alert to search for recent deploys/infra changes).
    context_lookback_minutes: int = 60

    max_retries: int = 5
    initial_backoff_seconds: float = 2.0
    ollama_timeout_seconds: float = 240.0


def load_config() -> Config:
    provider = os.environ.get("LLM_PROVIDER", "gemini")
    api_key = os.environ.get("GEMINI_API_KEY")
    if provider == "gemini" and not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env in the project root.")
    return Config(gemini_api_key=api_key)
