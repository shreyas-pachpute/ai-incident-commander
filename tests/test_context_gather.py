from incidentcommander.config import Config
from incidentcommander.context.gather import gather_context
from incidentcommander.data.scenarios import BAD_DEPLOY, INFRA_CHANGE, TRAFFIC_SPIKE

_CONFIG = Config(gemini_api_key="unused-in-tests")


def test_bad_deploy_context_includes_the_deploy_and_correct_snapshot():
    ctx = gather_context(BAD_DEPLOY, _CONFIG)
    assert [d.deploy_id for d in ctx.recent_deploys] == ["deploy-501"]
    assert ctx.recent_infra_changes == []
    snapshot = {m.metric_name: m.value for m in ctx.current_metrics}
    assert snapshot["error_rate_pct"] == 19.0  # latest point at or before minute 0
    assert snapshot["p99_latency_ms"] == 230.0


def test_infra_change_context_includes_the_change_not_a_deploy():
    ctx = gather_context(INFRA_CHANGE, _CONFIG)
    assert ctx.recent_deploys == []
    assert [c.change_id for c in ctx.recent_infra_changes] == ["infra-301"]


def test_traffic_spike_context_has_no_deploys_or_infra_changes():
    ctx = gather_context(TRAFFIC_SPIKE, _CONFIG)
    assert ctx.recent_deploys == []
    assert ctx.recent_infra_changes == []
    snapshot = {m.metric_name: m.value for m in ctx.current_metrics}
    assert snapshot["request_count"] == 2600.0


def test_lookback_window_excludes_deploys_outside_it():
    config = Config(gemini_api_key="unused-in-tests", context_lookback_minutes=5)
    ctx = gather_context(BAD_DEPLOY, config)  # deploy-501 is at minute -12
    assert ctx.recent_deploys == []


def test_snapshot_never_uses_a_metric_point_after_alert_time():
    ctx = gather_context(BAD_DEPLOY, _CONFIG)
    # BAD_DEPLOY has an error_rate_pct point at minute 3 (19.5), after the
    # alert -- the snapshot must not leak future data into minute-0 context.
    snapshot = {m.metric_name: m.minute for m in ctx.current_metrics}
    assert snapshot["error_rate_pct"] <= 0
