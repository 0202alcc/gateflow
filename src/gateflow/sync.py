from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gateflow.storage import RESOURCE_KEYS, get_storage

SYNC_META_KEY = "sync"
SYNC_RESOURCES = [resource for resource in RESOURCE_KEYS if resource != "frameworks"] + ["frameworks"]


class SyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class DriftEntry:
    resource: str
    item_id: str
    code: str

    def as_dict(self) -> dict[str, str]:
        return {"resource": self.resource, "item_id": self.item_id, "code": self.code}


def sync_from_main(root: Path) -> dict[str, Any]:
    storage = get_storage(root)
    commit = _resolve_main_commit(root)
    baseline = _load_main_snapshot(root, commit)
    metadata = {
        "source_ref": "main",
        "source_commit": commit,
        "captured_at": _timestamp(),
        "baseline": baseline,
    }
    storage.write_meta(SYNC_META_KEY, metadata)
    status = sync_status(root)
    return {
        "status": "ok",
        "source_commit": commit,
        "captured_at": metadata["captured_at"],
        "drift": status["drift"],
        "remediation": status["remediation"],
    }


def sync_status(root: Path) -> dict[str, Any]:
    storage = get_storage(root)
    metadata = storage.read_meta(SYNC_META_KEY)
    if not isinstance(metadata, dict):
        raise SyncError("sync metadata missing; run `gateflow sync from-main` first")
    baseline = metadata.get("baseline")
    if not isinstance(baseline, dict):
        raise SyncError("sync metadata is invalid; run `gateflow sync from-main` again")

    current = {resource: storage.list_items(resource) for resource in SYNC_RESOURCES}
    drift_entries = _drift_entries(baseline=baseline, current=current)
    is_clean = len(drift_entries) == 0
    summary = {
        "conflict_count": len(drift_entries),
        "resources": sorted({entry.resource for entry in drift_entries}),
    }
    return {
        "status": "clean" if is_clean else "drifted",
        "source_commit": metadata.get("source_commit"),
        "captured_at": metadata.get("captured_at"),
        "last_apply_at": metadata.get("last_apply_at"),
        "drift": {
            **summary,
            "conflicts": [entry.as_dict() for entry in drift_entries],
        },
        "remediation": [
            "gateflow sync from-main",
            "gateflow sync apply",
            "gateflow sync status",
        ],
    }


def sync_apply(root: Path) -> dict[str, Any]:
    storage = get_storage(root)
    metadata = storage.read_meta(SYNC_META_KEY)
    if not isinstance(metadata, dict):
        raise SyncError("sync metadata missing; run `gateflow sync from-main` first")
    baseline = metadata.get("baseline")
    if not isinstance(baseline, dict):
        raise SyncError("sync metadata is invalid; run `gateflow sync from-main` again")

    for resource in SYNC_RESOURCES:
        rows = baseline.get(resource, [])
        if not isinstance(rows, list):
            raise SyncError(f"sync baseline for {resource} is invalid")
        storage.write_items(resource, [dict(row) for row in rows])

    metadata["last_apply_at"] = _timestamp()
    storage.write_meta(SYNC_META_KEY, metadata)
    status = sync_status(root)
    return {
        "status": "ok",
        "applied_at": metadata["last_apply_at"],
        "source_commit": metadata.get("source_commit"),
        "drift": status["drift"],
    }


def require_synced_writes(root: Path) -> None:
    status = sync_status(root)
    if status["status"] != "clean":
        raise SyncError(
            "POLICY_SYNC_REQUIRED: writes are blocked until branch is synced; "
            "run `gateflow sync from-main` then `gateflow sync apply`"
        )


def _resolve_main_commit(root: Path) -> str:
    for ref in ("main", "origin/main"):
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", ref],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    raise SyncError("unable to resolve main branch commit (looked for main and origin/main)")


def _load_main_snapshot(root: Path, commit: str) -> dict[str, list[dict[str, Any]]]:
    snapshot: dict[str, list[dict[str, Any]]] = {}
    for resource in SYNC_RESOURCES:
        snapshot[resource] = _read_resource_from_git(root, commit, resource)
    return snapshot


def _read_resource_from_git(root: Path, commit: str, resource: str) -> list[dict[str, Any]]:
    if resource == "frameworks":
        payload = _git_show_json(root, commit, ".gateflow/config.json")
        frameworks = payload.get("frameworks", [])
        return _normalize_rows(frameworks)

    if resource == "closeout_refs":
        path = ".gateflow/closeout/metadata_refs.json"
    else:
        path = f".gateflow/{resource}.json"

    payload = _git_show_json(root, commit, path, allow_missing=(resource == "closeout_refs"))
    return _normalize_rows(payload.get("items", []))


def _git_show_json(root: Path, commit: str, path: str, allow_missing: bool = False) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if allow_missing:
            return {"items": []}
        raise SyncError(f"unable to read canonical snapshot file from main: {path}")
    return json.loads(result.stdout)


def _normalize_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized = [dict(row) for row in rows if isinstance(row, dict)]
    return sorted(normalized, key=lambda row: str(row.get("id", row.get("name", ""))))


def _drift_entries(*, baseline: dict[str, Any], current: dict[str, Any]) -> list[DriftEntry]:
    entries: list[DriftEntry] = []
    for resource in SYNC_RESOURCES:
        base_rows = baseline.get(resource, [])
        now_rows = current.get(resource, [])
        base_index = _index_rows(base_rows, resource)
        now_index = _index_rows(now_rows, resource)

        all_ids = sorted(set(base_index.keys()) | set(now_index.keys()))
        for item_id in all_ids:
            if item_id not in base_index:
                entries.append(DriftEntry(resource=resource, item_id=item_id, code="extra_on_branch"))
            elif item_id not in now_index:
                entries.append(DriftEntry(resource=resource, item_id=item_id, code="missing_from_branch"))
            elif _stable_json(base_index[item_id]) != _stable_json(now_index[item_id]):
                entries.append(DriftEntry(resource=resource, item_id=item_id, code="content_mismatch"))
    return entries


def _index_rows(rows: Any, resource: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return index
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = row.get("name") if resource == "frameworks" else row.get("id", row.get("name", ""))
        index[str(key)] = row
    return index


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
