# GateFlow v1.0.0 Compatibility Contract

## Scope
This contract defines stable behavior for the v1 CLI and planning API shim for single-user, offline/local-first operation across `file`, `backend`, and `local-external` storage modes.

## Compatibility Promise
- `gateflow` command groups in this repo are considered stable for `v1.x`:
  - `init`, `config`, `validate`, `api`, `render`, `import-luvatrix`, `backend`, `connect`, `sync`, `close`
  - resource groups: `milestones`, `tasks`, `boards`, `frameworks`, `backlog`, `closeout-refs`
- JSON output contracts are stable for:
  - `sync from-main|status|apply`
  - `backend status|migrate|export`
  - `connect status|local|remote`
  - `close task|milestone`
- Error contracts are stable:
  - `--json-errors` payload shape (`ok`, `error_type`, `exit_code`, `message`, `errors`)
  - exit codes: `0` success, `2` validation/close, `3` policy/sync, `4` internal

## Behavioral Guarantees
- Deterministic ordering for listed resources by stable key (`id` or `name`).
- Deterministic migration/export semantics between JSON ledgers and SQLite-backed modes.
- Offline/local-first by default. No network dependency for local CLI workflows.
- No silent policy bypass:
  - protected-branch guard for mutating operations
  - sync-before-write guard when `policy.require_sync_before_write=true`

## API Shim Contract
- `gateflow api` remains a compatibility interface for file-ledger-like operations.
- Shim compatibility marker remains `planning_api_shim_v1`.
- API behavior parity is maintained across storage modes for supported resources.

## Deprecation Policy
- v1 uses additive-first evolution.
- Breaking CLI/API changes require all of the following:
  1. Deprecation notice in release notes and changelog.
  2. Warning period across at least two minor releases (`v1.N` and `v1.N+1`).
  3. Migration guidance with explicit replacement command/path.
  4. Recovery/rollback note in operator docs when behavior touches storage/sync.

## Support Window
- `v1` support window: 12 months from `v1.0.0` release date.
- Patch releases (`v1.0.x`) are backward compatible.
- Minor releases (`v1.x`) preserve this contract or follow deprecation policy above.
