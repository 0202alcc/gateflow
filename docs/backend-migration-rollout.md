# v1 Rollout, Gates, and Risk Posture

## Phased Rollout

### Phase 0: Pilot local-external
- Initialize pilot repos with `gateflow init` (default `storage.mode=local-external`).
- Validate branch continuity via shared external DB.
- Keep `policy.require_sync_before_write=false` only during operator training.

### Phase 1: Enforce sync-before-write
- Set `policy.require_sync_before_write=true`.
- Require PR gates:
  - `planning-standardization-gates / planning-gates`
  - `backend-local-external-smoke / backend-local-external-smoke`
  - `release-reproducibility / reproducible-artifacts`

### Phase 2: v1 steady state
- Keep local-external default and deterministic migration fallback to file mode.
- Keep branch protection checks required.

## Go/No-Go Checks

Go criteria:
- Migration matrix tests green across `file`, `backend`, `local-external`.
- Drift/validate gates block merges when non-compliant.
- Reproducible packaging pipeline green.
- Operator rollback playbooks validated.

No-Go criteria:
- Non-deterministic migration or ordering drift.
- Missing rollback path for active storage mode.
- Branch protection does not require planning gates.
- Packaging reproducibility or install smoke fails.

## Risk Register (v1 summary)
1. Branch protection drift from required checks (high).
2. Incorrect `connect local --force` usage (high).
3. Baseline resolution failure when `main` missing (medium).
4. Build environment variability for reproducibility (medium).
