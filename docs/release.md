# Pre-Release Notes: `v0.1.0a4`

## Scope

- Added default `local-external` source-of-truth mode for new `gateflow init` workspaces.
- Added deterministic workspace connection metadata in `.gateflow/connection.json`.
- Added `gateflow connect` command surface:
  - `connect local` implemented for explicit local DB rebinding.
  - `connect remote` contract stub added for future hosted backends.
- Updated backend smoke coverage and integration tests for local-external behavior.
- Added planning packet/closeout artifacts for `GATEFLOW-LOCAL-EXTERNAL-003`.

## Publish Checklist

1. Build artifacts:

```bash
UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools uv run --with build python -m build
```

2. Validate package metadata:

```bash
UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools uv run --with twine twine check dist/*
```

3. Upload to package index:

```bash
UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools uv run --with twine twine upload dist/*
```

4. Push Git tag:

```bash
git tag -a gateflow-v0.1.0a4 -m "gateflow pre-release v0.1.0a4"
git push origin gateflow-v0.1.0a4
```

## Validation Evidence

- `PYTHONPATH=src python3 -m pytest tests -q`
- `PYTHONPATH=src python3 -m gateflow.cli --help`

## Install Paths

```bash
pipx install gateflow
gateflow --help
```

```bash
uvx --from ./gateflow gateflow --help
```
