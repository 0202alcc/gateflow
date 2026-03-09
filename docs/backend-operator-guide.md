# Backend + Local-External Operator Guide (v1)

## Default Init Behavior
New workspaces default to `storage.mode=local-external` and write canonical state to an external SQLite DB.

1. Initialize workspace:

```bash
gateflow --root <repo> init scaffold --profile minimal
```

2. Check active connection + backend target:

```bash
gateflow --root <repo> connect status
```

3. Rebind to known local DB path (continuity/recovery):

```bash
gateflow --root <repo> connect local --path <sqlite-db>
```

4. Remote contract stub (not implemented in v1):

```bash
gateflow --root <repo> connect remote --url <endpoint> --workspace <name>
```

## Mandatory Sync Workflow (policy enabled)
Run before mutating writes (`tasks|milestones|boards|backlog|config set|api POST/PATCH/DELETE|close`):

```bash
gateflow --root <repo> sync from-main
gateflow --root <repo> sync status
gateflow --root <repo> sync apply
```

When `policy.require_sync_before_write=true`, drifted writes fail with `POLICY_SYNC_REQUIRED`.

## Rollback Playbooks

### Playbook A: Roll back to file-ledger mode

```bash
gateflow --root <repo> backend export
gateflow --root <repo> backend migrate --to file
gateflow --root <repo> validate all
```

### Playbook B: Recover wrong local-external binding

```bash
gateflow --root <repo> connect status
gateflow --root <repo> connect local --path <expected-db>
# emergency only:
gateflow --root <repo> connect local --path <expected-db> --force
```

### Playbook C: Recover sync metadata failures

```bash
gateflow --root <repo> sync from-main
gateflow --root <repo> sync status
gateflow --root <repo> sync apply
```

## Troubleshooting Matrix

| Symptom | Likely Cause | Recovery |
|---|---|---|
| `POLICY_SYNC_REQUIRED` on write | branch drift while sync policy enabled | `sync from-main`, `sync status`, `sync apply` |
| `sync metadata missing` | baseline not captured yet | `sync from-main` then re-run command |
| `sync metadata is invalid` | stale/corrupt sync meta | recapture with `sync from-main` |
| `target DB ... different workspace_id` | attempted bind to foreign DB | rebind expected DB or use `--force` only for controlled recovery |
| validation fails after migration | incomplete/mismatched transition | `backend export`, inspect ledgers, re-run migration path |
| lock timeout on write | concurrent writer lock contention | retry after delay; stop stuck writer process |
