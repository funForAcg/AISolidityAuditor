import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.models.schemas import Finding, Severity

BASELINE_FILENAME = "glamsterdam-baseline.json"
INLINE_SUPPRESSION_MARKER = "glamsterdam-ignore"

# Canonical references for the upgrade as a whole. Individual EIPs below are
# fork candidates and may change; see EIP-7773 and https://forkcast.org.
META_REFERENCES = ("EIP-7773 (Glamsterdam meta)", "forkcast.org")


@dataclass(frozen=True)
class ReadinessRule:
    detector: str
    severity: Severity
    title: str
    keywords: tuple[str, ...]
    recommendation: str
    confidence: Literal["low", "medium", "high"]
    rationale: str
    eips: tuple[str, ...]


RULES = [
    ReadinessRule(
        detector="glamsterdam-eth-transfer-assumption",
        severity=Severity.LOW,
        title="Native ETH transfer assumption",
        keywords=(".transfer(", ".send(", ".call{value:", ".call.value("),
        recommendation=(
            "Review ETH transfer assumptions against proposed native ETH transfer logs "
            "and any gas repricing that may affect transfer-style patterns."
        ),
        confidence="medium",
        rationale=(
            "transfer()/send() forward a fixed 2300 gas stipend and value-bearing calls "
            "embed gas-cost assumptions. Gas repricing candidates and native ETH transfer "
            "logs directly touch these patterns, so a keyword match is usually relevant."
        ),
        eips=("EIP-7708 (ETH transfers emit a log, candidate)", "Glamsterdam gas repricing package (candidate)"),
    ),
    ReadinessRule(
        detector="glamsterdam-gas-sensitive-loop",
        severity=Severity.INFORMATIONAL,
        title="Gas-sensitive loop",
        keywords=("for (", "for(", "while (", "while("),
        recommendation=(
            "Review loop bounds and gas sensitivity against Glamsterdam gas repricing proposals."
        ),
        confidence="low",
        rationale=(
            "A loop is only gas-sensitive when its bound is dynamic or its body performs "
            "repriced operations. Keyword matching cannot see bounds, so this rule is "
            "deliberately high-recall and most matches need quick dismissal rather than action."
        ),
        eips=("Glamsterdam gas repricing package (candidate)",),
    ),
    ReadinessRule(
        detector="glamsterdam-low-level-evm",
        severity=Severity.INFORMATIONAL,
        title="Low-level EVM usage",
        keywords=("assembly", ".delegatecall(", ".staticcall(", ".call("),
        recommendation=(
            "Review low-level EVM assumptions against proposed opcode and EVM behavior changes."
        ),
        confidence="low",
        rationale=(
            "Assembly blocks and low-level calls may rely on opcode gas costs or semantics, "
            "but most uses are routine library plumbing. The rule flags surface area for "
            "review, not concrete incompatibilities."
        ),
        eips=("New EVM opcodes (candidates)", "Glamsterdam gas repricing package (candidate)"),
    ),
    ReadinessRule(
        detector="glamsterdam-block-context",
        severity=Severity.INFORMATIONAL,
        title="Block context dependency",
        keywords=("block.timestamp", "block.number", "block.prevrandao", "block.coinbase"),
        recommendation=(
            "Review block context assumptions as Glamsterdam candidates include protocol-level "
            "changes such as ePBS and Block-Level Access Lists."
        ),
        confidence="medium",
        rationale=(
            "Block-context values are produced by the proposer/builder pipeline. ePBS and "
            "Block-Level Access Lists change who assembles blocks and when state access is "
            "committed, so timing or ordering assumptions deserve a second look."
        ),
        eips=("EIP-7732 (ePBS, candidate)", "EIP-7928 (Block-Level Access Lists, candidate)"),
    ),
]

CONTRACT_SIZE_RULE = ReadinessRule(
    detector="glamsterdam-contract-size-watch",
    severity=Severity.INFORMATIONAL,
    title="Contract-size watch point",
    keywords=(),
    recommendation=(
        "Review contract-size assumptions against Glamsterdam max contract size discussions."
    ),
    confidence="low",
    rationale=(
        "File size is a rough proxy for deployed bytecode size. A raised max contract size "
        "would relax rather than break constraints, so this is a watch point only."
    ),
    eips=("EIP-7907 (meter and increase contract code size, candidate)",),
)


def _solidity_files(project_path: Path) -> list[Path]:
    if project_path.is_file() and project_path.suffix == ".sol":
        return [project_path]
    if project_path.is_dir():
        return sorted(project_path.rglob("*.sol"))
    return []


def _relative(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except ValueError:
        return path.name


def _code_portion(line: str) -> str:
    """Return executable code on a line, stripping // comments and string literals."""
    result: list[str] = []
    i = 0
    in_string = False
    string_char = ""
    while i < len(line):
        ch = line[i]
        if not in_string:
            if ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                break
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
                i += 1
                continue
            result.append(ch)
        else:
            if ch == "\\" and i + 1 < len(line):
                i += 2
                continue
            if ch == string_char:
                in_string = False
            i += 1
            continue
        i += 1
    return "".join(result)


def _source_context(lines: list[str], line_number: int) -> tuple[str, int, int]:
    start = max(1, line_number - 2)
    end = min(len(lines), line_number + 2)
    snippet = "\n".join(f"{idx}: {lines[idx - 1]}" for idx in range(start, end + 1))
    return snippet, start, end


def _load_baseline(base: Path) -> list[dict]:
    baseline_path = base / BASELINE_FILENAME
    if not baseline_path.is_file():
        return []
    try:
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    suppressions = data.get("suppressions", [])
    return suppressions if isinstance(suppressions, list) else []


def _baseline_suppressed(suppressions: list[dict], detector: str, rel: str, line: int) -> bool:
    for entry in suppressions:
        if not isinstance(entry, dict):
            continue
        if entry.get("detector") is not None and entry["detector"] != detector:
            continue
        if entry.get("file") is not None and entry["file"] != rel:
            continue
        if entry.get("line") is not None and entry["line"] != line:
            continue
        return True
    return False


def _inline_suppressed(raw_line: str, detector: str) -> bool:
    idx = raw_line.find(INLINE_SUPPRESSION_MARKER)
    if idx == -1:
        return False
    rest = raw_line[idx + len(INLINE_SUPPRESSION_MARKER):].strip()
    if rest.startswith(":"):
        listed = {item.strip() for item in rest[1:].split(",")}
        return detector in listed
    return True


def _rule_finding(
    rule: ReadinessRule,
    index: int,
    rel: str,
    line_number: int,
    description: str,
    snippet: str | None = None,
    start: int | None = None,
    end: int | None = None,
) -> Finding:
    return Finding(
        id=f"glamsterdam-{index}",
        detector=rule.detector,
        severity=rule.severity,
        description=description,
        file=rel,
        line=line_number,
        source_context=snippet,
        source_start_line=start,
        source_end_line=end,
        source="readiness-heuristic",
        rule_confidence=rule.confidence,
        rule_rationale=rule.rationale,
        related_eips=list(rule.eips),
    )


def scan_project(project_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    base = project_path if project_path.is_dir() else project_path.parent
    suppressions = _load_baseline(base)
    seen: set[tuple[str, str, int]] = set()

    for file_path in _solidity_files(project_path):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        rel = _relative(file_path, base)

        if len(text) > 20_000:
            key = (CONTRACT_SIZE_RULE.detector, rel, 1)
            if key not in seen and not _baseline_suppressed(
                suppressions, CONTRACT_SIZE_RULE.detector, rel, 1
            ):
                seen.add(key)
                findings.append(
                    _rule_finding(
                        CONTRACT_SIZE_RULE,
                        len(findings) + 1,
                        rel,
                        1,
                        "Large Solidity source file. "
                        + CONTRACT_SIZE_RULE.recommendation,
                    )
                )

        for line_number, line in enumerate(lines, start=1):
            code = _code_portion(line)
            if not code.strip():
                continue
            compact = code.replace(" ", "")
            for rule in RULES:
                haystacks = (code, compact)
                if not any(keyword in haystack for keyword in rule.keywords for haystack in haystacks):
                    continue
                key = (rule.detector, rel, line_number)
                if key in seen:
                    continue
                if _inline_suppressed(line, rule.detector):
                    continue
                if _baseline_suppressed(suppressions, rule.detector, rel, line_number):
                    continue
                seen.add(key)
                snippet, start, end = _source_context(lines, line_number)
                findings.append(
                    _rule_finding(
                        rule,
                        len(findings) + 1,
                        rel,
                        line_number,
                        f"{rule.title}. {rule.recommendation}",
                        snippet,
                        start,
                        end,
                    )
                )

    return findings


def _readiness_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.source == "readiness-heuristic"]


def _detector_summary(findings: list[Finding]) -> list[tuple[str, str, int]]:
    counts: dict[str, int] = {}
    confidences: dict[str, str] = {}
    for finding in findings:
        counts[finding.detector] = counts.get(finding.detector, 0) + 1
        if finding.rule_confidence:
            confidences[finding.detector] = finding.rule_confidence
    return [
        (detector, confidences.get(detector, "low"), count)
        for detector, count in sorted(counts.items())
    ]


def generate_readiness_report(project_name: str, findings: list[Finding]) -> str:
    findings = _readiness_findings(findings)
    lines = [
        "# Glamsterdam Solidity Readiness Report",
        "",
        f"- **Project**: {project_name}",
        f"- **Readiness findings**: {len(findings)}",
        f"- **Upgrade references**: {', '.join(META_REFERENCES)}",
        "",
        "> This report contains Glamsterdam readiness heuristics only. Slither findings are "
        "published separately in `audit-report.md` and `findings.json`.",
        "",
        "> This report is an early readiness triage for proposed Glamsterdam-related changes. "
        "It is not a protocol compatibility guarantee and requires manual review. Rule "
        "confidence below reflects how often a keyword match is expected to deserve action: "
        "low-confidence rules are intentionally high-recall review prompts.",
        "",
        "## Focus Areas",
        "",
        "- Gas repricing and gas-sensitive source patterns",
        "- EVM opcode or low-level call assumptions",
        "- Native ETH transfer logging assumptions",
        "- Block context assumptions around ePBS and Block-Level Access Lists",
        "- Contract-size watch points",
        "",
        "## Summary by detector",
        "",
    ]

    summary = _detector_summary(findings)
    if summary:
        lines.extend(
            [
                "| Detector | Rule confidence | Count |",
                "|----------|-----------------|------:|",
            ]
        )
        for detector, confidence, count in summary:
            lines.append(f"| `{detector}` | {confidence} | {count} |")
    else:
        lines.append("*No readiness findings.*")
    lines.extend(["", "## Findings", ""])

    if not findings:
        lines.append("*No Glamsterdam readiness patterns were detected by the current heuristics.*")
    else:
        for finding in findings:
            location = finding.file or "unknown"
            if finding.line:
                location = f"{location}:{finding.line}"
            lines.extend(
                [
                    f"### [{finding.severity.value}] {finding.detector}",
                    "",
                    f"- **Location**: `{location}`",
                    f"- **Review note**: {finding.description}",
                    f"- **Rule confidence**: {finding.rule_confidence or 'low'}",
                ]
            )
            if finding.rule_rationale:
                lines.append(f"- **Rule rationale**: {finding.rule_rationale}")
            if finding.related_eips:
                lines.append(f"- **Related fork candidates**: {', '.join(finding.related_eips)}")
            lines.extend(["- **Manual review required**: Yes", ""])
            if finding.source_context:
                lines.extend(["```solidity", finding.source_context, "```", ""])

    lines.extend(
        [
            "## Tuning and suppression",
            "",
            "Reviewed-and-accepted matches can be suppressed so repeat runs stay focused:",
            "",
            "- Inline: append `// glamsterdam-ignore` to the flagged line, or "
            "`// glamsterdam-ignore: <detector>[, <detector>]` to suppress specific rules.",
            f"- Baseline: add a `{BASELINE_FILENAME}` file at the scan root with "
            '`{"suppressions": [{"detector": "...", "file": "...", "line": 12}]}`. '
            "Omitted keys act as wildcards.",
            "",
            "## Limitations",
            "",
            "- Glamsterdam EIPs are still under consideration and may change; see "
            "EIP-7773 and forkcast.org for current status.",
            "- Readiness heuristics are separate from Slither static-analysis evidence.",
            "- Findings are review prompts, not vulnerability claims.",
            "- Low-confidence rules trade precision for recall by design; use suppression "
            "to record triage decisions.",
        ]
    )
    return "\n".join(lines)
