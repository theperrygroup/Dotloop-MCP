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
| `__DOTLOOP_ACCESS_TOKEN_SECRET_ARN__` | Optional Secrets Manager ARN whose secret string is the Dotloop access token. Omit for metadata/auth-only staging. |
| `__IMAGE_URI__` | Full ECR image URI, including tag or digest. |
| `__LOG_GROUP_NAME__` | CloudWatch Logs group name for the ECS service. |
| `__MCP_AUTH_AUDIENCE__` | Optional issuer-specific JWT audience; leave empty when the public MCP URL is the audience. |
| `__MCP_AUTH_ISSUER_URL__` | OAuth/OIDC issuer URL advertised through MCP protected-resource metadata. |
| `__MCP_AUTH_JWKS_URL__` | JWKS URL used to validate inbound MCP Bearer JWTs. |
| `__MCP_AUTH_REQUIRED_SCOPES__` | Comma-separated scopes; default `dotloop:read`. |
| `__MCP_AUTH_RESOURCE_SERVER_URL__` | External HTTPS MCP URL, such as `https://dotloop.theperry.group/mcp`. |
| `__TASK_EXECUTION_ROLE_ARN__` | ECS task execution role ARN. |
| `__TASK_ROLE_ARN__` | ECS task role ARN used by the app at runtime. |

The staging task template enables the built-in hosted OAuth issuer with public
consent so MCP clients can complete URL authentication without a separate
identity provider:

```text
DOTLOOP_MCP_HOSTED_OAUTH_ENABLED=1
DOTLOOP_MCP_HOSTED_OAUTH_PUBLIC_CONSENT_ENABLED=1
DOTLOOP_MCP_AUTH_JWKS_URL=https://dotloop.theperry.group/.well-known/jwks.json
```

Public consent is only acceptable for metadata/auth-only staging while no live
Dotloop access token is attached. Disable it or replace it with a real
login/consent boundary before enabling live Dotloop data access in hosted
runtime.

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
- `MCP_AUTH_ISSUER_URL`
- `MCP_AUTH_RESOURCE_SERVER_URL`
- `MCP_AUTH_JWKS_URL`
- `MCP_AUTH_REQUIRED_SCOPES` (optional; defaults to `dotloop:read`)
- `MCP_AUTH_AUDIENCE` (optional)

Configure the same environment with these secrets:

- `AWS_ROLE_TO_ASSUME`
- `DOTLOOP_ACCESS_TOKEN_SECRET_ARN` (optional until live Dotloop reads are enabled)
- `TASK_EXECUTION_ROLE_ARN`
- `TASK_ROLE_ARN`

When any required staging value is absent, the workflow still runs release
validation but skips the AWS deploy job. Once every required variable and secret
is configured, the same workflow activates the hosted deployment path. If
`DOTLOOP_ACCESS_TOKEN_SECRET_ARN` is absent, the hosted server still boots and
authenticates MCP callers, but Dotloop data tools return a clear missing-token
error until that secret is added.

The target group health matcher should accept `401` for `/mcp`, because a
hosted unauthenticated MCP request is expected to fail closed with
`invalid_token`.

The same public host should serve authorization-server discovery:

```text
https://dotloop.theperry.group/.well-known/oauth-authorization-server
https://dotloop.theperry.group/.well-known/openid-configuration
https://dotloop.theperry.group/.well-known/jwks.json
```
