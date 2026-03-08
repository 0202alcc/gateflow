# RFC: GATEFLOW-BACKEND-001 Local Backend Planning Mode

## Objective
Evolve GateFlow from file-ledger-only behavior to a local backend-backed planning system with deterministic branch synchronization while preserving offline usage and CLI compatibility.

## Scope
1. Storage layer with explicit source-of-truth mode:
- `file` mode: JSON ledgers are canonical.
- `backend` mode: SQLite is canonical.

2. Migration bridge:
- deterministic import (`file -> backend`)
- deterministic export (`backend -> file`)
- rollback safety via reversible mode switch

3. Branch standardization commands:
- `sync from-main`
- `sync status`
- `sync apply`

4. Drift and safety:
- baseline drift detector
- write lock / transaction semantics
- policy option to require clean sync before writes

5. Compatibility:
- preserve current CLI contracts where possible
- API shim warnings in backend mode
- luvatrix import/export transition support

## Non-Goals
- hosted/remote backend service
- online dependency for normal operations
- breaking API changes without deprecation window

## Design Summary
- Introduce `Storage` abstraction with `FileStorage` and `SQLiteStorage`.
- Keep resource services (`milestones/tasks/boards/backlog/frameworks/closeout refs`) storage-agnostic.
- Persist sync baseline metadata in active storage backend.
- Enforce deterministic ordering by stable key (`id` or `name`) for all reads/writes.
- Add lightweight local lock for file writes and SQLite immediate transactions for backend writes.

## Determinism Guarantees
- Stable serialization (`sort_keys=True`, ASCII JSON).
- Stable item ordering for all managed resources.
- Drift comparisons normalize ordering and compare canonical JSON representation.

## Failure Modes and Recovery
1. Main baseline unavailable:
- return sync error with remediation (`ensure main exists locally`)

2. Drifted branch with sync policy enabled:
- block writes with policy error
- remediation: `sync from-main`, inspect `sync status`, `sync apply`

3. Backend rollback required:
- run `backend migrate --to file`
- continue in file mode with exported ledgers

## Success Criteria
- deterministic roundtrip parity: file -> backend -> file
- sync status deterministic given same baseline and branch state
- conflict report lists actionable remediation commands
- no regression for existing CLI read/write commands across both modes
- CI backend smoke test green

## Go/No-Go Checks
Go:
- integration tests pass for sync, drift, conflict remediation, and roundtrip parity
- rollback path validated in test and operator guide
- zero unresolved critical data-loss defects

No-Go:
- non-deterministic export ordering
- silent overwrite paths without visible conflict output
- inability to recover to file mode

## Execution Plan
1. Finalize ADR + RFC artifacts and success criteria.
2. Land storage abstraction and backend implementation.
3. Land sync/drift/policy enforcement.
4. Land compatibility and migration shims.
5. Land integration tests and backend CI smoke gate.
6. Run phased rollout (observe-only -> optional backend -> default backend -> deprecate direct file writes).
