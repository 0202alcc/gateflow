# Pre-Release Notes: `v0.1.0a3`

## Scope

- Added explicit close commands:
  - `gateflow close task <id> --heads-up "..."`
  - `gateflow close milestone <id> --heads-up "..."`
- Enforced closure prechecks:
  - Go/No-Go heads-up required for task/milestone close.
  - Task close blocks when dependencies are not done.
  - Milestone close blocks when linked milestone tasks are not done.
- Added deterministic close issue ledger at `.gateflow/closeout/closure_issues.json`.
- Added `gateflow init` shorthand that defaults to `init scaffold --profile minimal`.

## Publish Checklist

1. Build artifacts:

```bash
cd gateflow
python3 -m build
```

2. Smoke run from built wheel:

```bash
UV_CACHE_DIR=../.uv-cache UV_TOOL_DIR=./.uv-tools uvx --from dist/gateflow-0.1.0a3-py3-none-any.whl gateflow --help
```

3. Push Git tag:

```bash
git tag -a gateflow-v0.1.0a3 -m "gateflow pre-release v0.1.0a3"
git push origin gateflow-v0.1.0a3
```

4. Validate package metadata:

```bash
python3 -m twine check dist/*
```

5. Upload to package index:

```bash
python3 -m twine upload dist/*
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
