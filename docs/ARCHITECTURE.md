# Architecture

`agentic-django-example` is a small Django project that demonstrates the
published `agentic-django` package. The example app should stay thin: it wires
the package into a runnable Django service and shows a realistic HTMX flow
without becoming a fork of the reusable library.

## Main Boundaries

- `agentic_django_example/` owns project settings, root URLs, ASGI/WSGI entry
  points, database configuration, CSP, static/media roots, and task backend
  selection.
- `apps/sample_app/` owns the demo user flow, session bootstrap, agent registry,
  prompt loading, mock tools, app templates, and rendering helpers used only by
  this example.
- `templates/agentic_django/partials/` contains deliberate template overrides
  for package-rendered fragments. Treat files here as integration surfaces with
  `agentic-django`, not generic sample app templates.
- `static/sample_app/` contains small self-hosted browser helpers. Keep external
  runtime scripts out of the demo unless the CSP is updated intentionally.
- The reusable `agentic-django` package is consumed from PyPI. Do not replace it
  with a local path dependency in this repository.

## Request And Run Flow

1. `sample_app:home` requires an authenticated user.
2. `apps/sample_app/views.py` stores a per-browser `agent_session_key` in the
   Django session and creates an `AgentSession` owned by the current user.
3. `apps/sample_app/templates/sample_app/home.html` posts user input to the
   package route `agents:run-create` using HTMX.
4. `agentic-django` creates an `AgentRun`, enqueues or executes the run, and
   returns package fragments for polling.
5. The run fragment polls `agents:run-fragment` until the package marks the run
   terminal. Completed HTMX polls use HTTP 286 to stop polling.
6. The conversation panel refreshes from `agents:session-items` after
   `run-update` events and renders through the local package partial override.

## Agent Registry And Prompts

`agentic_django_example.settings.AGENTIC_DJANGO_AGENT_REGISTRY` points to
`sample_app.agent_registry.get_agent_registry`. The registry returns callables
that build `agents.Agent` instances on demand.

Prompt text belongs in `apps/sample_app/prompts/*.prompt.md` and is loaded with
`promptdown`. Keep new prompt files external to Python code so prompt behavior
can be reviewed, tested, and changed without hiding instructions inside object
construction.

## Dependency Direction

- Project settings may configure installed apps and package settings.
- `sample_app` may import public package APIs from `agentic_django` and
  `agents`.
- `sample_app` should not reach into another example app if more apps are added.
- Package template overrides should stay under `templates/agentic_django/`.
- Tests may exercise package URLs because this repository's purpose is to prove
  the package integration works in a real Django project.

## Runtime Modes

The default local mode uses SQLite and Django's immediate task backend. Docker
Compose uses SQLite in a named volume, Redis, and an RQ worker so the demo can
exercise background execution. PostgreSQL is supported through `DATABASE_URL`
but is not required for the default example workflow.
