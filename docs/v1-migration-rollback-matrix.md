# GateFlow v1 Migration + Rollback Matrix

## Objectives
- Deterministic transitions across `file`, `backend`, and `local-external`.
- Explicit failure-path handling with recovery commands.
- No data-loss path for supported single-user workflows.

## Matrix

| From | To | Command(s) | Determinism Check | Rollback |
|---|---|---|---|---|
| `file` | `backend` | `gateflow backend migrate --to backend` | Resource ordering and item payload parity | `gateflow backend migrate --to file` |
| `backend` | `file` | `gateflow backend migrate --to file` | JSON ledgers sorted by stable key | `gateflow backend migrate --to backend` |
| `file` | `local-external` | `gateflow connect local --path <db>` | SQLite + mirrored ledgers maintain parity | `gateflow config set storage.mode '"file"'` |
| `local-external` | `file` | `gateflow backend migrate --to file` | Exported ledgers semantically match source | `gateflow connect local --path <db>` |
| `backend` | `local-external` | `gateflow backend migrate --to file` then `gateflow connect local --path <db>` | No semantic diff after transition | `gateflow backend migrate --to backend` |
| `local-external` | `backend` | `gateflow backend migrate --to file` then `gateflow backend migrate --to backend` | Stable ordered roundtrip | `gateflow connect local --path <db>` |

## Failure Paths + Recovery
1. `sync` metadata missing/invalid:
- Symptom: `sync status` or `sync apply` fails with sync error.
- Recovery:
```bash
gateflow --root <repo> sync from-main
gateflow --root <repo> sync status
gateflow --root <repo> sync apply
```

2. Workspace rebind to wrong local DB:
- Symptom: `connect local` fails due to workspace id mismatch.
- Recovery:
```bash
gateflow --root <repo> connect local --path <expected-db>
# emergency recovery only:
gateflow --root <repo> connect local --path <db> --force
```

3. Policy blocks write on drifted branch (`POLICY_SYNC_REQUIRED`):
- Recovery:
```bash
gateflow --root <repo> sync from-main
gateflow --root <repo> sync status
gateflow --root <repo> sync apply
```

4. Need temporary rollback to file-ledger source of truth:
```bash
gateflow --root <repo> backend export
gateflow --root <repo> backend migrate --to file
```

## Validation Evidence
- `tests/test_gateflow_cli_backend_sync.py`
- `tests/test_gateflow_cli_connect_local_external.py`
- `tests/test_gateflow_cli_migration_matrix_v1.py`
