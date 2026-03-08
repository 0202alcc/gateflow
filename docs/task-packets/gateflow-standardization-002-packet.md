# Task Packet: GATEFLOW-STANDARDIZATION-002

## Goal
Deliver always-standardized GateFlow behavior across branches by enforcing sync hygiene before writes and before merge.

## Problem
The backend/sync model exists, but behavior is optional unless policy and CI gates are enforced.

## Scope
1. Enforce sync-before-write in active workspaces.
2. Add CI gate to block merge when branch is drifted or planning state is invalid.
3. Standardize branch workflow commands and operator docs.
4. Add adoption telemetry/check script for policy drift.

## Required Commands (developer workflow)
1. `gateflow sync from-main`
2. `gateflow sync status`
3. `gateflow sync apply` (when drifted)
4. mutate planning state
5. `gateflow validate all`

## Success Criteria
- `policy.require_sync_before_write=true` in canonical config for managed repos.
- PR CI fails when sync status is drifted.
- PR CI fails when planning validation fails.
- Drift remediation guidance is printed in failure logs.
- No direct planning writes accepted on unsynced branches.

## Go/No-Go Checks
Go:
- CI gate is green for two sample repos with branch sync workflow.
- At least one forced failure case proves gate blocks unsynced writes.
- Operator docs include fast recovery path.

No-Go:
- Unsynced branches can still mutate planning records without policy override.
- CI allows drifted branch merge.

## Risks
- False positives in CI when local `main` baseline is stale.
- Team friction during initial enforcement.

## Mitigations
- Require fetch of `origin/main` in CI sync checks.
- Phase rollout: warn-only -> enforce.
- Provide clear remediation snippets in CI output.

## Deliverables
- Milestone and tasks wired in `.gateflow`.
- CI job updates for sync enforcement.
- Operator workflow doc update.
- Closeout evidence with pass/fail examples.
