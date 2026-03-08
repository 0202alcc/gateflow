# Backend Mode Operator Guide

## Enable Backend Mode
1. Initialize workspace if needed:

```bash
gateflow --root <repo> init scaffold --profile minimal
```

2. Migrate ledgers into SQLite and flip source of truth:

```bash
gateflow --root <repo> backend migrate --to backend
```

3. Verify mode:

```bash
gateflow --root <repo> backend status
```

## Mandatory Branch Sync Workflow (Required Before Writes)
Run this sequence before any `tasks|milestones|boards|backlog|config set|api POST/PATCH/DELETE|close` write:

1. Capture canonical snapshot from `main`:

```bash
gateflow --root <repo> sync from-main
```

2. Inspect drift/conflicts:

```bash
gateflow --root <repo> sync status
```

3. Apply canonical baseline on branch when required:

```bash
gateflow --root <repo> sync apply
```

4. Mutate planning state only when `sync status` is `clean`.

`policy.require_sync_before_write=true` is the canonical default. When drift exists, mutating commands return policy error `POLICY_SYNC_REQUIRED`.

## Export/Import Compatibility
- Export backend state back to file ledgers:

```bash
gateflow --root <repo> backend export
```

- Roll back fully to file mode:

```bash
gateflow --root <repo> backend migrate --to file
```

## Recovery Procedures
1. Drifted write blocked (`POLICY_SYNC_REQUIRED`):
- Run `sync from-main`, then `sync status`.
- If drift exists, review `drift.conflicts` and run `sync apply`.
- Re-run `sync status` and continue only when status is `clean`.

2. Drift unexpectedly high:
- Run `sync from-main`, then `sync status`.
- Review `drift.conflicts` and reconcile local work.
- Run `sync apply` only after confirming overwrites are safe.

3. Backend file corruption or rollback required:
- `backend migrate --to file` to rehydrate ledgers.
- Commit exported ledgers.
- Continue in `file` mode while investigating.

4. Lock contention on writes:
- Retry command after short delay.
- Ensure no stuck process is repeatedly writing GateFlow state.
