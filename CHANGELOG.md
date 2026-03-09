# Changelog

## 1.0.0 - 2026-03-09

- Locked v1 CLI/API compatibility contract and deprecation/support policy.
- Added deterministic migration/rollback matrix coverage across `file`, `backend`, and `local-external`.
- Added failure-path recovery coverage for sync metadata and workspace rebind mismatch scenarios.
- Added reproducible artifact and install-smoke CI workflow (`uv`, `pipx`, `wheel`, `sdist`).
- Finalized v1 operator runbooks, troubleshooting matrix, and release guidance.
- Added branch protection evidence template and v1 final risk register.

## 0.1.0a4 - 2026-03-08

- Added `local-external` storage mode as default for new workspace initialization.
- Added deterministic workspace connection metadata (`.gateflow/connection.json`) and external DB binding model.
- Added `gateflow connect local` workflow and `connect remote` contract stub for future hosted backends.
- Added local-external integration tests and backend smoke workflow coverage updates.
- Added closeout packet and milestone/task packet for `GATEFLOW-LOCAL-EXTERNAL-003`.

## 0.1.0a3 - 2026-03-08

- Added `gateflow close task` and `gateflow close milestone` commands with Go/No-Go heads-up enforcement.
- Added closure validation safeguards so incorrect close attempts fail with actionable errors.
- Added deterministic closure issue logging at `.gateflow/closeout/closure_issues.json` when close checks fail.
- Added `gateflow init` shorthand defaulting to `init scaffold --profile minimal`.
- Expanded test coverage for close workflows and scaffolded closeout issue ledgers.

## 0.1.0a2 - 2026-03-08

- Hard-deprecated legacy in-repo `gateflow_cli.cli` path and routed wrapper usage to standalone command execution.
- Added continuity CI gate in Luvatrix validating `uv run gateflow --root . validate all`.
- Removed stale legacy `gateflow_cli` implementation modules from Luvatrix root package.
- Added wrapper environment defaults for local uvx tool/cache directories (`UV_CACHE_DIR`, `UV_TOOL_DIR`) to improve reliability.
- Added release migration guidance for `LUVATRIX_GATEFLOW_WRAPPER_CMD` and standalone command paths.

## 0.1.0a1 - 2026-03-07

- Initial standalone CLI extraction from Luvatrix.
