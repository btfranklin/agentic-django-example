# Agentic Django Example Project

This Django project exercises the `agentic-django` package from PyPI.

The dependency is wired in `pyproject.toml` as:

```toml
agentic-django[rq]>=0.1.0
```

## Install

```bash
pdm install --group dev
```

## Configure OpenAI

Set `OPENAI_API_KEY` in your environment (see `.env.example`). Optionally set
`OPENAI_DEFAULT_MODEL` to override the default model (defaults to `gpt-4.1` in
the Agents SDK).

## Migrate

```bash
pdm run python manage.py migrate
```

## Run

```bash
pdm run python manage.py runserver
```

If you set `TASKS_BACKEND=django_tasks.backends.rq.RQBackend`, start an RQ worker
in a second terminal:

```bash
pdm run python manage.py rqworker --job-class django_tasks.backends.rq.Job
```

Visit `http://localhost:8000/` to use the sample UI.

## Docker

Set `OPENAI_API_KEY` (and optionally `OPENAI_DEFAULT_MODEL`) in `.env` so Compose
passes them through.
