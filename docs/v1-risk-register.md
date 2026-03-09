# GateFlow v1 Final Risk Register

## Open Risks
1. Branch protection drift from intended required checks.
- Impact: high
- Mitigation: enforce required checks and periodically audit via GitHub API.
- Residual: medium

2. Operator misuse of `connect local --force`.
- Impact: high
- Mitigation: runbook marks `--force` as recovery-only; require post-rebind verification.
- Residual: medium

3. Incorrect baseline branch resolution (`main` unavailable).
- Impact: medium
- Mitigation: explicit sync error and remediation commands in CLI + docs.
- Residual: low

4. Packaging environment variability for artifact reproducibility.
- Impact: medium
- Mitigation: pinned reproducibility workflow with deterministic `SOURCE_DATE_EPOCH` and hash compare.
- Residual: low

## Closed/Contained Risks
- Deterministic ordering drift across storage modes: covered by migration matrix tests.
- Missing rollback procedures: covered in migration matrix + operator runbooks.
- Merge policy bypass through CI omission: covered by planning gates + branch protection verification.
