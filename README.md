# Dotloop MCP

Read-first MCP server for Dotloop.

This initial implementation wraps `dotloop==1.3.2` behind service adapters and
exposes safe read tools for account, profiles, loops, loop details, folders,
documents, participants, tasks, activity, and templates. State-changing tools
remain deferred by the planning docs under `docs/planning/dotloop-mcp-buildout/`.

## MCP resources

- `dotloop://api-coverage-matrix`: domain-level library and MCP exposure status.
- `dotloop://library-method-coverage`: method-level `dotloop==1.3.2` coverage
  generated from the installed package surface.

The local `docs/` tree is intentionally ignored by this repo. Runtime coverage
resources and `make validate` are self-contained for clean checkouts without
local planning docs.

## Install

```bash
uv sync
```

## Configure

Set a local Dotloop access token outside version control:

```bash
export DOTLOOP_ACCESS_TOKEN="..."
```

The legacy `DOTLOOP_API_KEY` variable is also accepted because the underlying
`dotloop` package uses that name.

## Run

```bash
uv run python -m dotloop_mcp.cli stdio
uv run python -m dotloop_mcp.cli streamable-http --host 127.0.0.1 --port 8000 --path /mcp
```

## Validate

```bash
make validate
```

Live checks are disabled by default and require explicit opt-in:

```bash
make live-readiness-check
DOTLOOP_RUN_LIVE_TESTS=1 make live-identity-check
```
