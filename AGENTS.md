# Agent Map

This repository is a Django example app for the published `agentic-django`
package. Keep this file short; durable repo knowledge belongs in `docs/`.

## Start Here

- [README](README.md): quick start and demo overview.
- [Documentation index](docs/index.md): documentation map and maintenance rules.
- [Architecture](docs/ARCHITECTURE.md): boundaries, request flow, package
  integration, and dependency direction.
- [Operations](docs/OPERATIONS.md): setup, environment variables, runtime modes,
  and troubleshooting.
- [Quality](docs/QUALITY.md): validation commands, behavioral contracts,
  dependency policy, and documentation policy.
- [Legibility audit](docs/LEGIBILITY_AUDIT.md): current legibility strengths,
  fixed gaps, and next investments.

## Working Rules

- Use PDM for Python dependency and command management.
- Keep `agentic-django` consumed from PyPI; do not use a local path dependency.
- Store AI prompts in `apps/sample_app/prompts/*.prompt.md` with `promptdown`.
- Keep new example-app logic inside the owning Django app under `apps/`.
- Update docs with code when behavior, commands, boundaries, or runtime
  expectations change.

## Validation

```bash
pdm run lint
pdm run test
pdm run check
npm test
npm run build:css
```

Run the narrowest useful check while developing, then run the full relevant
validation loop before handoff.
