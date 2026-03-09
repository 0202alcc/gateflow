# Release Notes: `v1.0.0`

## Scope

- v1 contract lock for CLI/API behavior, error contracts, and storage-mode parity.
- Deterministic migration/rollback matrix validated across `file`, `backend`, and `local-external`.
- Planning standardization gates enforced in CI + branch protection.
- Reproducible packaging pipeline and install smoke paths (`uv`, `pipx`, wheel/sdist).
- Finalized operator runbooks with sync/drift/connect/storage rollback playbooks.

## Publish Checklist

1. Build artifacts:

```bash
UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools uv run --with build python -m build
```

2. Validate package metadata:

```bash
UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools uv run --with twine twine check dist/*
```

3. Smoke install paths:

```bash
UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools uvx --from dist/*.whl gateflow --version
pipx install --force dist/*.whl
gateflow --version
```

4. Tag guidance:

```bash
git tag -a gateflow-v1.0.0 -m "gateflow v1.0.0"
git push origin gateflow-v1.0.0
```

## Validation Evidence

- `uv run pytest tests/test_gateflow_cli_backend_sync.py -q`
- `uv run pytest tests/test_gateflow_cli_connect_local_external.py -q`
- `uv run pytest tests/test_gateflow_cli_migration_matrix_v1.py -q`
- `uv run pytest tests/test_gateflow_cli_close.py -q`
