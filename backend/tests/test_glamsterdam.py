from pathlib import Path

from app.models.schemas import Finding, Severity
from app.services import glamsterdam
from app.services.report import generate_sarif


def _write_readiness_source(tmp_path: Path, name: str = "Readiness.sol") -> Path:
    source = tmp_path / name
    source.write_text(
        "\n".join(
            [
                "// SPDX-License-Identifier: MIT",
                "pragma solidity ^0.8.20;",
                "contract Readiness {",
                "  function pay(address payable to) external {",
                "    to.transfer(address(this).balance);",
                "  }",
                "  function draw() external view returns (bool) {",
                "    return block.timestamp % 2 == 0;",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    return source


def test_scan_project_detects_glamsterdam_readiness_patterns(tmp_path: Path):
    source = tmp_path / "Readiness.sol"
    source.write_text(
        "\n".join(
            [
                "// SPDX-License-Identifier: MIT",
                "pragma solidity ^0.8.20;",
                "contract Readiness {",
                "  receive() external payable {}",
                "  function pay(address payable to) external {",
                "    to.transfer(address(this).balance);",
                "  }",
                "  function draw() external view returns (bool) {",
                "    return block.timestamp % 2 == 0;",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    findings = glamsterdam.scan_project(tmp_path)

    detectors = {finding.detector for finding in findings}
    assert "glamsterdam-eth-transfer-assumption" in detectors
    assert "glamsterdam-block-context" in detectors
    assert all(finding.ai.manual_review_required for finding in findings)


def test_scan_project_findings_carry_rule_metadata(tmp_path: Path):
    _write_readiness_source(tmp_path)

    findings = glamsterdam.scan_project(tmp_path)
    by_detector = {finding.detector: finding for finding in findings}

    transfer = by_detector["glamsterdam-eth-transfer-assumption"]
    assert transfer.rule_confidence == "medium"
    assert transfer.rule_rationale
    assert any("EIP-7708" in eip for eip in transfer.related_eips)

    block_context = by_detector["glamsterdam-block-context"]
    assert block_context.rule_confidence == "medium"
    assert any("EIP-7732" in eip for eip in block_context.related_eips)
    assert any("EIP-7928" in eip for eip in block_context.related_eips)


def test_inline_suppression_marker_skips_matches(tmp_path: Path):
    source = tmp_path / "Suppressed.sol"
    source.write_text(
        "\n".join(
            [
                "pragma solidity ^0.8.20;",
                "contract Suppressed {",
                "  function pay(address payable to) external {",
                "    to.transfer(1 ether); // glamsterdam-ignore",
                "  }",
                "  function draw() external view returns (bool) {",
                "    return block.timestamp % 2 == 0; // glamsterdam-ignore: glamsterdam-block-context",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    findings = glamsterdam.scan_project(tmp_path)

    assert findings == []


def test_inline_suppression_with_other_detector_keeps_match(tmp_path: Path):
    source = tmp_path / "Partial.sol"
    source.write_text(
        "\n".join(
            [
                "pragma solidity ^0.8.20;",
                "contract Partial {",
                "  function draw() external view returns (bool) {",
                "    return block.timestamp % 2 == 0; // glamsterdam-ignore: glamsterdam-gas-sensitive-loop",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    findings = glamsterdam.scan_project(tmp_path)

    assert [finding.detector for finding in findings] == ["glamsterdam-block-context"]


def test_baseline_file_suppresses_matches(tmp_path: Path):
    _write_readiness_source(tmp_path)
    (tmp_path / "glamsterdam-baseline.json").write_text(
        '{"suppressions": [{"detector": "glamsterdam-eth-transfer-assumption"}]}',
        encoding="utf-8",
    )

    findings = glamsterdam.scan_project(tmp_path)
    detectors = {finding.detector for finding in findings}

    assert "glamsterdam-eth-transfer-assumption" not in detectors
    assert "glamsterdam-block-context" in detectors


def test_generate_readiness_report_marks_manual_review(tmp_path: Path):
    finding = Finding(
        id="glamsterdam-1",
        detector="glamsterdam-eth-transfer-assumption",
        severity=Severity.LOW,
        description="Native ETH transfer assumption.",
        file="Readiness.sol",
        line=6,
        source="readiness-heuristic",
        rule_confidence="medium",
        rule_rationale="Fixed gas stipend assumptions.",
        related_eips=["EIP-7708 (ETH transfers emit a log, candidate)"],
    )

    report = glamsterdam.generate_readiness_report("demo", [finding])

    assert "Glamsterdam Solidity Readiness Report" in report
    assert "Manual review required" in report
    assert "not a protocol compatibility guarantee" in report
    assert "Slither findings are published separately" in report
    assert "Rule confidence**: medium" in report
    assert "Fixed gas stipend assumptions." in report
    assert "EIP-7708" in report
    assert "Summary by detector" in report
    assert "Tuning and suppression" in report
    assert "glamsterdam-baseline.json" in report
    assert "EIP-7773" in report


def test_generate_readiness_report_excludes_slither_findings():
    slither_finding = Finding(
        id="finding-1",
        detector="reentrancy-eth",
        severity=Severity.HIGH,
        description="Reentrancy in withdraw",
        file="Readiness.sol",
        line=5,
        source="slither",
    )
    readiness_finding = Finding(
        id="glamsterdam-1",
        detector="glamsterdam-eth-transfer-assumption",
        severity=Severity.LOW,
        description="Native ETH transfer assumption.",
        file="Readiness.sol",
        line=6,
        source="readiness-heuristic",
    )

    report = glamsterdam.generate_readiness_report("demo", [slither_finding, readiness_finding])

    assert "glamsterdam-eth-transfer-assumption" in report
    assert "reentrancy-eth" not in report


def test_generate_sarif_accepts_glamsterdam_tags():
    finding = Finding(
        id="glamsterdam-1",
        detector="glamsterdam-block-context",
        severity=Severity.INFORMATIONAL,
        description="Block context dependency.",
        file="Readiness.sol",
        line=9,
        source="readiness-heuristic",
    )

    sarif = generate_sarif([finding], readiness_tags=["glamsterdam", "gas-repricing"])
    rule = sarif["runs"][0]["tool"]["driver"]["rules"][0]
    result = sarif["runs"][0]["results"][0]
    tags = rule["properties"]["tags"]

    assert "glamsterdam" in tags
    assert "gas-repricing" in tags
    assert "readiness-heuristic" in tags
    assert "slither" not in tags
    assert rule["properties"]["tool"] == "AISolidityAuditor-GlamsterdamReadiness"
    assert rule["properties"]["source"] == "readiness-heuristic"
    assert result["properties"]["tool"] == "AISolidityAuditor-GlamsterdamReadiness"
    assert "Glamsterdam readiness heuristic" in rule["fullDescription"]["text"]


def test_scan_project_skips_non_file_sol_paths(tmp_path: Path):
    source_dir = tmp_path / "Auth.sol"
    source_dir.mkdir()
    real_file = tmp_path / "Real.sol"
    real_file.write_text(
        "\n".join(
            [
                "pragma solidity ^0.8.20;",
                "contract Real { function f() external { block.timestamp; } }",
            ]
        ),
        encoding="utf-8",
    )

    findings = glamsterdam.scan_project(tmp_path)

    assert len(findings) == 1
    assert findings[0].detector == "glamsterdam-block-context"


def test_scan_project_ignores_comments_and_string_literals(tmp_path: Path):
    source = tmp_path / "Noisy.sol"
    source.write_text(
        "\n".join(
            [
                "// SPDX-License-Identifier: MIT",
                "pragma solidity ^0.8.20;",
                "contract Noisy {",
                '  string public note = "block.timestamp in docs";',
                "  // avoid block.timestamp in production",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    findings = glamsterdam.scan_project(tmp_path)

    assert findings == []
