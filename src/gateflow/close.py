from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gateflow.io import read_json, write_json
from gateflow.resources import ResourceError, get_resource, update_resource
from gateflow.workspace import GateflowWorkspace

ISSUES_FILE = "closeout/closure_issues.json"


class CloseCommandError(RuntimeError):
    pass


@dataclass(frozen=True)
class ClosureIssue:
    entity_type: str
    entity_id: str
    code: str
    message: str
    remediation: str
    created_at: str

    def as_dict(self) -> dict[str, str]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "code": self.code,
            "message": self.message,
            "remediation": self.remediation,
            "created_at": self.created_at,
        }


def close_task(workspace: GateflowWorkspace, task_id: str, heads_up: str | None) -> dict[str, Any]:
    try:
        task = get_resource(workspace, "tasks", task_id)
    except ResourceError as exc:
        raise CloseCommandError(str(exc)) from exc

    resolved_heads_up = _resolve_heads_up(existing=task, heads_up=heads_up)
    if resolved_heads_up is None:
        _raise_with_issue(
            workspace=workspace,
            entity_type="task",
            entity_id=task_id,
            code="GO_NO_GO_HEADS_UP_MISSING",
            message="Task close blocked: missing Go/No-Go heads-up acknowledgement.",
            remediation="Run `gateflow close task <id> --heads-up \"...\"`.",
        )

    deps = task.get("depends_on", [])
    if not isinstance(deps, list):
        deps = []
    task_index = {str(row.get("id", "")): row for row in workspace.list_items("tasks")}

    incomplete_deps: list[str] = []
    for dep in deps:
        dep_id = str(dep)
        dep_task = task_index.get(dep_id)
        if dep_task is None or dep_task.get("status") != "Done":
            incomplete_deps.append(dep_id)
    if incomplete_deps:
        _raise_with_issue(
            workspace=workspace,
            entity_type="task",
            entity_id=task_id,
            code="DEPENDENCY_NOT_DONE",
            message=f"Task close blocked: dependencies not done ({', '.join(sorted(incomplete_deps))}).",
            remediation="Close dependency tasks first, then retry close.",
        )

    update_body: dict[str, Any] = {
        "go_no_go": resolved_heads_up,
    }
    if task.get("status") != "Done":
        update_body["status"] = "Done"
        update_body["actuals"] = task.get("actuals") or _default_actuals()
        update_body["done_gate"] = task.get("done_gate") or _default_done_gate()

    update_resource(workspace, "tasks", task_id, update_body)
    return {
        "status": "closed",
        "entity": "task",
        "id": task_id,
        "go_no_go": resolved_heads_up,
    }


def close_milestone(workspace: GateflowWorkspace, milestone_id: str, heads_up: str | None) -> dict[str, Any]:
    try:
        milestone = get_resource(workspace, "milestones", milestone_id)
    except ResourceError as exc:
        raise CloseCommandError(str(exc)) from exc

    resolved_heads_up = _resolve_heads_up(existing=milestone, heads_up=heads_up)
    if resolved_heads_up is None:
        _raise_with_issue(
            workspace=workspace,
            entity_type="milestone",
            entity_id=milestone_id,
            code="GO_NO_GO_HEADS_UP_MISSING",
            message="Milestone close blocked: missing Go/No-Go heads-up acknowledgement.",
            remediation="Run `gateflow close milestone <id> --heads-up \"...\"`.",
        )

    tasks = workspace.list_items("tasks")
    task_index = {str(row.get("id", "")): row for row in tasks}

    direct_task_ids = milestone.get("task_ids", [])
    if not isinstance(direct_task_ids, list):
        direct_task_ids = []
    milestone_task_ids = {str(tid) for tid in direct_task_ids}
    milestone_task_ids.update(str(row.get("id", "")) for row in tasks if row.get("milestone_id") == milestone_id)
    milestone_task_ids.discard("")

    unresolved: list[str] = []
    for tid in sorted(milestone_task_ids):
        task = task_index.get(tid)
        if task is None or task.get("status") != "Done":
            unresolved.append(tid)

    if unresolved:
        _raise_with_issue(
            workspace=workspace,
            entity_type="milestone",
            entity_id=milestone_id,
            code="TASKS_NOT_DONE",
            message=f"Milestone close blocked: tasks not done ({', '.join(unresolved)}).",
            remediation="Close all milestone tasks, then retry milestone close.",
        )

    update_resource(
        workspace,
        "milestones",
        milestone_id,
        {
            "status": "Complete",
            "go_no_go": resolved_heads_up,
        },
    )
    return {
        "status": "closed",
        "entity": "milestone",
        "id": milestone_id,
        "task_count": len(milestone_task_ids),
        "go_no_go": resolved_heads_up,
    }


def _resolve_heads_up(existing: dict[str, Any], heads_up: str | None) -> dict[str, Any] | None:
    if heads_up is not None and heads_up.strip() != "":
        return {
            "received": True,
            "message": heads_up.strip(),
            "received_at": _timestamp(),
        }
    current = existing.get("go_no_go")
    if isinstance(current, dict) and current.get("received") is True:
        return current
    return None


def _raise_with_issue(
    *,
    workspace: GateflowWorkspace,
    entity_type: str,
    entity_id: str,
    code: str,
    message: str,
    remediation: str,
) -> None:
    issue = ClosureIssue(
        entity_type=entity_type,
        entity_id=entity_id,
        code=code,
        message=message,
        remediation=remediation,
        created_at=_timestamp(),
    )
    _record_issue(workspace.root, issue)
    raise CloseCommandError(message)


def _record_issue(root: Path, issue: ClosureIssue) -> None:
    path = root / ".gateflow" / ISSUES_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        payload = read_json(path)
    else:
        payload = {"items": [], "version": "gateflow_v1"}
    items = payload.get("items")
    if not isinstance(items, list):
        items = []
    items.append(issue.as_dict())
    payload["items"] = sorted(
        items,
        key=lambda row: (
            str(row.get("entity_type", "")),
            str(row.get("entity_id", "")),
            str(row.get("created_at", "")),
            str(row.get("code", "")),
        ),
    )
    payload.setdefault("version", "gateflow_v1")
    payload["updated_at"] = _timestamp()
    write_json(path, payload)


def _default_actuals() -> dict[str, int]:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "wall_time_sec": 0,
        "tool_calls": 0,
        "reopen_count": 0,
    }


def _default_done_gate() -> dict[str, bool]:
    return {
        "success_criteria_met": True,
        "safety_tests_passed": True,
        "implementation_tests_passed": True,
        "edge_case_tests_passed": True,
        "merged_to_main": True,
        "required_checks_passed_on_main": True,
    }


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
