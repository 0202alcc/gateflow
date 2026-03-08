# Task Packet: GATEFLOW-LOCAL-EXTERNAL-003

## Goal
Adopt a single-user, cross-branch source-of-truth model without requiring hosted infrastructure.

## Product Direction
- `gateflow init` should initialize a workspace-bound database outside the repo (`local-external` mode).
- Repo state keeps lightweight connection metadata and optional deterministic snapshots.
- Add `gateflow connect` for backend switching:
  - `connect local --path <sqlite-db>` (implement now)
  - `connect remote --url <...>` (stub contract now; full implementation later)

## Rationale
This gives Google-Doc-like continuity for one user across branches/devices while avoiding mandatory external services.

## Scope
1. Storage mode extension: `local-external`.
2. Workspace identity and connection metadata contract.
3. `init` behavior to create/bind external local DB.
4. `connect` command family for local binding and remote stub.
5. Snapshot import/export compatibility.
6. Validation/tests/docs for deterministic behavior.

## Non-Goals (this milestone)
- Multi-user realtime collaboration backend.
- Full remote auth/tenant management.

## Success Criteria
- New workspace defaults to external local DB outside repo.
- Branch switching in same repo keeps shared planning state through connection metadata.
- Existing CLI resource/API commands operate unchanged under `local-external` mode.
- Export/import roundtrip remains deterministic.
- `connect local` rebinding works with explicit safety checks.
- `connect remote` provides a stable CLI contract and actionable "not yet implemented" guidance.

## Go/No-Go Checks
Go:
- Integration tests prove branch continuity for one user.
- No regressions in existing command surface.
- Recovery docs verified (`rebind`, `export`, `rollback to file mode`).

No-Go:
- Connection metadata can silently point to wrong DB.
- Deterministic ordering/parity is broken in local-external mode.
- Existing resource commands diverge behavior by mode.

## Risks and Mitigations
- Risk: orphaned/unknown local DB paths.
  - Mitigation: explicit workspace ID + `status`/`doctor` diagnostics.
- Risk: accidental repo coupling to machine-specific paths.
  - Mitigation: path normalization and user-home relative tokens where possible.
- Risk: confusion between local and remote semantics.
  - Mitigation: explicit mode display and `connect` UX docs.

## Deliverables
- Milestone + task graph in GateFlow.
- Implementation PR with tests and docs.
- Migration note from file/backend modes to local-external.
