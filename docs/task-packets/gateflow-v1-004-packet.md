# Task Packet: GATEFLOW-V1-004

## Goal
Ship GateFlow `v1.0.0` with stable single-user local-external workflows, deterministic behavior, and enforceable release gates.

## Scope
1. Lock compatibility contract for CLI/API behavior.
2. Finalize schema/migration guarantees and rollback safety.
3. Enforce branch/CI protection for planning standardization.
4. Harden packaging/release pipeline for v1 cut.
5. Finalize operator docs and recovery runbooks.

## Out of Scope
- Full multi-user hosted backend implementation.
- Realtime collaboration (WebSocket/SSE).

## Success Criteria
- Publicly documented v1 command contract and deprecation policy.
- Migration tests cover file <-> backend <-> local-external transitions with deterministic parity.
- Required CI gates are enforced in branch protection.
- Release pipeline produces reproducible artifacts and install smoke passes.
- Operator guide includes recovery for sync/drift/connect failures.

## Go/No-Go
Go:
- All v1 tasks closed with Go/No-Go heads-up.
- No open P0/P1 issues in closure ledger.
- v1 release candidate passes full CI + packaging checks.

No-Go:
- Any nondeterministic state transitions in storage/sync/migration.
- Missing rollback path for active storage modes.
- Merge protection not requiring planning gates.

## Deliverables
- v1 milestone + tasks in GateFlow.
- Versioned docs for contract, migration, and operations.
- CI and protection evidence.
- Final release recommendation (`GO` or `NO-GO`) with risks.
