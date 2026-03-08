from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gateflow.storage import LEDGER_FILES, Storage, get_storage


@dataclass(frozen=True)
class GateflowWorkspace:
    root: Path

    @property
    def gateflow_dir(self) -> Path:
        return self.root / ".gateflow"

    @property
    def storage(self) -> Storage:
        return get_storage(self.root)

    def ledger_path(self, resource: str) -> Path:
        if resource in LEDGER_FILES:
            return self.gateflow_dir / LEDGER_FILES[resource]
        if resource == "frameworks":
            return self.gateflow_dir / "config.json"
        raise ValueError(f"unsupported resource: {resource}")

    def list_items(self, resource: str) -> list[dict[str, Any]]:
        return self.storage.list_items(resource)

    def write_items(self, resource: str, items: list[dict[str, Any]]) -> None:
        self.storage.write_items(resource, items)
