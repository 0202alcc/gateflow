from __future__ import annotations

import json
from pathlib import Path

from gateflow.cli import main


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _seed(root: Path) -> None:
    assert main(["--root", str(root), "init", "scaffold", "--profile", "minimal"]) == 0


def _done_body() -> str:
    return json.dumps(
        {
            "status": "Done",
            "actuals": {
                "input_tokens": 1,
                "output_tokens": 1,
                "wall_time_sec": 1,
                "tool_calls": 1,
                "reopen_count": 0,
            },
            "done_gate": {
                "success_criteria_met": True,
                "safety_tests_passed": True,
                "implementation_tests_passed": True,
                "edge_case_tests_passed": True,
                "merged_to_main": True,
                "required_checks_passed_on_main": True,
            },
            "go_no_go": {
                "received": True,
                "message": "reviewed",
                "received_at": "2026-03-08T00:00:00+00:00",
            },
        },
        sort_keys=True,
    )


def test_close_task_requires_heads_up_and_records_issue(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-1"}']) == 0
    _ = capsys.readouterr()

    rc = main(["--root", str(tmp_path), "close", "task", "T-1"])
    assert rc == 2
    assert "missing Go/No-Go heads-up" in capsys.readouterr().out

    issues = _load(tmp_path / ".gateflow" / "closeout" / "closure_issues.json")
    assert issues["items"][-1]["entity_type"] == "task"
    assert issues["items"][-1]["entity_id"] == "T-1"
    assert issues["items"][-1]["code"] == "GO_NO_GO_HEADS_UP_MISSING"


def test_close_task_requires_dependency_done(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-dep"}']) == 0
    assert main(
        [
            "--root",
            str(tmp_path),
            "tasks",
            "create",
            "--body",
            '{"id":"T-main","depends_on":["T-dep"]}',
        ]
    ) == 0
    _ = capsys.readouterr()

    rc = main(["--root", str(tmp_path), "close", "task", "T-main", "--heads-up", "approved"]) 
    assert rc == 2
    assert "dependencies not done" in capsys.readouterr().out


def test_close_task_success_sets_done_defaults(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    _ = capsys.readouterr()
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-2"}']) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "close", "task", "T-2", "--heads-up", "approved"]) == 0
    _ = capsys.readouterr()
    task = _load(tmp_path / ".gateflow" / "tasks.json")["items"][0]
    assert task["status"] == "Done"
    assert task["go_no_go"]["received"] is True
    assert task["done_gate"]["required_checks_passed_on_main"] is True


def test_close_milestone_requires_all_tasks_done_and_records_issue(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    _ = capsys.readouterr()
    assert main(
        [
            "--root",
            str(tmp_path),
            "milestones",
            "create",
            "--body",
            '{"id":"M-1","task_ids":["T-10"]}',
        ]
    ) == 0
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-10","milestone_id":"M-1"}']) == 0
    _ = capsys.readouterr()

    rc = main(["--root", str(tmp_path), "close", "milestone", "M-1", "--heads-up", "approved"])
    assert rc == 2
    assert "tasks not done" in capsys.readouterr().out
    issues = _load(tmp_path / ".gateflow" / "closeout" / "closure_issues.json")
    assert issues["items"][-1]["entity_type"] == "milestone"
    assert issues["items"][-1]["code"] == "TASKS_NOT_DONE"


def test_close_milestone_success(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    _ = capsys.readouterr()
    assert main(
        [
            "--root",
            str(tmp_path),
            "milestones",
            "create",
            "--body",
            '{"id":"M-2","task_ids":["T-20"]}',
        ]
    ) == 0
    assert main(["--root", str(tmp_path), "tasks", "create", "--body", '{"id":"T-20","milestone_id":"M-2"}']) == 0
    assert main(["--root", str(tmp_path), "tasks", "update", "T-20", "--body", _done_body()]) == 0
    _ = capsys.readouterr()

    assert main(["--root", str(tmp_path), "close", "milestone", "M-2", "--heads-up", "ship it"]) == 0
    _ = capsys.readouterr()
    milestone = _load(tmp_path / ".gateflow" / "milestones.json")["items"][0]
    assert milestone["status"] == "Complete"
    assert milestone["go_no_go"]["received"] is True
