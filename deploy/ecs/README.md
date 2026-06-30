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
| `__DOTLOOP_ACCESS_TOKEN_SECRET_ARN__` | Secrets Manager ARN whose secret string is the Dotloop access token. |
| `__IMAGE_URI__` | Full ECR image URI, including tag or digest. |
| `__LOG_GROUP_NAME__` | CloudWatch Logs group name for the ECS service. |
| `__MCP_AUTH_AUDIENCE__` | Optional issuer-specific JWT audience; leave empty when the public MCP URL is the audience. |
| `__MCP_AUTH_ISSUER_URL__` | OAuth/OIDC issuer URL advertised through MCP protected-resource metadata. |
| `__MCP_AUTH_JWKS_URL__` | JWKS URL used to validate inbound MCP Bearer JWTs. |
| `__MCP_AUTH_REQUIRED_SCOPES__` | Comma-separated scopes; default `dotloop:read`. |
| `__MCP_AUTH_RESOURCE_SERVER_URL__` | External HTTPS MCP URL, such as `https://dotloop.theperry.group/mcp`. |
| `__TASK_EXECUTION_ROLE_ARN__` | ECS task execution role ARN. |
| `__TASK_ROLE_ARN__` | ECS task role ARN used by the app at runtime. |

## GitHub Actions Staging Deploy

`.github/workflows/deploy-staging.yml` validates the repo, builds a multi-arch
Docker image, pushes it to ECR, renders the task definition, updates the ECS
service, and waits for service stability.

Configure a GitHub Actions environment named `staging` with these variables:

- `AWS_REGION`
- `ECR_REPOSITORY`
- `ECS_CLUSTER`
- `ECS_SERVICE`
- `LOG_GROUP_NAME`
- `MCP_AUTH_ISSUER_URL`
- `MCP_AUTH_RESOURCE_SERVER_URL`
- `MCP_AUTH_JWKS_URL`
- `MCP_AUTH_REQUIRED_SCOPES` (optional; defaults to `dotloop:read`)
- `MCP_AUTH_AUDIENCE` (optional)

Configure the same environment with these secrets:

- `AWS_ROLE_TO_ASSUME`
- `DOTLOOP_ACCESS_TOKEN_SECRET_ARN`
- `TASK_EXECUTION_ROLE_ARN`
- `TASK_ROLE_ARN`

The target group health matcher should accept `401` for `/mcp`, because a
hosted unauthenticated MCP request is expected to fail closed with
`invalid_token`.
