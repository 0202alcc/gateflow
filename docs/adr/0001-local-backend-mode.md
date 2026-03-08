# ADR 0001: Local Backend + Local-External Modes for GateFlow

## Status
Accepted (implementation phase started in this change set).

## Context
GateFlow currently stores planning state in JSON ledgers under `.gateflow/`. This keeps workflows simple and local-first, but branch consistency depends on manual discipline. We need a canonical local store that supports deterministic branch sync while preserving offline usage and compatibility with existing CLI contracts.

## Decision
GateFlow supports three explicit storage modes:

- `file` mode: JSON ledgers remain source of truth.
- `backend` mode: embedded repo-local SQLite (`.gateflow/gateflow.db`) is source of truth.
- `local-external` mode (default for new init): external SQLite outside repo is source of truth, with repo connection metadata at `.gateflow/connection.json`.

Mode is controlled via `config.storage.mode` and can be overridden with `GATEFLOW_STORAGE_MODE`.

A storage abstraction (`gateflow.storage`) now backs resources:

- milestones
- tasks
- boards
- frameworks
- backlog
- closeout metadata refs (`closeout_refs`)

Branch standardization uses sync metadata persisted in storage:

- `gateflow sync from-main` captures canonical baseline from `main` commit snapshot.
- `gateflow sync status` reports drift/conflicts + remediation commands.
- `gateflow sync apply` writes baseline to current branch state.

Policy option `policy.require_sync_before_write` blocks writes when branch drift exists.

## Migration + Rollback
Forward migration:

1. `gateflow backend migrate --to backend`
2. Enable optional `policy.require_sync_before_write`.
3. Use `sync` workflow per branch.

Rollback:

1. `gateflow backend migrate --to file` (exports SQLite state back to ledgers)
2. Set `storage.mode` to `file`.

This preserves deterministic export/import roundtrip and offline operation.

## Rationale
- SQLite gives transactional writes + deterministic ordered reads.
- File mode remains available for compatibility and conservative rollout.
- Sync metadata and drift reports make branch hygiene explicit and automatable.

## Consequences
Positive:

- Canonical local state in local-external/backend modes.
- Deterministic branch sync primitives.
- Better conflict visibility and safer writes.

Tradeoffs:

- Additional complexity in storage and migration paths.
- Need CI and docs coverage for dual-mode behavior.

## Implementation Plan
1. Add storage abstraction + SQLite backend with deterministic ordering and metadata persistence.
2. Add backend migration/export commands and mode flags.
3. Add sync/drift/apply commands with persisted metadata (source commit, timestamps, conflict summary).
4. Enforce optional sync-before-write policy.
5. Keep API shim contract; add compatibility warning when SQLite-backed mode is active.
6. Add integration tests + CI smoke workflow for backend/sync.
7. Publish operator, migration, and rollout docs.
