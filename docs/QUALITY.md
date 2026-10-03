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
npm test
npm run build:css
```

For Python-only changes, `pdm run check` runs lint and tests together.

## Behavioral Contracts

- The home page requires login and creates a user-owned `AgentSession`.
- Demo login is available only when `DJANGO_DEBUG=true`. It uses an account
  with no usable password, and ordinary password login rejects the `demo`
  username.
- Demo login requires POST with a CSRF token. Its control is visible only in
  debug mode.
- Resetting a session clears backend and local history and creates a fresh
  session key. It returns HTTP 409 while a run is pending or running and keeps
  the old key and history.
- HTMX run creation returns a fragment; non-HTMX run creation returns JSON.
- The request form clears submitted text only after a successful response and
  only when the user has not changed the text since submission.
- Request errors stay next to the form. They keep the draft and the existing run
  status. Empty requests use browser form validation.
- The request field has a visible label. The run status region announces changes
  without interrupting other screen reader output.
- An expired HTMX login keeps the unsent request and shows a login link. Run
  polling stops, and login returns to the home page.
- Running fragments keep polling; terminal HTMX fragments stop polling with
  HTTP 286.
- Failed runs show their error text. Templates escape that text before display.
- Conversation rendering handles user, assistant, tool call, tool output, and
  reasoning events deterministically.
- Flight search requires `travel_date` in `YYYY-MM-DD` format and reports
  invalid dates as tool errors.
- Prompt instructions live in `*.prompt.md` files and are loaded through
  `promptdown`.
- Mock flight search, price, and booking results use the Economy fare class.
  Quotes and bookings use the same amount. Mock tools must not call real
  booking or pricing services.

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
- Keep application behavior tests adjacent under `apps/<app>/tests/`. Keep
  documentation governance and project configuration tests in separate modules
  under top-level `tests/`; they should validate navigability and structured
  configuration without duplicating application behavior assertions.
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
- Documentation governance tests should fail with remediation text when the
  docs map drifts.
