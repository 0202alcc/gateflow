from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from gateflow.connection import resolve_local_external_sqlite_path
from gateflow.io import read_json, write_json

RESOURCE_KEYS = ("milestones", "tasks", "boards", "frameworks", "backlog", "closeout_refs")
LEDGER_FILES = {
    "milestones": "milestones.json",
    "tasks": "tasks.json",
    "boards": "boards.json",
    "backlog": "backlog.json",
    "closeout_refs": "closeout/metadata_refs.json",
}


class StorageError(RuntimeError):
    pass


class StorageLockTimeout(StorageError):
    pass


@dataclass(frozen=True)
class StorageMode:
    mode: str
    sqlite_path: Path


class Storage:
    def list_items(self, resource: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def write_items(self, resource: str, items: list[dict[str, Any]]) -> None:
        raise NotImplementedError

    def read_meta(self, key: str) -> Any:
        raise NotImplementedError

    def write_meta(self, key: str, value: Any) -> None:
        raise NotImplementedError


class FileStorage(Storage):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.gateflow_dir = root / ".gateflow"
        self._meta_path = self.gateflow_dir / "sync_state.json"
        self._lock_path = self.gateflow_dir / ".write.lock"

    def list_items(self, resource: str) -> list[dict[str, Any]]:
        if resource == "frameworks":
            config = read_json(self.gateflow_dir / "config.json")
            return _sort_items(list(config.get("frameworks", [])), resource=resource)

        if resource not in LEDGER_FILES:
            raise ValueError(f"unsupported resource: {resource}")
        ledger = read_json(self.gateflow_dir / LEDGER_FILES[resource])
        return _sort_items(list(ledger.get("items", [])), resource=resource)

    def write_items(self, resource: str, items: list[dict[str, Any]]) -> None:
        with _file_lock(self._lock_path):
            ordered = _sort_items(items, resource=resource)
            if resource == "frameworks":
                config_path = self.gateflow_dir / "config.json"
                config = read_json(config_path)
                config["frameworks"] = ordered
                write_json(config_path, config)
                return

            if resource not in LEDGER_FILES:
                raise ValueError(f"unsupported resource: {resource}")
            ledger_path = self.gateflow_dir / LEDGER_FILES[resource]
            ledger = read_json(ledger_path)
            ledger["items"] = ordered
            write_json(ledger_path, ledger)

    def read_meta(self, key: str) -> Any:
        if not self._meta_path.exists():
            return None
        payload = read_json(self._meta_path)
        return payload.get(key)

    def write_meta(self, key: str, value: Any) -> None:
        with _file_lock(self._lock_path):
            if self._meta_path.exists():
                payload = read_json(self._meta_path)
            else:
                payload = {}
            payload[key] = value
            write_json(self._meta_path, payload)


class SQLiteStorage(Storage):
    def __init__(self, root: Path, sqlite_path: Path) -> None:
        self.root = root
        self.sqlite_path = sqlite_path
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def list_items(self, resource: str) -> list[dict[str, Any]]:
        if resource not in RESOURCE_KEYS:
            raise ValueError(f"unsupported resource: {resource}")
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM records WHERE resource = ? ORDER BY item_id",
                (resource,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def write_items(self, resource: str, items: list[dict[str, Any]]) -> None:
        if resource not in RESOURCE_KEYS:
            raise ValueError(f"unsupported resource: {resource}")
        ordered = _sort_items(items, resource=resource)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM records WHERE resource = ?", (resource,))
            for item in ordered:
                conn.execute(
                    "INSERT INTO records(resource, item_id, payload) VALUES(?, ?, ?)",
                    (resource, _item_key(resource, item), json.dumps(item, sort_keys=True, ensure_ascii=True)),
                )
            conn.commit()

    def read_meta(self, key: str) -> Any:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def write_meta(self, key: str, value: Any) -> None:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO metadata(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, sort_keys=True, ensure_ascii=True)),
            )
            conn.commit()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS records("
                "resource TEXT NOT NULL,"
                "item_id TEXT NOT NULL,"
                "payload TEXT NOT NULL,"
                "PRIMARY KEY(resource, item_id)"
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS metadata(" "key TEXT PRIMARY KEY," "value TEXT NOT NULL" ")"
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn


class LocalExternalStorage(SQLiteStorage):
    def __init__(self, root: Path, sqlite_path: Path) -> None:
        super().__init__(root=root, sqlite_path=sqlite_path)
        self._mirror = FileStorage(root=root)

    def write_items(self, resource: str, items: list[dict[str, Any]]) -> None:
        ordered = _sort_items(items, resource=resource)
        super().write_items(resource, ordered)
        self._mirror.write_items(resource, ordered)


def resolve_storage_mode(root: Path) -> StorageMode:
    config = read_json(root / ".gateflow" / "config.json")
    storage_cfg = config.get("storage", {})
    mode = str(storage_cfg.get("mode", "file")).strip().lower()
    mode_override = os.environ.get("GATEFLOW_STORAGE_MODE")
    if mode_override:
        mode = mode_override.strip().lower()
    sqlite_path = resolve_configured_backend_sqlite_path(root)
    if mode == "local-external":
        sqlite_path = resolve_local_external_sqlite_path(root)
    if mode not in {"file", "backend", "local-external"}:
        raise ValueError("config storage.mode must be 'file', 'backend', or 'local-external'")
    return StorageMode(mode=mode, sqlite_path=sqlite_path)


def resolve_configured_backend_sqlite_path(root: Path) -> Path:
    config = read_json(root / ".gateflow" / "config.json")
    storage_cfg = config.get("storage", {})
    sqlite_rel = str(storage_cfg.get("sqlite_path", ".gateflow/gateflow.db"))
    return (root / sqlite_rel).resolve() if not Path(sqlite_rel).is_absolute() else Path(sqlite_rel)


def get_storage(root: Path) -> Storage:
    mode = resolve_storage_mode(root)
    if mode.mode == "backend":
        return SQLiteStorage(root=root, sqlite_path=mode.sqlite_path)
    if mode.mode == "local-external":
        return LocalExternalStorage(root=root, sqlite_path=mode.sqlite_path)
    return FileStorage(root=root)


def import_json_ledgers_to_backend(root: Path, sqlite_path: Path) -> None:
    storage = SQLiteStorage(root=root, sqlite_path=sqlite_path)
    file_storage = FileStorage(root=root)
    for resource in RESOURCE_KEYS:
        storage.write_items(resource, file_storage.list_items(resource))
    sync_state = file_storage.read_meta("sync")
    if sync_state is not None:
        storage.write_meta("sync", sync_state)


def export_backend_to_json_ledgers(root: Path, sqlite_path: Path) -> None:
    storage = SQLiteStorage(root=root, sqlite_path=sqlite_path)
    file_storage = FileStorage(root=root)
    for resource in RESOURCE_KEYS:
        file_storage.write_items(resource, storage.list_items(resource))
    sync_state = storage.read_meta("sync")
    if sync_state is not None:
        file_storage.write_meta("sync", sync_state)


def _sort_items(items: list[dict[str, Any]], *, resource: str) -> list[dict[str, Any]]:
    return sorted(items, key=lambda row: _item_key(resource, row))


def _item_key(resource: str, item: dict[str, Any]) -> str:
    if resource == "frameworks":
        key = item.get("name")
    else:
        key = item.get("id", item.get("name", ""))
    return str(key)


@contextmanager
def _file_lock(lock_path: Path, timeout_sec: float = 3.0, poll_sec: float = 0.05) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    while True:
        try:
            fd = lock_path.open("x", encoding="utf-8")
            fd.write(str(time.time()))
            fd.close()
            break
        except FileExistsError:
            if time.monotonic() - start >= timeout_sec:
                raise StorageLockTimeout(f"timed out waiting for write lock: {lock_path}")
            time.sleep(poll_sec)

    try:
        yield
    finally:
        if lock_path.exists():
            lock_path.unlink()
