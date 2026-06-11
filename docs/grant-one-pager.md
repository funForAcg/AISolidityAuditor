# Ethereum grant one-pager

## Project

**Glamsterdam Solidity Readiness Triage Toolkit** extends AISolidityAuditor, an open-source Solidity security triage assistant. The Glamsterdam mode helps Ethereum developers review source patterns that may need attention as Glamsterdam candidates evolve.

The MVP already runs Slither, preserves raw analyzer output, emits SARIF, and produces separate readiness artifacts for gas, EVM, native ETH transfer logging, block context, and contract-size watch points. It is not a formal audit or a protocol compatibility guarantee. Every result requires manual review.

## ESP Wishlist alignment

This proposal targets the current ESP Wishlist item **Glamsterdam Grants Round**. That round asks for work that helps the Ethereum community prepare for and adapt to Glamsterdam, including developer tooling updates, impact analysis tooling, monitoring tooling, and data-driven research.

This project fits as developer tooling and impact-analysis support for Solidity maintainers.

## Problem

Protocol upgrades can affect assumptions embedded in contracts and developer workflows. Many small teams do not have an upgrade-readiness checklist or CI artifact that flags gas-sensitive patterns, low-level EVM usage, ETH transfer assumptions, or block context dependencies for review.

Raw static analysis is useful, but it does not package upgrade-readiness prompts into a reviewer-friendly report and SARIF workflow with clean evidence boundaries.

## Current base (MVP already shipped)

AISolidityAuditor already provides:

- FastAPI + React self-hosted web app.
- Reusable GitHub Action with `mode: glamsterdam-readiness`.
- Slither JSON preservation and Slither-only `audit-report.md` / `findings.json`.
- Separate `glamsterdam-readiness-report.md` and `glamsterdam-findings.json`.
- Combined SARIF with tool/source metadata for Slither vs readiness heuristics.
- 30-fixture CI evaluation corpus.
- Assistive AI explanations that always require manual review.
- Docker-based verification commands and sandbox documentation.

Grant funding is requested to validate, harden, demonstrate, and release this MVP for real ecosystem use—not to build the initial mode from scratch.

## Proposed grant scope: 6-8 weeks

1. **Harden and validate Glamsterdam readiness mode**
   - Lock evidence boundaries between Slither and readiness heuristics in reports, JSON, and SARIF.
   - Add end-to-end Action tests and CI validation for readiness artifact generation.
   - Document mode usage, limitations, and reviewer-facing evidence boundaries.

2. **Run two public repo demos** — *status: 1 of 2 completed*
   - Completed: [transmissions11/solmate](https://github.com/transmissions11/solmate) at a pinned commit, with published artifacts, an end-to-end Action run (SARIF code-scanning upload, artifacts, PR comment), and recorded evidence links.
   - Within the grant period: a second demo (OpenZeppelin Contracts or Uniswap v4-core) and an optional third, each with commit SHA, setup assumptions, Slither counts, readiness counts, SARIF tags, and artifacts.

3. **Improve heuristic precision and false-positive handling**
   - Shipped: per-rule confidence levels, rule rationales, fork-candidate (EIP) linkage, inline `glamsterdam-ignore` suppression, and a `glamsterdam-baseline.json` suppression file.
   - Within the grant period: execute the published false-positive measurement protocol (sampled two-reviewer classification per detector) and publish per-detector precision in the benchmark report.
   - Continue reducing comment/string false positives and expand readiness evaluation fixtures.

4. **Publish benchmark notes and demo artifacts**
   - Publish benchmark comparisons and real-project demo artifacts for grant reviewers.
   - Record Foundry/Hardhat/remapping limitations transparently.

5. **Prepare tagged Action release**
   - Publish a tagged `AISolidityAuditor-action@v1` repository and version.
   - Finalize release notes, usage docs, and maintenance expectations.

## Budget request

Requested budget: **USD 10,000-15,000 equivalent**.

Suggested allocation:

- Hardening, validation, and evidence-boundary work: 25%
- Heuristic precision and fixture/benchmark coverage: 20%
- Two public repo demos and published artifacts: 30%
- Tagged Action release and documentation: 15%
- Maintenance buffer: 10%

## Success metrics

- Action supports `mode: glamsterdam-readiness` with end-to-end CI coverage.
- `audit-report.md` and `findings.json` contain Slither evidence only.
- Readiness report and JSON contain readiness heuristics only.
- SARIF merges both sources with distinct tool/source metadata and Glamsterdam tags on readiness rules only.
- 30 existing Solidity fixtures continue to pass.
- At least 2 public Solidity repositories have documented readiness demo runs — *1 completed (solmate, with end-to-end Action evidence); the second and an optional third are grant-period deliverables*.
- Per-detector readiness false-positive rates are measured and published in the benchmark report — *measurement protocol published; classification is a grant-period deliverable*.
- Tagged Action release is published.

## Risks and mitigations

- **Glamsterdam EIPs may change**: findings are conservative readiness prompts, and docs explicitly avoid compatibility guarantees.
- **False confidence**: Slither output stays separate; readiness heuristics are labeled explicitly and require manual review.
- **Over-broad heuristics**: checks are documented as review triggers, not vulnerability claims; each rule carries an explicit confidence level and rationale, suppression/baseline mechanisms record triage decisions, and per-detector false-positive rates are reported separately in the benchmark.
- **Complex project compatibility**: demo notes record setup assumptions and limitations instead of hiding failures.
