# Codex Rules for Apifox Endpoint Docs

This repository is for safe, single-endpoint Apifox documentation updates.

## Hard Boundaries

- Generate documentation for one endpoint at a time.
- Never use bulk import.
- Never update common parameters, environments, variables, project settings, security schemes, auth schemes, pre-processors, or post-processors.
- Never commit real tokens, project IDs, endpoint IDs, private URLs, private examples, or proprietary field names.
- Use placeholders for all IDs and credentials in examples.

## Allowed Apifox CLI Commands

Codex may only use:

```text
apifox login --with-token
apifox project list
apifox endpoint get
apifox cli-schema validate endpoint-update
apifox endpoint update <id>
```

## Endpoint JSON Rules

Every generated `endpoint-update` JSON file must:

- Include `method`.
- Include `path`.
- Match the expected method and path when those are supplied by the user.
- Describe endpoint-local request parameters, request body, responses, and examples only.
- Avoid adding shared public parameters to a single endpoint.

Forbidden fields anywhere in the JSON:

```text
commonParameters
auth
security
preProcessors
postProcessors
commonResponseStatus
```

Forbidden common public parameter names:

```text
Authorization
uid
did
lang
ctry
app
vsn
ch
pf
br
os
mod
us
seq
adid
gaid
idfa
nw
ts
```

## Recommended Workflow

1. Read the endpoint implementation or user-provided notes.
2. Generate one endpoint-update JSON file.
3. Run local JSON validation.
4. Run `apifox-endpoint-sync --dry-run`.
5. Confirm endpoint ID, method, path, and update scope.
6. Apply the update only after the dry-run plan is reviewed.

Prefer small, reviewable documentation edits over broad rewrites.
