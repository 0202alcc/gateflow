from __future__ import annotations

from pathlib import Path
from typing import Any

from gateflow.config import set_config_value, show_config
from gateflow.storage import (
    export_backend_to_json_ledgers,
    import_json_ledgers_to_backend,
    resolve_storage_mode,
)


def backend_status(root: Path) -> dict[str, Any]:
    mode = resolve_storage_mode(root)
    config = show_config(root)
    return {
        "mode": mode.mode,
        "sqlite_path": str(mode.sqlite_path),
        "policy_require_sync_before_write": bool(config.get("policy", {}).get("require_sync_before_write", False)),
    }


def backend_migrate(root: Path, to_mode: str) -> dict[str, Any]:
    to_mode = to_mode.strip().lower()
    mode = resolve_storage_mode(root)
    if to_mode not in {"file", "backend"}:
        raise ValueError("backend migrate --to must be 'file' or 'backend'")

    if to_mode == mode.mode:
        return {"status": "noop", "mode": mode.mode, "sqlite_path": str(mode.sqlite_path)}

    if to_mode == "backend":
        import_json_ledgers_to_backend(root, mode.sqlite_path)
        set_config_value(root, "storage.mode", '"backend"')
        return {
            "status": "ok",
            "mode": "backend",
            "sqlite_path": str(mode.sqlite_path),
            "rollback": "gateflow backend migrate --to file",
        }

    export_backend_to_json_ledgers(root, mode.sqlite_path)
    set_config_value(root, "storage.mode", '"file"')
    return {
        "status": "ok",
        "mode": "file",
        "sqlite_path": str(mode.sqlite_path),
        "rollback": "gateflow backend migrate --to backend",
    }


def backend_export(root: Path) -> dict[str, Any]:
    mode = resolve_storage_mode(root)
    export_backend_to_json_ledgers(root, mode.sqlite_path)
    return {
        "status": "ok",
        "exported_to": str(root / ".gateflow"),
        "sqlite_path": str(mode.sqlite_path),
    }
