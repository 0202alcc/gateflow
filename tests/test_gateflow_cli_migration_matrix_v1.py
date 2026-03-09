from __future__ import annotations

import json
from pathlib import Path

from gateflow.cli import main


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _capture_json(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def _init(root: Path, capsys) -> None:
    assert main(["--root", str(root), "init", "scaffold", "--profile", "minimal"]) == 0
    _ = capsys.readouterr()


def _seed_tasks(root: Path, capsys) -> None:
    assert main(["--root", str(root), "tasks", "create", "--body", '{"id":"T-MX-002","title":"second"}']) == 0
    assert main(["--root", str(root), "tasks", "create", "--body", '{"id":"T-MX-001","title":"first"}']) == 0
    _ = capsys.readouterr()


def _task_ids(root: Path) -> list[str]:
    return [row["id"] for row in _load(root / ".gateflow" / "tasks.json")["items"]]


def test_migration_matrix_is_deterministic_across_storage_modes(tmp_path: Path, capsys) -> None:
    _init(tmp_path, capsys)
    _seed_tasks(tmp_path, capsys)

    assert _task_ids(tmp_path) == ["T-MX-001", "T-MX-002"]

    assert main(["--root", str(tmp_path), "backend", "migrate", "--to", "file"]) == 0
    payload = _capture_json(capsys)
    assert payload["mode"] == "file"
    assert _task_ids(tmp_path) == ["T-MX-001", "T-MX-002"]

    assert main(["--root", str(tmp_path), "backend", "migrate", "--to", "backend"]) == 0
    payload = _capture_json(capsys)
    assert payload["mode"] == "backend"

    assert main(["--root", str(tmp_path), "backend", "migrate", "--to", "file"]) == 0
    payload = _capture_json(capsys)
    assert payload["mode"] == "file"
    assert _task_ids(tmp_path) == ["T-MX-001", "T-MX-002"]

    rebound = tmp_path / "migration-matrix" / "local-external.db"
    assert main(["--root", str(tmp_path), "connect", "local", "--path", str(rebound), "--allow-in-repo"]) == 0
    payload = _capture_json(capsys)
    assert payload["mode"] == "local-external"

    assert main(["--root", str(tmp_path), "backend", "export"]) == 0
    _ = _capture_json(capsys)
    assert _task_ids(tmp_path) == ["T-MX-001", "T-MX-002"]


def test_sync_failure_paths_emit_recovery_commands(tmp_path: Path, capsys) -> None:
    _init(tmp_path, capsys)

    rc = main(["--root", str(tmp_path), "sync", "status"])
    assert rc == 3
    out = capsys.readouterr().out
    assert "sync metadata missing" in out
    assert "sync from-main" in out

    rc = main(["--root", str(tmp_path), "sync", "apply"])
    assert rc == 3
    out = capsys.readouterr().out
    assert "sync metadata missing" in out
    assert "sync from-main" in out


def test_connect_local_workspace_mismatch_has_recovery_path(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    _init(source, capsys)
    _init(target, capsys)

    assert main(["--root", str(target), "connect", "status"]) == 0
    target_db = Path(_capture_json(capsys)["sqlite_path"])

    rc = main(["--root", str(source), "connect", "local", "--path", str(target_db)])
    assert rc == 2
    out = capsys.readouterr().out
    assert "different workspace_id" in out
    assert "--force" in out
