from __future__ import annotations

import json
import subprocess
from pathlib import Path

from gateflow.cli import main


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _seed(root: Path) -> None:
    assert main(["--root", str(root), "init", "scaffold", "--profile", "minimal"]) == 0


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _capture_json(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def test_backend_roundtrip_file_to_sqlite_to_file(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-1002","title":"second"}']) == 0
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-1001","title":"first"}']) == 0
    _ = capsys.readouterr()

    before = _load(tmp_path / ".gateflow" / "tasks.json")
    assert [row["id"] for row in before["items"]] == ["T-1001", "T-1002"]

    assert main(["--root", str(tmp_path), "backend", "migrate", "--to", "backend"]) == 0
    payload = _capture_json(capsys)
    assert payload["mode"] == "backend"

    assert main(["--root", str(tmp_path), "tasks", "list"]) == 0
    listed = _capture_json(capsys)
    assert [row["id"] for row in listed] == ["T-1001", "T-1002"]

    assert main(["--root", str(tmp_path), "backend", "migrate", "--to", "file"]) == 0
    payload = _capture_json(capsys)
    assert payload["mode"] == "file"

    after = _load(tmp_path / ".gateflow" / "tasks.json")
    assert after["items"] == before["items"]


def test_sync_from_main_detects_drift_and_apply_resolves(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "config", "set", "policy.protected_branches", "[]"]) == 0
    _ = capsys.readouterr()
    _git("init", "-b", "main", cwd=tmp_path)
    _git("config", "user.email", "dev@example.com", cwd=tmp_path)
    _git("config", "user.name", "Dev", cwd=tmp_path)

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-2001","title":"main"}']) == 0
    _ = capsys.readouterr()
    _git("add", ".", cwd=tmp_path)
    _git("commit", "-m", "seed main", cwd=tmp_path)
    _git("checkout", "-b", "feature/test-sync", cwd=tmp_path)

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-2999","title":"feature"}']) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "sync", "from-main"]) == 0
    from_main = _capture_json(capsys)
    assert from_main["drift"]["conflict_count"] >= 1

    assert main(["--root", str(tmp_path), "sync", "status"]) == 0
    status = _capture_json(capsys)
    assert status["status"] == "drifted"

    assert main(["--root", str(tmp_path), "sync", "apply"]) == 0
    apply_payload = _capture_json(capsys)
    assert apply_payload["drift"]["conflict_count"] == 0

    assert main(["--root", str(tmp_path), "tasks", "list"]) == 0
    listed = _capture_json(capsys)
    assert [row["id"] for row in listed] == ["T-2001"]


def test_require_sync_policy_blocks_writes_until_clean(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "config", "set", "policy.protected_branches", "[]"]) == 0
    _ = capsys.readouterr()
    _git("init", "-b", "main", cwd=tmp_path)
    _git("config", "user.email", "dev@example.com", cwd=tmp_path)
    _git("config", "user.name", "Dev", cwd=tmp_path)

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-3001"}']) == 0
    _ = capsys.readouterr()
    _git("add", ".", cwd=tmp_path)
    _git("commit", "-m", "seed", cwd=tmp_path)
    _git("checkout", "-b", "feature/require-sync", cwd=tmp_path)

    assert main(["--root", str(tmp_path), "sync", "from-main"]) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-3002"}']) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "config", "set", "policy.require_sync_before_write", "true"]) == 0
    _ = capsys.readouterr()

    rc = main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-3003"}'])
    assert rc == 3
    assert "POLICY_SYNC_REQUIRED" in capsys.readouterr().out

    assert main(["--root", str(tmp_path), "sync", "apply"]) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-3004"}']) == 0
