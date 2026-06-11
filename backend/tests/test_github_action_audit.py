import asyncio
import importlib.util
import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.models.schemas import Finding, Severity

GLAMSTERDAM_SARIF_TAGS = [
    "glamsterdam",
    "gas-repricing",
    "evm-compatibility",
    "eth-transfer-logs",
    "contract-size",
]

READINESS_CONTRACT = "\n".join(
    [
        "// SPDX-License-Identifier: MIT",
        "pragma solidity ^0.8.20;",
        "contract Readiness {",
        "  function pay(address payable to) external {",
        "    to.transfer(1 ether);",
        "  }",
        "  function draw() external view returns (bool) {",
        "    return block.timestamp % 2 == 0;",
        "  }",
        "}",
    ]
)


def _load_action_module():
    script = Path(__file__).resolve().parents[2] / "scripts" / "github_action_audit.py"
    spec = importlib.util.spec_from_file_location("github_action_audit", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_args(
    project: Path,
    output_dir: Path,
    mode: str,
    readiness_project: Path | None = None,
) -> Namespace:
    return Namespace(
        project=project,
        readiness_project=readiness_project,
        output_dir=output_dir,
        ai_provider="openai",
        mode=mode,
        openai_api_key="",
        anthropic_api_key="",
        deepseek_api_key="",
        max_ai_findings=20,
        include_informational="true",
        fail_on_high="false",
        fail_on_medium="false",
    )


def _run_action_audit(module, args: Namespace, slither_findings: list[Finding]) -> None:
    mock_raw = {"results": {"detectors": []}}
    with patch.object(module.slither, "run_slither", return_value=mock_raw):
        with patch.object(module.slither, "parse_slither_results", return_value=slither_findings):
            with patch.object(module.source_context, "attach_source_context"):
                with patch.object(
                    module.ai,
                    "explain_findings",
                    new=AsyncMock(return_value=slither_findings),
                ):
                    asyncio.run(module.run_action_audit(args))


def _sarif_rules_by_id(sarif: dict) -> dict[str, dict]:
    return {rule["id"]: rule for rule in sarif["runs"][0]["tool"]["driver"]["rules"]}


def test_parse_bool_accepts_common_true_values():
    module = _load_action_module()

    assert module._parse_bool("true") is True
    assert module._parse_bool("1") is True
    assert module._parse_bool("yes") is True
    assert module._parse_bool("false") is False


def test_filter_findings_can_drop_informational_and_optimization():
    module = _load_action_module()
    findings = [
        Finding(id="high", detector="high", severity=Severity.HIGH, description="high"),
        Finding(id="info", detector="info", severity=Severity.INFORMATIONAL, description="info"),
        Finding(id="opt", detector="opt", severity=Severity.OPTIMIZATION, description="opt"),
    ]

    filtered = module._filter_findings(findings, include_informational=False)

    assert [finding.id for finding in filtered] == ["high"]


def test_run_action_audit_standard_mode_writes_slither_only_artifacts(tmp_path: Path):
    module = _load_action_module()
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "Readiness.sol").write_text(READINESS_CONTRACT, encoding="utf-8")
    output_dir = tmp_path / "results"
    slither_finding = Finding(
        id="finding-1",
        detector="reentrancy-eth",
        severity=Severity.HIGH,
        description="Reentrancy in withdraw",
        file="Readiness.sol",
        line=5,
    )

    _run_action_audit(module, _make_args(project, output_dir, "standard"), [slither_finding])

    assert (output_dir / "audit-report.md").is_file()
    assert (output_dir / "findings.json").is_file()
    assert (output_dir / "audit-results.sarif").is_file()
    assert not (output_dir / "glamsterdam-readiness-report.md").exists()
    assert not (output_dir / "glamsterdam-findings.json").exists()

    findings_payload = json.loads((output_dir / "findings.json").read_text(encoding="utf-8"))
    rules = _sarif_rules_by_id(json.loads((output_dir / "audit-results.sarif").read_text(encoding="utf-8")))

    assert findings_payload == [finding.model_dump(mode="json") for finding in [slither_finding]]
    assert all(item["source"] == "slither" for item in findings_payload)
    assert "reentrancy-eth" in rules
    assert rules["reentrancy-eth"]["properties"]["tool"] == "Slither"
    assert "glamsterdam" not in rules["reentrancy-eth"]["properties"]["tags"]


def test_run_action_audit_glamsterdam_readiness_end_to_end(tmp_path: Path):
    module = _load_action_module()
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "Readiness.sol").write_text(READINESS_CONTRACT, encoding="utf-8")
    output_dir = tmp_path / "results"
    slither_finding = Finding(
        id="finding-1",
        detector="reentrancy-eth",
        severity=Severity.HIGH,
        description="Reentrancy in withdraw",
        file="Readiness.sol",
        line=5,
    )

    _run_action_audit(
        module,
        _make_args(project, output_dir, "glamsterdam-readiness"),
        [slither_finding],
    )

    readiness_report = output_dir / "glamsterdam-readiness-report.md"
    readiness_json = output_dir / "glamsterdam-findings.json"
    findings_json = output_dir / "findings.json"
    sarif_path = output_dir / "audit-results.sarif"
    audit_report = output_dir / "audit-report.md"

    assert readiness_report.is_file()
    assert readiness_json.is_file()
    assert findings_json.is_file()
    assert sarif_path.is_file()
    assert audit_report.is_file()

    readiness_payload = json.loads(readiness_json.read_text(encoding="utf-8"))
    findings_payload = json.loads(findings_json.read_text(encoding="utf-8"))
    sarif = json.loads(sarif_path.read_text(encoding="utf-8"))
    readiness_text = readiness_report.read_text(encoding="utf-8")
    report_text = audit_report.read_text(encoding="utf-8")
    rules = _sarif_rules_by_id(sarif)

    assert readiness_payload
    assert all(item["source"] == "readiness-heuristic" for item in readiness_payload)
    assert findings_payload == [slither_finding.model_dump(mode="json")]
    assert all(item["source"] == "slither" for item in findings_payload)

    assert "Glamsterdam Solidity Readiness Report" in readiness_text
    assert "glamsterdam-eth-transfer-assumption" in {item["detector"] for item in readiness_payload}
    assert "reentrancy-eth" not in readiness_text
    assert "Slither findings are published separately" in readiness_text

    assert "reentrancy-eth" in report_text
    assert "glamsterdam-eth-transfer-assumption" not in report_text

    readiness_rules = {
        rule_id: rule for rule_id, rule in rules.items() if rule_id.startswith("glamsterdam-")
    }
    assert readiness_rules
    for rule in readiness_rules.values():
        assert rule["properties"]["tool"] == "AISolidityAuditor-GlamsterdamReadiness"
        assert rule["properties"]["source"] == "readiness-heuristic"
        assert all(tag in rule["properties"]["tags"] for tag in GLAMSTERDAM_SARIF_TAGS)

    assert rules["reentrancy-eth"]["properties"]["tool"] == "Slither"
    assert rules["reentrancy-eth"]["properties"]["source"] == "slither"
    assert "glamsterdam" not in rules["reentrancy-eth"]["properties"]["tags"]


def test_run_action_audit_glamsterdam_readiness_honors_readiness_project(tmp_path: Path):
    module = _load_action_module()
    project = tmp_path / "demo-project"
    src = project / "src"
    lib = project / "lib"
    src.mkdir(parents=True)
    lib.mkdir()
    (src / "App.sol").write_text(READINESS_CONTRACT, encoding="utf-8")
    (lib / "Noise.sol").write_text(
        "\n".join(
            [
                "pragma solidity ^0.8.20;",
                "contract Noise {",
                "  function loop() external {",
                "    for (uint256 i; i < 10; ++i) { block.timestamp; }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "results"

    _run_action_audit(
        module,
        _make_args(project, output_dir, "glamsterdam-readiness", readiness_project=src),
        [],
    )

    readiness_payload = json.loads(
        (output_dir / "glamsterdam-findings.json").read_text(encoding="utf-8")
    )
    files = {item["file"] for item in readiness_payload}

    assert readiness_payload
    assert all(path.startswith("src/") or path == "App.sol" for path in files)
    assert not any("lib/" in path or path == "Noise.sol" for path in files)
