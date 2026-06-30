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

Use `.env.example` for the supported non-secret variable names. Keep real
values in your shell or a local ignored `.env` file. The server and live
readiness check load `DOTLOOP_*` values from `.env` in the current working
directory when those variables are not already exported. Set `DOTLOOP_ENV_FILE`
to point at a different local env file.

## Run

```bash
uv run python -m dotloop_mcp.cli stdio
uv run python -m dotloop_mcp.cli streamable-http --host 127.0.0.1 --port 8000 --path /mcp
```

## Authenticate the MCP URL

Streamable HTTP can be protected as an MCP OAuth resource server. The server
can validate tokens from an external OAuth/OIDC issuer and JWKS URL, then
clients must send `Authorization: Bearer <token>` on every MCP HTTP request.
Tokens in URL query strings are not supported.

```bash
export DOTLOOP_TRANSPORT=streamable-http
export DOTLOOP_MCP_AUTH_ENABLED=1
export DOTLOOP_MCP_AUTH_ISSUER_URL="https://auth.example.com"
export DOTLOOP_MCP_AUTH_RESOURCE_SERVER_URL="https://dotloop-mcp.example.com/mcp"
export DOTLOOP_MCP_AUTH_JWKS_URL="https://auth.example.com/.well-known/jwks.json"
export DOTLOOP_MCP_AUTH_REQUIRED_SCOPES="dotloop:read"
```

`DOTLOOP_MCP_AUTH_RESOURCE_SERVER_URL` is the public MCP endpoint URL clients
authenticate for. It is also used for protected-resource metadata discovery.
Set `DOTLOOP_MCP_AUTH_AUDIENCE` only when the issuer uses a separate JWT
audience value. Stdio transport is unchanged and should continue to load local
credentials from the environment.

Hosted staging can also expose built-in OAuth issuer endpoints for MCP clients
that expect URL-based browser authentication:

```bash
export DOTLOOP_MCP_HOSTED_OAUTH_ENABLED=1
export DOTLOOP_MCP_HOSTED_OAUTH_PUBLIC_CONSENT_ENABLED=1
```

That built-in issuer serves:

```text
/.well-known/oauth-authorization-server
/.well-known/openid-configuration
/.well-known/jwks.json
/oauth/register
/oauth/authorize
/oauth/token
```

`DOTLOOP_MCP_HOSTED_OAUTH_PUBLIC_CONSENT_ENABLED=1` is a staging bridge for MCP
URL compatibility while live Dotloop API credentials are not attached. Before a
real Dotloop access token is added to hosted staging or production, replace that
public consent bridge with a real login/consent boundary or disable it.

## Hosted Staging Deployment

Dotloop staging is designed to run as a Docker image with the
`dotloop-mcp-hosted` entrypoint on ECS/Fargate behind
an HTTPS load balancer, with the public MCP endpoint expected at:

```text
https://dotloop.theperry.group/mcp
```

The hosted entrypoint is streamable HTTP only and requires inbound MCP URL auth:

```bash
DOTLOOP_TRANSPORT=streamable-http
DOTLOOP_HOST=0.0.0.0
DOTLOOP_PORT=8000
DOTLOOP_STREAMABLE_HTTP_PATH=/mcp
DOTLOOP_MCP_AUTH_ENABLED=1
DOTLOOP_MCP_AUTH_ISSUER_URL=https://dotloop.theperry.group
DOTLOOP_MCP_AUTH_RESOURCE_SERVER_URL=https://dotloop.theperry.group/mcp
DOTLOOP_MCP_AUTH_JWKS_URL=https://dotloop.theperry.group/.well-known/jwks.json
DOTLOOP_MCP_HOSTED_OAUTH_ENABLED=1
DOTLOOP_MCP_HOSTED_OAUTH_PUBLIC_CONSENT_ENABLED=1
```

Deployment assets live under `deploy/ecs/`. The staging GitHub Actions workflow
is `.github/workflows/deploy-staging.yml`; it validates the repo, builds and
pushes a multi-architecture ECR image, renders the ECS task definition, updates
the configured ECS service, and waits for stability. DNS should point
`dotloop.theperry.group` at the public load balancer before enabling client use.

## Validate

```bash
make validate
```

Live checks are disabled by default and require explicit opt-in:

```bash
make live-readiness-check
make live-read-check
```
