from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from gateflow.io import read_json, write_json

CONNECTION_FILE = ".gateflow/connection.json"
CONNECTION_VERSION = "gateflow_connection_v1"


class ConnectionError(RuntimeError):
    pass


def connection_path(root: Path) -> Path:
    return root / CONNECTION_FILE


def default_external_sqlite_path(workspace_id: str) -> Path:
    root_override = os.environ.get("GATEFLOW_LOCAL_EXTERNAL_ROOT")
    if root_override:
        return Path(root_override).expanduser().resolve() / workspace_id / "gateflow.db"
    return Path.home() / ".gateflow" / "workspaces" / workspace_id / "gateflow.db"


def load_connection(root: Path) -> dict[str, Any]:
    return read_json(connection_path(root))


def ensure_connection_metadata(root: Path) -> tuple[dict[str, Any], bool]:
    path = connection_path(root)
    if path.exists():
        return load_connection(root), False

    workspace_id = compute_workspace_id(root)
    payload = {
        "backend": {
            "kind": "local",
            "path_token": path_to_token(default_external_sqlite_path(workspace_id)),
            "provider": "sqlite",
        },
        "updated_at": date.today().isoformat(),
        "version": CONNECTION_VERSION,
        "workspace_id": workspace_id,
    }
    write_json(path, payload)
    return payload, True


def resolve_local_external_sqlite_path(root: Path) -> Path:
    payload = load_connection(root)
    backend = payload.get("backend")
    if not isinstance(backend, dict):
        raise ConnectionError("connection metadata missing backend object")
    if str(backend.get("kind", "")).lower() != "local":
        raise ConnectionError("connection backend kind must be 'local' for local-external mode")
    if str(backend.get("provider", "")).lower() != "sqlite":
        raise ConnectionError("connection backend provider must be 'sqlite' for local-external mode")
    token = backend.get("path_token")
    if not isinstance(token, str) or token.strip() == "":
        raise ConnectionError("connection backend.path_token must be a non-empty string")
    return token_to_path(token)


def compute_workspace_id(root: Path) -> str:
    descriptor = {
        "git_origin": _git_origin_url(root),
        "git_toplevel": _git_toplevel(root),
        "schema": "gateflow_workspace_identity_v1",
    }
    digest = hashlib.sha256(json.dumps(descriptor, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
    return f"ws-{digest[:16]}"


def path_to_token(path: Path) -> str:
    resolved = path.expanduser().resolve()
    home = Path.home().resolve()
    if resolved == home:
        return "~"
    try:
        rel = resolved.relative_to(home)
    except ValueError:
        return str(resolved)
    return f"~/{rel.as_posix()}"


def token_to_path(token: str) -> Path:
    if token == "~":
        return Path.home()
    if token.startswith("~/"):
        return (Path.home() / token[2:]).resolve()
    return Path(token).expanduser().resolve()


def _git_origin_url(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_toplevel(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return str(root.resolve())
    return str(Path(result.stdout.strip()).resolve())
