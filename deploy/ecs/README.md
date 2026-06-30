# ECS Hosted Deployment

This directory contains the ECS/Fargate hosting assets for the Dotloop MCP
server.

## Files

- `task-definition.template.json`: ECS task definition template for the hosted
  streamable HTTP server.
- `task-role-policy.template.json`: least-privilege task-role policy template
  for runtime secret access.

## Public Endpoint

The staging hostname should be:

```text
https://dotloop.theperry.group/mcp
```

Route DNS for `dotloop.theperry.group` to the public HTTPS load balancer. The
container listens on port `8000` over HTTP behind that trusted proxy or load
balancer.

## Placeholder Values

Before registering the task definition, replace:

| Placeholder | Meaning |
| --- | --- |
| `__AWS_REGION__` | AWS region, such as `us-west-1`. |
| `__DOTLOOP_API_CLIENT_ID_SECRET_ARN__` | Secrets Manager ARN whose secret string is the Dotloop app client id. |
| `__DOTLOOP_API_SECRET_SECRET_ARN__` | Secrets Manager ARN whose secret string is the Dotloop app client secret. |
| `__DOTLOOP_APP_OAUTH_REDIRECT_URL__` | Dotloop OAuth callback URL registered with the Dotloop developer app, normally `https://tpgstats.com/agents/dotloop/callback` for the Perry Group hosted deployment. |
| `__DOTLOOP_APP_OAUTH_TOKEN_SECRET_ARN__` | Secrets Manager ARN for the refreshable Dotloop token-state JSON store. |
| `__DOTLOOP_BATTLE_FIXTURE_MODE__` | Optional fixture-mode switch for AI battle tests; defaults to `0`. |
| `__DOTLOOP_BATTLE_RECORD_PATH__` | Optional JSONL call-log path for fixture-mode battle tests. |
| `__IMAGE_URI__` | Full ECR image URI, including tag or digest. |
| `__LOG_GROUP_NAME__` | CloudWatch Logs group name for the ECS service. |
| `__MCP_AUTH_AUDIENCE__` | Optional issuer-specific JWT audience; leave empty when the public MCP URL is the audience. |
| `__MCP_AUTH_ISSUER_URL__` | OAuth/OIDC issuer URL advertised through MCP protected-resource metadata. |
| `__MCP_AUTH_JWKS_URL__` | JWKS URL used to validate inbound MCP Bearer JWTs. |
| `__MCP_AUTH_REQUIRED_SCOPES__` | Comma-separated scopes; default `dotloop:read`. |
| `__MCP_AUTH_RESOURCE_SERVER_URL__` | External HTTPS MCP URL, such as `https://dotloop.theperry.group/mcp`. |
| `__TASK_EXECUTION_ROLE_ARN__` | ECS task execution role ARN. |
| `__TASK_ROLE_ARN__` | ECS task role ARN used by the app at runtime. |

The staging task template enables the built-in hosted OAuth issuer and uses
Dotloop app OAuth as the consent boundary for live Dotloop API access:

```text
DOTLOOP_APP_OAUTH_ENABLED=1
DOTLOOP_APP_OAUTH_REDIRECT_URL=https://tpgstats.com/agents/dotloop/callback
DOTLOOP_MCP_HOSTED_OAUTH_ENABLED=1
DOTLOOP_MCP_HOSTED_OAUTH_PUBLIC_CONSENT_ENABLED=0
DOTLOOP_MCP_AUTH_JWKS_URL=https://dotloop.theperry.group/.well-known/jwks.json
```

The Dotloop app must allow `https://tpgstats.com/agents/dotloop/callback` as a
redirect URI. The Perry Group Django app relays MCP-prefixed callback states
to `https://dotloop.theperry.group/oauth/dotloop/callback`; normal Django
Dotloop authorization states continue through the website flow. The refreshable
token-state secret starts empty and is populated after a browser completes the
first connector authorization.

## Hosted Battle Testing

For ChatGPT connector battle tests, deploy staging with deterministic fixture
mode before attaching live Dotloop credentials:

```text
DOTLOOP_BATTLE_FIXTURE_MODE=1
DOTLOOP_BATTLE_RECORD_PATH=/tmp/ai-battle/chatgpt/mcp_calls.jsonl
```

Fixture mode is incompatible with `DOTLOOP_RUN_LIVE_TESTS=1`, does not build a
real Dotloop API client, and should be scored with `scripts/battle_report.py`
after retrieving the JSONL call log from the container or log export path.

## GitHub Actions Staging Deploy

`.github/workflows/deploy-staging.yml` validates the repo, builds a multi-arch
Docker image, pushes it to ECR, renders the task definition, creates or updates
the ECS service, and waits for service stability.

Configure a GitHub Actions environment named `staging` with these variables:

- `AWS_REGION`
- `ECR_REPOSITORY`
- `ECS_CLUSTER`
- `ECS_SERVICE`
- `ECS_SECURITY_GROUP_IDS` (comma-separated security group IDs)
- `ECS_SUBNET_IDS` (comma-separated subnet IDs)
- `ECS_TARGET_GROUP_ARN`
- `LOG_GROUP_NAME`
- `DOTLOOP_APP_OAUTH_REDIRECT_URL` (optional; defaults to `https://tpgstats.com/agents/dotloop/callback`)
- `DOTLOOP_BATTLE_FIXTURE_MODE` (optional; defaults to `0`)
- `DOTLOOP_BATTLE_RECORD_PATH` (optional; defaults to `/tmp/ai-battle/staging/mcp_calls.jsonl`)
- `MCP_AUTH_ISSUER_URL`
- `MCP_AUTH_RESOURCE_SERVER_URL`
- `MCP_AUTH_JWKS_URL`
- `MCP_AUTH_REQUIRED_SCOPES` (optional; defaults to `dotloop:read`)
- `MCP_AUTH_AUDIENCE` (optional)

Configure the same environment with these secrets:

- `AWS_ROLE_TO_ASSUME`
- `DOTLOOP_API_CLIENT_ID_SECRET_ARN`
- `DOTLOOP_API_SECRET_SECRET_ARN`
- `DOTLOOP_APP_OAUTH_TOKEN_SECRET_ARN`
- `TASK_EXECUTION_ROLE_ARN`
- `TASK_ROLE_ARN`

When any required staging value is absent, the workflow still runs release
validation but skips the AWS deploy job. Once every required variable and secret
is configured, the same workflow activates the hosted deployment path.

The target group health matcher should accept `401` for `/mcp`, because a
hosted unauthenticated MCP request is expected to fail closed with
`invalid_token`.

The same public host should serve authorization-server discovery:

```text
https://dotloop.theperry.group/.well-known/oauth-authorization-server
https://dotloop.theperry.group/.well-known/openid-configuration
https://dotloop.theperry.group/.well-known/jwks.json
```
