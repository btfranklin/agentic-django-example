# Quality

This repository's quality bar is integration correctness: the example should
prove that `agentic-django` works in a real Django project with authentication,
sessions, HTMX fragments, prompt loading, tool calls, and optional background
execution.

## Required Checks

Run these before handing off meaningful changes:

```bash
pdm run lint
pdm run test
npm run build:css
```

For Python-only changes, `pdm run check` runs lint and tests together.

## Behavioral Contracts

- The home page requires login and creates a user-owned `AgentSession`.
- Demo login is available only when `DJANGO_DEBUG=true`.
- Resetting a session clears package-backed history and creates a fresh session
  key.
- HTMX run creation returns a fragment; non-HTMX run creation returns JSON.
- Running fragments keep polling; terminal HTMX fragments stop polling with
  HTTP 286.
- Conversation rendering handles user, assistant, tool call, tool output, and
  reasoning events deterministically.
- Prompt instructions live in `*.prompt.md` files and are loaded through
  `promptdown`.
- Mock tools are deterministic enough for tests and demos; they must not call
  real booking or pricing services.

## Dependency Policy

- Manage Python packages with PDM.
- Target Python 3.14+ for local development, CI, and container builds.
- Keep Django services on Django 6.x unless a future change explicitly scopes a
  different track. If Django becomes a direct dependency here, use
  `django>=6,<7`.
- Use `>=` dependency bounds unless a tighter bound is required for
  functionality.
- When adding a dependency, use the latest available version at the time of the
  change.
- Keep `agentic-django` as a PyPI dependency in `pyproject.toml`; this example
  repository must not depend on a local checkout of the package.
- Store AI prompts externally with `promptdown`.

## Coding Conventions

- Use 4-space indentation and type-annotate every function.
- Prefer built-in generics such as `list[str]` and `dict[str, Any]`, and use
  `| None` for optional values.
- Keep Django apps modular. New views, forms, services, tasks, templates, and
  tests should live under the app that owns the workflow.
- Keep app tests adjacent under `apps/<app>/tests/`. Repo-structure tests may
  live under top-level `tests/`.
- Follow `<app>/templates/<app>/**` for app templates, and keep package
  overrides under the package template namespace they override.
- Prefer Django 6's built-in tasks framework for background work. Add Celery
  only if the demo needs guarantees that Django tasks plus RQ cannot provide.
- Prefer Django 6 template partials before splitting markup into many tiny
  includes.
- Keep CSP intentional. Prefer self-hosted static assets and update
  `SECURE_CSP` only when a feature actually requires it.
- Write docstrings and comments in American English, focused on intent rather
  than restating code.

## Documentation Policy

- `AGENTS.md` is a routing map, not the full source of truth.
- `docs/` owns architecture, operations, quality, and legibility notes.
- Update docs in the same change as code when behavior, commands, boundaries,
  or runtime expectations change.
- The repo legibility tests should fail with remediation text when the docs map
  drifts.
