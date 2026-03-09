# gateflow

Standalone GateFlow CLI package extracted from Luvatrix.

Current release version: `1.0.0`.

## Install and Run

### `uvx`

```bash
UV_CACHE_DIR=./.uv-cache UV_TOOL_DIR=./.uv-tools uvx --from ./ gateflow --help
```

### Local editable install

```bash
uv sync
uv run gateflow --help
```

### `pipx`

```bash
pipx install gateflow
gateflow --help
```

## Command Surface

Stable v1 groups:

- `init`
- `config`
- `validate`
- `api`
- `render`
- `import-luvatrix`
- `backend`
- `connect`
- `sync`
- `close`
- `milestones`
- `tasks`
- `boards`
- `frameworks`
- `backlog`
- `closeout-refs`

See v1 contract details in `docs/v1-compatibility-contract.md`.
