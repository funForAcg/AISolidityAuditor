import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.models.schemas import SEVERITY_ORDER, Finding, Severity

logger = logging.getLogger(__name__)

IMPACT_TO_SEVERITY = {
    "High": Severity.HIGH,
    "Medium": Severity.MEDIUM,
    "Low": Severity.LOW,
    "Informational": Severity.INFORMATIONAL,
    "Optimization": Severity.OPTIMIZATION,
}


def check_slither_available() -> tuple[bool, Optional[str]]:
    try:
        result = subprocess.run(
            ["slither", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            version = (result.stdout or result.stderr).strip().split("\n")[0]
            return True, version
        return False, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, None


def check_solc_available() -> bool:
    try:
        result = subprocess.run(
            ["solc", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_slither(project_path: Path, output_path: Path) -> dict[str, Any]:
    cmd = [
        "slither",
        str(project_path),
        "--json",
        str(output_path),
        "--disable-color",
    ]

    logger.info("Running Slither: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.slither_timeout_sec,
            cwd=str(project_path),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Slither 分析超时（超过 {settings.slither_timeout_sec} 秒）"
        ) from exc

    if not output_path.exists():
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(stderr or "Slither 执行失败，未生成输出文件")

    raw = json.loads(output_path.read_text(encoding="utf-8"))

    if result.returncode != 0 and not raw.get("results", {}).get("detectors"):
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(stderr or "Slither 执行失败")

    return raw


def _extract_location(elements: list[dict[str, Any]]) -> tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    contract = None
    function = None
    file_path = None
    line = None

    for el in elements:
        el_type = el.get("type", "")
        if el_type == "contract":
            contract = el.get("name")
        elif el_type == "function":
            function = el.get("name")
        elif el_type in ("variable", "node"):
            src = el.get("source_mapping", {})
            if src.get("filename_short"):
                file_path = src["filename_short"]
            if src.get("lines"):
                line = src["lines"][0]

    if file_path is None:
        for el in elements:
            src = el.get("source_mapping", {})
            if src.get("filename_short"):
                file_path = src["filename_short"]
                if src.get("lines"):
                    line = src["lines"][0]
                break

    return contract, function, file_path, line


def parse_slither_results(raw: dict[str, Any]) -> list[Finding]:
    detectors = raw.get("results", {}).get("detectors", [])
    findings: list[Finding] = []

    for idx, det in enumerate(detectors):
        impact = det.get("impact", "Informational")
        severity = IMPACT_TO_SEVERITY.get(impact, Severity.INFORMATIONAL)
        elements = det.get("elements", [])
        contract, function, file_path, line = _extract_location(elements)

        findings.append(
            Finding(
                id=f"finding-{idx + 1}",
                detector=det.get("check", "unknown"),
                severity=severity,
                description=det.get("description", ""),
                contract=contract,
                function=function,
                file=file_path,
                line=line,
            )
        )

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.id))
    return findings
