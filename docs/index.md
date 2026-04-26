# Documentation Index

This directory is the system of record for repo knowledge that is too detailed
for `AGENTS.md` or the quick-start `README.md`.

## Start Here

- [Architecture](ARCHITECTURE.md): project boundaries, request flow, dependency
  rules, and package integration points.
- [Operations](OPERATIONS.md): local setup, Docker setup, environment variables,
  runtime modes, and troubleshooting entry points.
- [Quality](QUALITY.md): validation commands, behavioral contracts, dependency
  policy, and review expectations.
- [Legibility audit](LEGIBILITY_AUDIT.md): current strengths, fixed gaps, and
  next investments for future agent autonomy.

## Maintenance Rules

- Keep `AGENTS.md` short and route durable knowledge here.
- Update the relevant doc in the same change as code or workflow changes.
- Add new docs only when they clarify repeated work or non-obvious decisions.
- Move completed plans into current-truth docs; do not keep stale completion logs.
