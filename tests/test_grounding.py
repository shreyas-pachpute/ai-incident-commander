from incidentcommander.agent.grounding import validate_grounding
from incidentcommander.agent.schemas import EvidenceCitation, RootCauseReport


def _report(evidence, confidence="high") -> RootCauseReport:
    return RootCauseReport(
        scenario_summary="s", root_cause_category="bad_deploy", confidence=confidence,
        narrative="n", evidence=evidence, ruled_out=[], recommended_remediation=["roll back the deploy"],
    )


def test_grounded_evidence_passes():
    report = _report([EvidenceCitation(kind="log", record_id="log-3", note="n")])
    assert validate_grounding(report, {"log-3"}) == []


def test_hallucinated_record_id_flagged():
    report = _report([EvidenceCitation(kind="log", record_id="log-99", note="n")])
    violations = validate_grounding(report, {"log-3"})
    assert len(violations) == 1
    assert "log-99" in violations[0]


def test_high_confidence_with_zero_evidence_flagged():
    report = _report([], confidence="high")
    violations = validate_grounding(report, {"log-3"})
    assert any("zero evidence" in v for v in violations)


def test_low_confidence_with_zero_evidence_is_allowed():
    report = _report([], confidence="low")
    assert validate_grounding(report, {"log-3"}) == []


def test_multiple_citations_all_checked_independently():
    report = _report([
        EvidenceCitation(kind="deploy", record_id="deploy-501", note="n"),
        EvidenceCitation(kind="log", record_id="log-99", note="n"),
    ])
    violations = validate_grounding(report, {"deploy-501"})
    assert len(violations) == 1
    assert "log-99" in violations[0]
