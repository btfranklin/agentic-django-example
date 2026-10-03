# Operations

Use PDM for Python dependency and command management. The app can run locally
with SQLite or through Docker Compose with Redis and an RQ worker.

Settings load the project root `.env` file for management commands, WSGI, and
ASGI. Existing process variables take precedence over values in the file.

## Local Setup

```bash
pdm install --group dev
cp .env.example .env
pdm run python manage.py migrate
pdm run python manage.py runserver
```

Set `OPENAI_API_KEY` in `.env` before running live agent requests. Visit
`http://localhost:8000/` and use the demo login in local debug mode.
The Log out button submits a POST request and returns to the login page.

For local runs with `DJANGO_DEBUG=false`, use
`pdm run python manage.py runserver --insecure`. This development server option
also serves the demo's static files when debug mode is off.

The example environment uses immediate tasks. Local runs need no Redis worker.
For local background runs, set `TASKS_BACKEND=django_tasks_rq.RQBackend`, keep
`REDIS_URL=redis://localhost:6379/0`, and start Redis and the RQ worker:

```bash
pdm run python manage.py rqworker --job-class django_tasks_rq.Job
```

## Docker Setup

This Compose stack is for local development. Its Django development server uses
`--insecure` to serve static files with either debug setting.

```bash
cp .env.example .env
docker compose up --build
```

Compose starts Redis and runs a separate migration service. The web process and
RQ worker start only after that service succeeds. The database uses a shared
SQLite volume. Each `docker compose up` runs the migration service again; no
persistent readiness file is used.

Web and worker startup also wait for Redis to pass its health check. Redis and
the worker restart after an unexpected exit. A manual stop keeps them stopped.

Redis stores queue data in a named volume with append-only persistence. Each
write is saved to disk. A normal `docker compose down` and `up` keeps both the
database and queue. `docker compose down --volumes` removes both data volumes.

The Docker build excludes `.env`, local Python environments, Git data, and local
databases. Compose passes the API key to the containers at run time.

The image checks the committed PDM lockfile and installs its runtime packages.
It does not resolve new versions during the build. The app runs from the copied
source files, so the build needs no Git data for a package version.

Compose passes `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`,
`DATABASE_URL`, and the OpenAI settings from the environment file to each app
service. Compose selects the RQ backend and its internal Redis address. With no
`DATABASE_URL`, it uses the shared SQLite volume. A PostgreSQL URL must name a
host that the containers can reach.

## Environment Variables

- `DJANGO_SECRET_KEY`: Django secret key. The default is development-only.
- `DJANGO_DEBUG`: `true` enables the demo login route.
- `DJANGO_ALLOWED_HOSTS`: comma-separated host allowlist.
- `DATABASE_URL`: optional PostgreSQL URL. Leave unset for SQLite.
- `SQLITE_PATH`: optional SQLite database path.
- `TASKS_BACKEND`: defaults to immediate tasks locally; set
  `django_tasks_rq.RQBackend` for RQ.
- `REDIS_URL`: Redis connection string for RQ mode.
- `OPENAI_API_KEY`: required for real OpenAI-backed agent runs.
- `OPENAI_DEFAULT_MODEL`: optional model override used by the Agents SDK.

The default dependency set includes the Psycopg driver for PostgreSQL.
Use a `postgres://` or `postgresql://` URL. URL-encode special characters in
credentials and database names. Query parameters pass PostgreSQL connection
options such as `sslmode=require` and `connect_timeout=10` to the driver.

## Validation Commands

```bash
pdm run lint
pdm run test
pdm run check
npm test
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
  logs and confirm `TASKS_BACKEND=django_tasks_rq.RQBackend`.
- If queue data was lost, stop web and worker processes and make sure their old
  queued tasks cannot run. Mark the affected runs as failed with
  `pdm run python manage.py agentic_django_recover_runs --mode fail --include-pending`
  before starting the processes again. Requeueing can repeat tool actions.
- If CSP blocks a script, prefer self-hosted static assets and update
  `SECURE_CSP` in settings intentionally.
