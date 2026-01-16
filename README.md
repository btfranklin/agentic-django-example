# Agentic Django Example Project

This Django project exercises the `agentic-django` package from PyPI.
The library provides agent run/session primitives, tool calling, and web-friendly
UI hooks to build LLM-powered Django apps.
See the [agentic-django GitHub repo](https://github.com/btfranklin/agentic-django) and
the [agentic-django PyPI page](https://pypi.org/project/agentic-django/).

The dependency is wired in `pyproject.toml` as:

```toml
agentic-django[rq]>=0.1.0
```

## Quick start (Docker)

Prereqs: Docker Desktop (or compatible Docker CLI + Compose plugin).

1. Configure env vars:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Optionally set `OPENAI_DEFAULT_MODEL`.

2. Build and run:

```bash
docker compose up --build
```

Visit `http://localhost:8000/` and use the "Demo login" link.

## Quick start (local)

Prereqs: Python 3.14+, PDM, and (optionally) Redis if you want background runs.

1. Install dependencies:

```bash
pdm install --group dev
```

2. Configure env vars:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Optionally set `OPENAI_DEFAULT_MODEL`.

3. Run migrations:

```bash
pdm run python manage.py migrate
```

4. Start the dev server:

```bash
pdm run python manage.py runserver
```

Visit `http://localhost:8000/` and use the "Demo login" link.

Optional: enable background runs by setting
`TASKS_BACKEND=django_tasks.backends.rq.RQBackend` and starting an RQ worker:

```bash
pdm run python manage.py rqworker --job-class django_tasks.backends.rq.Job
```

## What this demo shows (and where)

- Agent registry and prompt loading: `apps/sample_app/agent_registry.py` builds the demo `Agent` and pulls instructions from `apps/sample_app/prompts/demo_agent.prompt.md` using `promptdown`.
- Tool calling: `apps/sample_app/tools.py` defines three `@function_tool` examples (find, price, book) to show tool usage.
- Agent runs and sessions: `apps/sample_app/views.py` wires per-user `AgentSession` and uses the `agentic_django` run/session models to track history.
- HTMX run flow: `apps/sample_app/templates/sample_app/home.html` posts to `agents:run-create`, polls `agents:run-fragment`, and refreshes the conversation via `agents:session-items`.
- Conversation rendering: `templates/agentic_django/partials/conversation.html` and `apps/sample_app/templatetags/sample_app_tags.py` format messages, tool calls, and reasoning summaries.
- Background execution (optional): `agentic_django_example/settings.py` configures `django_tasks` with an RQ backend; `docker-compose.yml` starts Redis + an RQ worker.
