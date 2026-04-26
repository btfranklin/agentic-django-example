# Operations

Use PDM for Python dependency and command management. The app can run locally
with SQLite or through Docker Compose with Redis and an RQ worker.

## Local Setup

```bash
pdm install --group dev
cp .env.example .env
pdm run python manage.py migrate
pdm run python manage.py runserver
```

Set `OPENAI_API_KEY` in `.env` before running live agent requests. Visit
`http://localhost:8000/` and use the demo login in local debug mode.

## Docker Setup

```bash
cp .env.example .env
docker compose up --build
```

Compose starts Redis, the Django web process, and an RQ worker. The web process
runs migrations before starting the server. The worker waits until the migration
sentinel exists in the shared SQLite volume.

## Environment Variables

- `DJANGO_SECRET_KEY`: Django secret key. The default is development-only.
- `DJANGO_DEBUG`: `true` enables the demo login route.
- `DJANGO_ALLOWED_HOSTS`: comma-separated host allowlist.
- `DATABASE_URL`: optional PostgreSQL URL. Leave unset for SQLite.
- `SQLITE_PATH`: optional SQLite database path.
- `TASKS_BACKEND`: defaults to immediate tasks locally; set
  `django_tasks.backends.rq.RQBackend` for RQ.
- `REDIS_URL`: Redis connection string for RQ mode.
- `OPENAI_API_KEY`: required for real OpenAI-backed agent runs.
- `OPENAI_DEFAULT_MODEL`: optional model override used by the Agents SDK.

## Validation Commands

```bash
pdm run lint
pdm run test
pdm run check
npm run build:css
```

`pdm run check` is the default full local validation loop for Python changes.
`npm run build:css` is currently a placeholder, but keeping the script present
makes future frontend tooling predictable.

## Runtime Troubleshooting

- If the app starts but package views fail, run migrations again and check that
  `agentic_django.apps.AgenticDjangoConfig` is installed.
- If HTMX polling does not run, verify that `django_htmx` is installed, the
  middleware is enabled, and `{% htmx_script %}` is rendered by
  `apps/sample_app/templates/sample_app/base.html`.
- If background runs do not progress in Docker, check the `rqworker` container
  logs and confirm `TASKS_BACKEND=django_tasks.backends.rq.RQBackend`.
- If CSP blocks a script, prefer self-hosted static assets and update
  `SECURE_CSP` in settings intentionally.
