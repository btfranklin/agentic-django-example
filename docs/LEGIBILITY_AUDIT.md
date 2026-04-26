# Legibility Audit

## Current Strengths

- The README explains the demo goal and gives both Docker and local quick-start
  paths.
- `pyproject.toml` exposes canonical `lint` and `test` scripts through PDM.
- The sample app has focused tests around login, session creation, run
  lifecycle fragments, JSON responses, ownership checks, and conversation
  rendering.
- Runtime configuration is centralized in Django settings and `.env.example`.
- Prompt text already lives in promptdown files instead of inline Python.

## Fixed Gaps

- `AGENTS.md` previously carried most repo guidance inline. It is now a short
  map that routes agents to durable docs.
- The repo had no `docs/` system of record. Architecture, operations, quality,
  and this audit now live in versioned docs.
- The package boundary was implied by README prose. It is now explicit:
  `agentic-django` is consumed from PyPI and template overrides are deliberate
  integration surfaces.
- Validation expectations existed, but there was no check that the documentation
  spine remained connected. Structural tests now enforce the highest-value
  legibility invariants.

## Remaining Risks

- There is no dedicated smoke script that boots the server and checks the main
  browser journey. Add one if UI regressions become common.
- There is no generated inventory because the repository is still small. Add a
  generated reference only if agents start rediscovering the same file map.
- The Docker build intentionally refreshes the PDM environment during image
  build. Revisit this if reproducible image builds become more important than
  tracking fresh example dependencies.

## Next Best Investments

1. Add a lightweight runtime smoke check for the demo login, home page, HTMX
   script presence, and first run creation path.
2. Add CI coverage for `npm run build:css` when frontend tooling becomes real.
3. Add an execution-plan directory only when work starts spanning multiple
   iterations or important decisions need durable acceptance criteria.
