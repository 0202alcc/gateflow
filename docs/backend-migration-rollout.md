# Backend Rollout, Success Criteria, and Risk Register

## Phased Rollout

### Phase 0: Observe-only
- Keep `storage.mode=file`.
- Run `sync from-main` + `sync status` on feature branches.
- Record conflict frequency and remediation latency.

### Phase 1: Optional backend writes
- Allow selected branches/repos to run `backend migrate --to backend`.
- Keep `policy.require_sync_before_write=false` by default.
- Verify export parity with `backend export`.

### Phase 2: Default backend mode
- New scaffolds default to backend mode in selected environments.
- Enable `policy.require_sync_before_write=true` for high-change branches.
- Track incident rate and rollback events.

### Phase 3: Deprecate direct file writes
- Retain file export/import bridge for transition windows.
- Announce deprecation window before removing direct file-only write path.

## Measurable Success Criteria
- Deterministic roundtrip: `file -> backend -> file` has no semantic diff for managed resources.
- Sync stability: `sync status` is deterministic for identical state/commit input.
- Conflict handling: conflict report includes actionable remediation commands.
- Safety: write policy blocks drifted writes when enabled.
- Compatibility: legacy CLI/API commands continue to function in both storage modes.

## Go/No-Go Checks
Go criteria:
- Backend smoke CI is green.
- Integration tests pass for sync, drift, conflict remediation, and roundtrip parity.
- Operator guide validated by at least one dry-run migration and rollback.
- No unresolved P0/P1 data-loss issues.

No-Go criteria:
- Non-deterministic ordering observed in backend exports.
- Sync apply overwrites without conflict visibility.
- Policy enforcement can be bypassed in mutating paths.
- Rollback (`backend migrate --to file`) fails to restore writable ledgers.

## Risk Register
1. Data divergence between SQLite and JSON ledgers
- Impact: high
- Mitigation: explicit import/export commands, parity tests, deterministic ordering.

2. Accidental overwrite during `sync apply`
- Impact: high
- Mitigation: `sync status` + conflict report before apply, policy-gated writes.

3. Git baseline unavailable (`main` missing/local detached state)
- Impact: medium
- Mitigation: explicit sync error with remediation; require valid `main` reference.

4. Lock contention in local concurrent writes
- Impact: medium
- Mitigation: lightweight file lock + SQLite `BEGIN IMMEDIATE`; retries in callers.

5. Compatibility drift in external consumers of file ledgers
- Impact: medium
- Mitigation: keep file mode, keep export bridge, maintain API shim warnings.

## Rollout Recommendation
Proceed to Phase 1 immediately with backend mode opt-in and required CI smoke gates. Promote to Phase 2 only after two consecutive release cycles with zero critical rollback incidents and deterministic parity checks passing on every release branch.
