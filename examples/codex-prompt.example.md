# Codex Prompt Example

You are updating one Apifox endpoint document only.

Target endpoint:

- endpointId: `endpoint_id_placeholder`
- method: `GET`
- path: `/api/admin/users`

Task:

1. Read the local endpoint implementation and related tests.
2. Produce a single `endpoint-update` JSON file.
3. Include only endpoint-local request parameters, request body, response schema, examples, and descriptions.
4. Do not add common public headers or shared parameters.
5. Do not modify environments, variables, project settings, common parameters, security schemes, auth schemes, pre-processors, or post-processors.
6. Run:

```bash
apifox-endpoint-sync --endpoint-id endpoint_id_placeholder --update-file endpoint-update.json --expected-method GET --expected-path /api/admin/users --dry-run
```

Stop after dry-run and show the update plan for review.
