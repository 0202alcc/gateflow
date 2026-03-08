# Changelog

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
