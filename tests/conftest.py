from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _set_local_external_root(monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory) -> None:
    root = tmp_path_factory.mktemp("local_external_root")
    monkeypatch.setenv("GATEFLOW_LOCAL_EXTERNAL_ROOT", str(Path(root)))
