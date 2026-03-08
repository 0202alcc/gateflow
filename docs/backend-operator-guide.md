# Backend + Local-External Operator Guide

## Default Init Behavior
New workspaces now default to `storage.mode=local-external` and write canonical state to an external SQLite DB.

1. Initialize workspace:

```bash
gateflow --root <repo> init scaffold --profile minimal
```

2. Check active connection + backend target:

```bash
gateflow --root <repo> connect status
```

3. Rebind to a known local DB path (recovery/continuity):

```bash
gateflow --root <repo> connect local --path <sqlite-db>
```

4. Remote contract stub (not implemented yet):

```bash
gateflow --root <repo> connect remote --url <endpoint> --workspace <name>
```

## Legacy Backend Mode
Legacy repo-local backend mode is still supported:

```bash
gateflow --root <repo> backend migrate --to backend
gateflow --root <repo> backend status
```

## Mandatory Branch Sync Workflow (When Policy Enabled)
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

`policy.require_sync_before_write=true` remains supported. When drift exists, mutating commands return policy error `POLICY_SYNC_REQUIRED`.

## Export/Import Compatibility
- Export backend state back to file ledgers:

```bash
gateflow --root <repo> backend export
```

- Roll back fully to file mode (`storage.mode=file`):

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

3. External/local backend recovery:
- Rebind workspace: `connect local --path <known-db>`.
- If needed, force rebind after explicit validation: `connect local --path <known-db> --force`.
- Confirm active target with `connect status`.

4. Rollback to file-ledger source of truth:
- `backend export` to refresh deterministic snapshots.
- `backend migrate --to file`.
- Continue in `storage.mode=file` while investigating.

5. Lock contention on writes:
- Retry command after short delay.
- Ensure no stuck process is repeatedly writing GateFlow state.
