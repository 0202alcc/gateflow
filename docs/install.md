# Installation Paths

## uvx

Run from source checkout:

```bash
uvx --from ./ gateflow --help
```

Run against a workspace:

```bash
uvx --from ./ gateflow --root /path/to/workspace validate all
```

## pipx

```bash
pipx install gateflow
gateflow --help
```

## Build + smoke-check wheel/sdist

```bash
uv run --with build python -m build
uv run --with twine twine check dist/*
uvx --from dist/*.whl gateflow --version
pipx install --force dist/*.whl
gateflow --version
```
