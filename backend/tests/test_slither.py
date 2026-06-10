from app.models.schemas import Severity
from app.services.slither import parse_slither_results


def test_parse_slither_results(slither_raw):
    findings = parse_slither_results(slither_raw)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.detector == "reentrancy-eth"
    assert finding.severity == Severity.HIGH
    assert finding.contract == "VulnerableBank"
    assert finding.function == "withdraw"
    assert finding.file == "Reentrancy.sol"
    assert finding.line == 15
    assert "Reentrancy" in finding.description


def test_parse_empty_results():
    findings = parse_slither_results({"results": {"detectors": []}})
    assert findings == []


def test_parse_sorts_by_severity():
    raw = {
        "results": {
            "detectors": [
                {"check": "low-issue", "impact": "Low", "description": "low", "elements": []},
                {"check": "high-issue", "impact": "High", "description": "high", "elements": []},
                {"check": "med-issue", "impact": "Medium", "description": "med", "elements": []},
            ]
        }
    }
    findings = parse_slither_results(raw)
    assert [f.severity for f in findings] == [
        Severity.HIGH,
        Severity.MEDIUM,
        Severity.LOW,
    ]
