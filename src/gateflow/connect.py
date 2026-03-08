from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from gateflow.config import set_config_value
from gateflow.connection import (
    CONNECTION_VERSION,
    default_external_sqlite_path,
    ensure_connection_metadata,
    load_connection,
    path_to_token,
    resolve_local_external_sqlite_path,
    token_to_path,
)
from gateflow.io import write_json
from gateflow.storage import RESOURCE_KEYS, SQLiteStorage, get_storage, resolve_storage_mode


class ConnectError(RuntimeError):
    pass


def connect_status(root: Path) -> dict[str, Any]:
    mode = resolve_storage_mode(root)
    payload: dict[str, Any] = {
        "mode": mode.mode,
        "target_backend": "local-sqlite" if mode.mode in {"backend", "local-external"} else "file-ledgers",
    }
    if mode.mode == "local-external":
        connection = load_connection(root)
        payload["connection"] = connection
        payload["sqlite_path"] = str(resolve_local_external_sqlite_path(root))
    elif mode.mode == "backend":
        payload["sqlite_path"] = str(mode.sqlite_path)
    return payload


def connect_local(root: Path, *, path: Path, force: bool, allow_in_repo: bool) -> dict[str, Any]:
    current_storage = get_storage(root)
    resolved = path.expanduser()
    resolved = resolved if resolved.is_absolute() else (root / resolved)
    sqlite_path = resolved.resolve()

    if _is_within(sqlite_path, root.resolve()) and not allow_in_repo:
        raise ConnectError("connect local refuses repo-internal DB path; pass --allow-in-repo to override")

    connection, _created = ensure_connection_metadata(root)
    workspace_id = str(connection.get("workspace_id", ""))
    if workspace_id == "":
        raise ConnectError("connection metadata missing workspace_id")

    target_storage = SQLiteStorage(root=root, sqlite_path=sqlite_path)
    target_workspace_id = target_storage.read_meta("workspace_id")
    if target_workspace_id is not None and str(target_workspace_id) != workspace_id and not force:
        raise ConnectError(
            "target DB is already bound to a different workspace_id; pass --force to rebind for recovery"
        )

    if force or _is_empty_storage(target_storage):
        _copy_storage_state(current_storage=current_storage, target_storage=target_storage)
    target_storage.write_meta("workspace_id", workspace_id)

    _write_connection(
        root=root,
        workspace_id=workspace_id,
        path_token=path_to_token(sqlite_path),
    )
    set_config_value(root, "storage.mode", '"local-external"')
    set_config_value(root, "storage.provider", '"sqlite"')

    return {
        "status": "ok",
        "mode": "local-external",
        "sqlite_path": str(sqlite_path),
        "workspace_id": workspace_id,
        "rollback": "gateflow config set storage.mode '\"file\"'",
    }


def connect_remote_stub(root: Path, *, url: str, workspace: str | None) -> dict[str, Any]:
    ensure_connection_metadata(root)
    mode = resolve_storage_mode(root)
    return {
        "status": "not_implemented",
        "contract": "connect_remote_v1",
        "requested": {
            "mode_before": mode.mode,
            "url": url,
            "workspace": workspace,
        },
        "guidance": [
            "Remote backends are not implemented yet in this milestone.",
            "Use `gateflow connect local --path <sqlite-db>` for single-user continuity.",
            "Keep deterministic snapshots with `gateflow backend export` when needed.",
        ],
    }


def bootstrap_local_external_connection(root: Path) -> dict[str, Any]:
    connection, _created = ensure_connection_metadata(root)
    workspace_id = str(connection["workspace_id"])
    sqlite_path = token_to_path(str(connection["backend"]["path_token"]))
    storage = SQLiteStorage(root=root, sqlite_path=sqlite_path)
    if storage.read_meta("workspace_id") is None:
        storage.write_meta("workspace_id", workspace_id)
    return {
        "workspace_id": workspace_id,
        "sqlite_path": str(sqlite_path),
    }


def ensure_default_local_external_connection(root: Path) -> dict[str, Any]:
    connection, _ = ensure_connection_metadata(root)
    workspace_id = str(connection["workspace_id"])
    configured_path = connection.get("backend", {}).get("path_token")
    if not isinstance(configured_path, str) or configured_path.strip() == "":
        configured_path = path_to_token(default_external_sqlite_path(workspace_id))
    _write_connection(root=root, workspace_id=workspace_id, path_token=str(configured_path))
    return bootstrap_local_external_connection(root)


def _write_connection(*, root: Path, workspace_id: str, path_token: str) -> None:
    payload = {
        "backend": {
            "kind": "local",
            "path_token": path_token,
            "provider": "sqlite",
        },
        "updated_at": date.today().isoformat(),
        "version": CONNECTION_VERSION,
        "workspace_id": workspace_id,
    }
    write_json(root / ".gateflow" / "connection.json", payload)


def _copy_storage_state(*, current_storage: Any, target_storage: SQLiteStorage) -> None:
    for resource in RESOURCE_KEYS:
        target_storage.write_items(resource, current_storage.list_items(resource))
    sync_state = current_storage.read_meta("sync")
    if sync_state is not None:
        target_storage.write_meta("sync", sync_state)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _is_empty_storage(storage: SQLiteStorage) -> bool:
    for resource in RESOURCE_KEYS:
        if storage.list_items(resource):
            return False
    return True
