from incidentcommander.data.scenarios import BAD_DEPLOY, INFRA_CHANGE, TRAFFIC_SPIKE
from incidentcommander.telemetry.tools import query_logs, query_metrics


def test_query_logs_filters_by_level():
    results = query_logs(BAD_DEPLOY, level_filter="ERROR", since_minute=-60)
    assert results
    assert all(r.level.value == "ERROR" for r in results)


def test_query_logs_respects_since_minute():
    results = query_logs(BAD_DEPLOY, since_minute=-10)
    assert all(r.minute >= -10 for r in results)
    assert all(r.log_id != "log-1" for r in results)  # log-1 is at minute -20, before the cutoff


def test_query_logs_most_recent_first_and_limit():
    results = query_logs(BAD_DEPLOY, since_minute=-60, limit=2)
    assert len(results) == 2
    assert results[0].minute >= results[1].minute


def test_query_metrics_filters_by_name_and_is_chronological():
    results = query_metrics(TRAFFIC_SPIKE, metric_name="p99_latency_ms", since_minute=-60)
    assert all(r.metric_name == "p99_latency_ms" for r in results)
    minutes = [r.minute for r in results]
    assert minutes == sorted(minutes)


def test_query_metrics_since_minute_excludes_earlier_points():
    results = query_metrics(TRAFFIC_SPIKE, metric_name="request_count", since_minute=-15)
    assert all(r.minute >= -15 for r in results)


def test_query_metrics_limit_keeps_most_recent():
    results = query_metrics(INFRA_CHANGE, metric_name="error_rate_pct", since_minute=-60, limit=2)
    assert len(results) == 2
    all_points = query_metrics(INFRA_CHANGE, metric_name="error_rate_pct", since_minute=-60, limit=100)
    assert results == all_points[-2:]


def test_metric_point_record_id_format():
    results = query_metrics(BAD_DEPLOY, metric_name="error_rate_pct", since_minute=-60, limit=1)
    assert results[0].record_id == f"error_rate_pct@{results[0].minute}"
