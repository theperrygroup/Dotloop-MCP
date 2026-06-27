---
name: dotloop-mcp-implementation-planning
description: Create and maintain phased planning docs for the Dotloop MCP workspace. Use when planning Dotloop MCP server work, MCP tools and resources, OAuth/token handling, Dotloop API integration, schema modeling, local verification, roadmap updates, tracker refreshes, or planning consolidation under docs/planning.
---

# Dotloop MCP Implementation Planning

## Purpose

Use this skill when the user wants a doc-first implementation plan for this
Dotloop MCP workspace, or when existing planning docs need to be extended,
refreshed, or consolidated after work lands.

This skill supports four modes:

- `scaffold`: create a new planning tree for a Dotloop MCP initiative.
- `extend`: add a new active plan, phase, ADR, tracker, or proof artifact to an
  existing tree.
- `refresh`: update status docs after checked-in implementation changes the
  current truth.
- `consolidate`: reconcile shared planning docs after related slices land.

Respect the current interaction mode:

- In Plan mode, research first and return the proposed tree or update plan.
- In Agent mode, create or update the docs directly.

## Read First

Start by inspecting the workspace, because this repo may be empty or only
partially scaffolded:

- List the current files and directories.
- Read any existing `README.md`, `docs/planning/**`, `.codex/**`,
  package/config files, MCP server entrypoints, or Dotloop API notes.
- If the workspace is not yet a Git repo, treat that as normal bootstrap state.
- If no repo docs exist, proceed from observed files and the user's request
  rather than assuming a prior project structure.

If a matching planning root already exists, read that root's key docs before
editing:

- `README.md`
- `ARTIFACT_PATH_INDEX.md`
- `execution/README.md`
- `execution/execution-plan.md`
- `execution/roadmap.md`
- the most relevant active plan, tracker, ADR, or proof file

If no matching planning root exists, create only the minimum planning structure
needed for the requested Dotloop MCP workstream. Do not create broad governance,
tracking, or evidence layers until the workstream needs them.

## Mode Selection

Choose the smallest honest mode that matches the request:

- Use `scaffold` when the user wants planning docs for a new Dotloop MCP idea,
  or when no existing planning root can honestly own the work.
- Use `extend` when an existing tree is the right home and the user needs a new
  phase, active execution artifact, ADR, or focused tracker.
- Use `refresh` when implementation has already changed and planning docs need
  current status, readiness, proof, or ledger language brought back in sync.
- Use `consolidate` when multiple related slices landed and shared planning
  docs need one coherent narrative.

If a request includes both a new active phase and a status sync, run `extend`
first and then `refresh` in the same pass.

Ask one concise clarifying question only when the choice would materially
change which planning root or files you create. Otherwise choose the smallest
mode that keeps the docs accurate.

## Dotloop MCP Planning Context

Treat Dotloop MCP as the default domain. Plans should account for the relevant
parts of the MCP and Dotloop integration surface:

- MCP server scaffolding, transport, startup configuration, and client
  compatibility.
- Dotloop OAuth, credential storage, refresh behavior, token scope, and safe
  local configuration.
- Dotloop API resource modeling, pagination, filtering, rate limits, error
  handling, and API shape uncertainty.
- MCP tool and resource schemas, input validation, output shape, and user-safe
  mutation boundaries.
- Verification through unit tests, local MCP client checks, mocked Dotloop API
  responses, and any live API smoke tests the user explicitly authorizes.
- Documentation that distinguishes proposed plans from implemented code and
  verified runtime behavior.

Do not invent Dotloop implementation status. If a server, OAuth flow, API
client, schema, or test does not exist in the workspace, describe it as planned
or missing until checked-in files prove otherwise.

## Scaffold Size

Every initiative should live under one root:

`docs/planning/<initiative-slug>/`

Use a thin scaffold when all of these are true:

- the work is one bounded MCP feature or integration seam
- one owner or implementation path is clear
- the user mainly needs sequencing
- trackers, ADRs, or proof files would be speculative overhead

A thin scaffold usually includes:

- `README.md`
- `ARTIFACT_PATH_INDEX.md`
- `execution/README.md`
- `execution/execution-plan.md`
- `execution/roadmap.md`
- one active plan doc under `execution/`

Use a full scaffold when any of these are true:

- the initiative spans multiple MCP tools, Dotloop API resources, auth flows, or
  runtime boundaries
- more than one readiness lens needs ongoing tracking
- work will land across multiple phases or parallel slices
- future agents will need durable status refreshes
- the user explicitly asks for a multi-phase planning tree

A full scaffold may add:

- `foundation/README.md`
- targeted ADRs or source-of-truth notes
- `trackers/README.md`
- `trackers/readiness-overview.md`
- focused trackers for auth, API coverage, MCP client compatibility, live
  verification, or rollout risk

When in doubt in a new Dotloop MCP workspace, start thin and promote to full
only when the request shows durable complexity.

## Core Rules

- Keep one planning root per workstream.
- Extend a matching root instead of creating a near-duplicate slug.
- Keep planning trees docs-only. Runtime MCP code, tests, generated files, and
  product artifacts belong outside `docs/planning/`.
- Treat `README.md` as the operating guide and
  `ARTIFACT_PATH_INDEX.md` as the naming and path index.
- Treat `execution/execution-plan.md` as the live checked-in ledger.
- Treat `execution/roadmap.md` as baseline sequencing and dependency order, not
  the freshest status snapshot.
- Use one dedicated active plan doc when a single remediation, bootstrap, or
  build sequence should outrank the historical roadmap.
- Add phase proof files only when a slice needs durable evidence beyond a short
  ledger note.
- Keep status language honest: planned is not implemented, implemented is not
  verified, and local proof is not live Dotloop proof.
- Keep mutation boundaries explicit for any MCP tool that can create, update,
  send, archive, delete, or otherwise alter Dotloop data.
- If code changes alongside docs, run the relevant tests and validation commands
  after substantive edits.

## Required Workflow

### Scaffold Mode

1. Derive the canonical initiative slug and confirm no existing planning root
   already owns the work.
2. Choose thin versus full scaffold using the rules above.
3. Create landing docs first, then execution docs, then foundation or tracker
   docs only if needed.
4. If the user asked for a multi-phase plan, create one active execution
   artifact under `execution/` and make the landing README point to it.
5. Seed the landing docs with document precedence, common workflows, update
   order, MCP/Dotloop-specific verification expectations, and working rules.

### Extend Mode

1. Read the existing active plan, execution ledger, and relevant tracker before
   adding anything new.
2. Prefer updating the current canonical active plan doc instead of spawning a
   sibling plan for the same seam.
3. Add a phase proof file only when the new slice needs durable,
   slice-specific evidence beyond the execution ledger.
4. Promote a thin tree to full only when the new scope adds durable auth,
   API-resource, MCP-client, readiness, or rollout complexity.

### Refresh Mode

1. Inspect checked-in code and docs before changing status language.
2. Update docs in this order: phase proof, focused tracker, readiness overview,
   execution ledger, foundation docs if durable rules changed, then landing docs
   only if navigation or canonical-path assumptions changed.
3. Keep the roadmap untouched unless baseline dependency order changed.
4. Mark live Dotloop API behavior as verified only when a live check actually
   ran and the user authorized any state-changing operation.

### Consolidate Mode

1. Use this mode when multiple slices landed and shared planning docs need a
   single coherent story.
2. Reconcile shared docs from landed work only.
3. Do not upgrade proposals, TODOs, or unverified assumptions into completed
   facts.
4. If one active execution artifact supersedes an older sequence, update the
   landing README and `execution/README.md` so readers know which document wins.

## Output Requirements

Return different outputs by mode.

For `scaffold`, report:

- chosen initiative root
- chosen scaffold size and why
- files created or updated
- canonical active plan doc, if created
- intentionally deferred docs

For `extend`, report:

- what was extended
- files changed
- any new active plan, ADR, tracker, or phase proof file
- any deferred tracker or ledger follow-up

For `refresh`, report:

- what checked-in truth was synchronized
- files changed
- whether the roadmap changed and why
- remaining blockers or follow-up docs still needed

For `consolidate`, report:

- what was reconciled
- which shared docs changed and why
- stale claims corrected
- ambiguities or unlanded proposals intentionally left out

If code changed alongside docs, also report tests run and lints checked.

## Do Not

- Do not create root-level planning docs outside one initiative folder.
- Do not duplicate an existing initiative under a near-synonym slug.
- Do not use `ARTIFACT_PATH_INDEX.md` as a current-status ledger.
- Do not treat `execution/roadmap.md` as the live status document.
- Do not mark proposals, TODOs, or unlanded implementation ideas as completed.
- Do not create `progress/`, `evidence/`, or `adjacent/` by default.
- Do not build the Dotloop MCP server when the user only asked for planning
  docs.
- Do not run live Dotloop mutations unless the user explicitly authorized that
  state-changing action.

## Suggested User Invocation

Use this skill for requests like:

- "Use Dotloop MCP planning to scaffold the OAuth implementation plan."
- "Create a planning tree for the Dotloop loop search tool."
- "Add a new phase for MCP client compatibility testing."
- "Refresh the Dotloop API coverage tracker after this landed."
- "Consolidate the planning docs after the auth and loop-read slices merged."
