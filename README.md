# apifox-endpoint-sync

> Let Codex update Apifox docs without handing it the keys to the whole API project.

`apifox-endpoint-sync` is a safety-first CLI for AI-assisted API documentation. It gives Codex, or any careful human workflow, one narrow lane: validate one `endpoint-update` JSON file, preview the plan, ask Apifox to validate the schema, then update exactly one existing endpoint by `endpointId`.

Suggested GitHub description:

```text
Safe single-endpoint Apifox doc sync for Codex and AI agents. No imports, no project-wide writes, no shared-resource changes.
```

## Why It Stands Out

- Built for agent workflows, but constrained like production tooling.
- Updates one endpoint at a time, so every change is reviewable.
- Supports dry-run by default in the recommended flow.
- Blocks common project-wide writes before the Apifox CLI is called.
- Uses only Python standard library code.

## Background

AI coding agents are useful for turning implementation notes, API examples, and review comments into structured API documentation. The risky part is not generating JSON. The risky part is letting automation write too broadly.

`apifox-endpoint-sync` creates a narrow path:

- Codex prepares one `endpoint-update` JSON file.
- This tool validates the JSON locally.
- The Apifox CLI validates the update schema.
- The tool updates exactly one endpoint ID.

No bulk import. No shared parameter changes. No environment, variable, security, or project setting updates.

## Install

Clone the repository and run it directly:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Or use the checkout script without installing:

```bash
chmod +x scripts/apifox-endpoint-sync
./scripts/apifox-endpoint-sync --help
```

You also need the official Apifox CLI installed and available as `apifox` in `PATH`.

## Configure

Copy the example env file:

```bash
cp examples/.env.example .env
```

Supported variables:

```dotenv
APIFOX_TOKEN=apifox_token_placeholder
APIFOX_PROJECT_ID=project_id_placeholder
APIFOX_PROJECT_NAME=Project Name Placeholder
APIFOX_BRANCH=main
```

Keep `.env` local. Do not commit real tokens, project IDs, endpoint IDs, private URLs, or private API examples.

## One-Line Usage

Dry-run first:

```bash
apifox-endpoint-sync --endpoint-id endpoint_id_placeholder --update-file examples/endpoint-update.example.json --expected-method GET --expected-path /api/admin/users --dry-run
```

Apply the update after review:

```bash
apifox-endpoint-sync --endpoint-id endpoint_id_placeholder --update-file examples/endpoint-update.example.json --expected-method GET --expected-path /api/admin/users
```

The update file is sent to `apifox endpoint update <id>` through standard input. Tokens are sent to `apifox login --with-token` through standard input.

## Codex Workflow

1. Ask Codex to read the relevant local implementation and produce one `endpoint-update` JSON file.
2. Require Codex to preserve only endpoint-local request, response, examples, and descriptions.
3. Run this tool with `--dry-run`.
4. Review the method, path, endpoint ID, and command plan.
5. Run without `--dry-run` only when the plan is correct.

Use [examples/codex-prompt.example.md](examples/codex-prompt.example.md) as a starting prompt.

## Safety Boundary

Before writing, the tool validates that:

- `method` exists and is a supported HTTP method.
- `path` exists and starts with `/`.
- Optional `--expected-method` and `--expected-path` match the JSON.
- Forbidden endpoint-level fields are absent: `commonParameters`, `auth`, `security`, `preProcessors`, `postProcessors`, `commonResponseStatus`.
- Common public parameters are not written into the endpoint: `Authorization`, `uid`, `did`, `lang`, `ctry`, `app`, `vsn`, `ch`, `pf`, `br`, `os`, `mod`, `us`, `seq`, `adid`, `gaid`, `idfa`, `nw`, `ts`.

The tool only allows these Apifox CLI commands:

```text
apifox login --with-token
apifox project list
apifox endpoint get
apifox cli-schema validate endpoint-update
apifox endpoint update <id>
```

## Resources This Tool Will Not Modify

This tool refuses to call commands that update or import:

- Projects through bulk import
- Common parameters
- Environments
- Variables
- Project settings
- Security or auth schemes
- Pre-processors
- Post-processors

It is a single endpoint documentation sync helper, not a project migration tool.

## Local Checks

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m json.tool examples/endpoint-update.example.json >/dev/null
./scripts/apifox-endpoint-sync --endpoint-id endpoint_id_placeholder --update-file examples/endpoint-update.example.json --expected-method GET --expected-path /api/admin/users --dry-run
```

## License

MIT
