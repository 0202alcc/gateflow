from __future__ import annotations

import json
import subprocess
from pathlib import Path

from gateflow.cli import main


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _set_require_sync(root: Path, enabled: bool) -> None:
    path = root / ".gateflow" / "config.json"
    payload = _load(path)
    payload["policy"]["require_sync_before_write"] = enabled
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_init_defaults_to_local_external_and_connection_metadata(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "init"]) == 0
    _ = capsys.readouterr()

    config = _load(tmp_path / ".gateflow" / "config.json")
    connection = _load(tmp_path / ".gateflow" / "connection.json")
    assert config["storage"]["mode"] == "local-external"
    assert connection["backend"]["kind"] == "local"
    assert connection["backend"]["provider"] == "sqlite"
    assert connection["workspace_id"].startswith("ws-")


def test_connect_status_reports_mode_and_target_backend(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "init"]) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "connect", "status"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "local-external"
    assert payload["target_backend"] == "local-sqlite"
    assert payload["connection"]["backend"]["kind"] == "local"


def test_connect_remote_contract_stub(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "init"]) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "connect", "remote", "--url", "https://example.invalid/ws"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "not_implemented"
    assert payload["contract"] == "connect_remote_v1"
    assert "Remote backends are not implemented yet in this milestone." in payload["guidance"]


def test_branch_continuity_uses_same_external_db_across_branches(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "init"]) == 0
    _set_require_sync(tmp_path, False)
    assert main(["--root", str(tmp_path), "config", "set", "policy.protected_branches", "[]"]) == 0
    _ = capsys.readouterr()

    _git("init", "-b", "main", cwd=tmp_path)
    _git("config", "user.email", "dev@example.com", cwd=tmp_path)
    _git("config", "user.name", "Dev", cwd=tmp_path)
    _git("add", ".", cwd=tmp_path)
    _git("commit", "-m", "seed", cwd=tmp_path)

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-LE-1001","title":"main"}']) == 0
    _ = capsys.readouterr()
    _git("add", ".", cwd=tmp_path)
    _git("commit", "-m", "main task", cwd=tmp_path)

    _git("checkout", "-b", "feature/continuity", cwd=tmp_path)
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-LE-1002","title":"feature"}']) == 0
    _ = capsys.readouterr()

    _git("checkout", "main", cwd=tmp_path)
    assert main(["--root", str(tmp_path), "tasks", "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert [row["id"] for row in listed] == ["T-LE-1001", "T-LE-1002"]


def test_rebind_recovery_workflow(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "init"]) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-LE-2001","title":"seed"}']) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "connect", "status"]) == 0
    status_before = json.loads(capsys.readouterr().out)
    old_db = Path(status_before["sqlite_path"])
    new_db = tmp_path / "rebound" / "gateflow.db"

    assert main(["--root", str(tmp_path), "connect", "local", "--path", str(new_db), "--allow-in-repo"]) == 0
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-LE-2002","title":"new-db"}']) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "connect", "local", "--path", str(old_db)]) == 0
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "tasks", "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert [row["id"] for row in listed] == ["T-LE-2001"]


def test_local_external_export_import_roundtrip_deterministic(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "init"]) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-LE-3002","title":"b"}']) == 0
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-LE-3001","title":"a"}']) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "backend", "export"]) == 0
    _ = capsys.readouterr()
    exported = _load(tmp_path / ".gateflow" / "tasks.json")
    assert [row["id"] for row in exported["items"]] == ["T-LE-3001", "T-LE-3002"]

    assert main(["--root", str(tmp_path), "backend", "migrate", "--to", "file"]) == 0
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "connect", "local", "--path", str(tmp_path / "reimport.db"), "--allow-in-repo"]) == 0
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "tasks", "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert [row["id"] for row in listed] == ["T-LE-3001", "T-LE-3002"]
